"""IndoBERT Embedding Microservice (OpenAI-compatible).

Menyediakan endpoint OpenAI-compatible /v1/embeddings menggunakan arsitektur
IndoBERT (indobenchmark/indobert-base-p1) untuk retrieval semantik bahasa Indonesia.
Sesuai rancangan Lembar Konsultasi Tugas Besar UAS AI 2026:
'Hybrid Index berbasis BERT dan Dense Vektor'.
"""
from __future__ import annotations

import os
import time
from typing import List, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import torch
from transformers import AutoModel, AutoTokenizer

MODEL_NAME = os.getenv("MODEL_NAME", "indobenchmark/indobert-base-p1")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

app = FastAPI(title="IndoBERT Embedding Service", version="1.0")

print(f"[IndoBERT] Loading tokenizer and model: {MODEL_NAME} on {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()
print(f"[IndoBERT] Model successfully loaded (dim=768)!")


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]] = Field(..., description="Teks tunggal atau list teks")
    model: str = Field(default=MODEL_NAME, description="Nama model")
    encoding_format: str = Field(default="float")


def mean_pooling(model_output, attention_mask):
    """Mean pooling untuk menghasilkan representasi kalimat 768-dim dari token output."""
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "device": DEVICE,
        "dimension": 768,
    }


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "owned_by": "indobenchmark",
            },
            {
                "id": "indobert",
                "object": "model",
                "owned_by": "indobenchmark",
            }
        ]
    }


@app.post("/v1/embeddings")
def create_embeddings(req: EmbeddingRequest):
    inputs = [req.input] if isinstance(req.input, str) else req.input
    if not inputs:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    t0 = time.time()
    try:
        encoded = tokenizer(
            inputs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(DEVICE)

        with torch.no_grad():
            outputs = model(**encoded)
            sentence_embeddings = mean_pooling(outputs, encoded["attention_mask"])
            # Normalisasi L2 agar cosine similarity setara dengan dot product
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

        vectors = sentence_embeddings.cpu().tolist()

        data = [
            {
                "object": "embedding",
                "index": i,
                "embedding": vec,
            }
            for i, vec in enumerate(vectors)
        ]

        total_tokens = int(encoded["attention_mask"].sum().item())
        return {
            "object": "list",
            "data": data,
            "model": MODEL_NAME,
            "usage": {
                "prompt_tokens": total_tokens,
                "total_tokens": total_tokens,
            },
            "_latency_ms": round((time.time() - t0) * 1000, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

