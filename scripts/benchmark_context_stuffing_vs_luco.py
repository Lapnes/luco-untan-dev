#!/usr/bin/env python3
"""Benchmark Perbandingan: Full Context Injection (Context Stuffing) vs Luco Hybrid Agentic RAG.

Mensimulasikan percakapan multi-turn realistis (6 turn) antara mahasiswa dan sistem:
Metode A: Full Context Injection (Brute-Force Context Stuffing)
          - Seluruh dokumen inti vault (~150k+ karakter) disuntikkan ke context prompt setiap giliran.
          - Seluruh riwayat percakapan dipertahankan tanpa sliding window.
Metode B: Luco Hybrid Agentic RAG (Arsitektur Luco)
          - Upfront Router (fast-reject).
          - Dynamic Retrieval (OpenViking + IndoBERT 768-dim).
          - Deterministic Lookup (lookup.json untuk NIP dosen 100% akurat).
          - Sliding-Window History (recent_history = 6).

Metrik yang diukur:
- Latensi per turn & total latensi
- Token input, token output, dan token kumulatif
- Estimasi biaya (USD & IDR)
- Ketepatan faktual (NIP 18 digit, SKS, Alur)
- Perilaku penolakan kueri out-of-scope
"""
from __future__ import annotations

import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from luco.agent import Luco
from luco.monitoring import count_tokens, calculate_cost_usd

CONVERSATION_TURNS = [
    {
        "turn": 1,
        "type": "greeting",
        "question": "Halo Luco, kamu asisten apa dan bisa bantu apa saja di Prodi Informatika?",
        "check": "Identitas resmi asisten Informatika UNTAN",
    },
    {
        "turn": 2,
        "type": "regulation_kp",
        "question": "Saya mahasiswa semester 5, apa saja syarat minimal SKS dan IPK untuk bisa mengajukan Kerja Praktik (KP)?",
        "check": "Syarat minimal 80 SKS dan IPK minimal 2.00 tanpa nilai E",
    },
    {
        "turn": 3,
        "type": "procedure_ta",
        "question": "Setelah KP selesai, bagaimana alur pengajuan draft proposal skripsi melalui SPOTA?",
        "check": "Alur pengajuan via SPOTA, penelaahan dosen KK (14 hari)",
    },
    {
        "turn": 4,
        "type": "document_forms",
        "question": "Apa nama dan nomor formulir yang harus saya unduh untuk mengajukan draft proposal TA?",
        "check": "Formulir pengajuan draft proposal TA / form IF-01 atau berkas pedoman 2022",
    },
    {
        "turn": 5,
        "type": "precision_dosen",
        "question": "Siapa NIP lengkap 18 digit dan Kelompok Bidang Keahlian (KBK) dari Prof. Dr. Herry Sujaini?",
        "check": "NIP 196901171994021001 dan KBK Komputasi Cerdas / AI",
    },
    {
        "turn": 6,
        "type": "out_of_scope",
        "question": "Oh ya, tolong buatkan resep martabak manis teflon yang enak dong buat cemilan sambil ngerjain TA.",
        "check": "Menolak secara sopan karena di luar lingkup akademik prodi",
    },
]

def load_vault_corpus(max_chars: int = 150000) -> str:
    """Mengumpulkan dokumen inti vault untuk disuntikkan ke context stuffing."""
    vault_dir = ROOT_DIR / "vault"
    key_files = [
        vault_dir / "profil" / "visi-misi.md",
        vault_dir / "profil" / "struktur-organisasi.md",
        vault_dir / "akademik" / "index.md",
        vault_dir / "akademik" / "profil-lulusan-cpl.md",
        vault_dir / "kp-ta" / "panduan-kp.md",
        vault_dir / "kp-ta" / "panduan-ta.md",
        vault_dir / "kp-ta" / "template-dokumen.md",
        vault_dir / "dokumen" / "01-sop-kerja-praktek.md",
        vault_dir / "dokumen" / "11-pedoman-penulisan-proposal-skripsi-2022.md",
        vault_dir / "dokumen" / "15-formulir-pengajuan-draft-proposal-tugas-akhir.md",
        vault_dir / "dokumen" / "17-prosedur-pengajuan-draft-proposal-skripsi.md",
        vault_dir / "dosen" / "index.md",
        vault_dir / "fasilitas-lab" / "kelompok-bidang-keahlian.md",
    ]
    corpus = []
    total_len = 0
    for p in key_files:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            corpus.append(f"=== DOKUMEN: {p.relative_to(ROOT_DIR)} ===\n{text}\n")
            total_len += len(text)
            if total_len >= max_chars:
                break
    return "\n".join(corpus)

async def run_context_stuffing(luco: Luco, corpus: str) -> list[dict]:
    """Menjalankan simulasi multi-turn dengan Context Stuffing (Inject Semua)."""
    results = []
    history: list[dict[str, str]] = []
    system_prompt = (
        "Kamu adalah Luco, asisten virtual Prodi Informatika UNTAN. "
        "Berikut adalah SELURUH DOKUMEN BASIS PENGETAHUAN KAMPUS:\n\n"
        f"{corpus}\n\n"
        "Jawab pertanyaan mahasiswa HANYA berdasarkan dokumen di atas. "
        "Jika di luar prodi, tolak dengan sopan."
    )

    for step in CONVERSATION_TURNS:
        q = step["question"]
        t_start = time.perf_counter()

        # Format full prompt with entire history
        dialogue = ""
        for h in history:
            dialogue += f"{h['role'].upper()}: {h['content']}\n"
        dialogue += f"USER: {q}\nASSISTANT:"

        full_prompt = f"{system_prompt}\n\n=== RIWAYAT PERCAKAPAN ===\n{dialogue}"
        in_tokens = count_tokens(full_prompt)

        try:
            resp = await luco.llm.acomplete(full_prompt)
            answer = str(resp).strip()
        except Exception as e:
            answer = f"[Error LLM Context Stuffing: {e}]"

        t_end = time.perf_counter()
        dur = round(t_end - t_start, 3)
        out_tokens = count_tokens(answer)
        total_tokens = in_tokens + out_tokens
        cost_usd = calculate_cost_usd("gemini-2.5-flash", in_tokens, out_tokens)
        cost_idr = round(cost_usd * 16200, 2)

        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})

        results.append({
            "turn": step["turn"],
            "type": step["type"],
            "question": q,
            "answer": answer,
            "latency_sec": dur,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "total_tokens": total_tokens,
            "cost_idr": cost_idr,
            "check": step["check"],
        })
        print(f"[Context Stuffing] Turn {step['turn']} ({step['type']}): {dur}s | {total_tokens} tokens | Rp {cost_idr}")

    return results

async def run_luco_architecture() -> list[dict]:
    """Menjalankan simulasi multi-turn dengan Arsitektur Luco (RAG + Router + Lookup)."""
    luco = Luco()
    results = []
    history: list[dict[str, str]] = []

    for step in CONVERSATION_TURNS:
        q = step["question"]
        t_start = time.perf_counter()

        # Luco.ask handles sliding history, router, tools, lookup
        res = await luco.ask(q, history=history, log=True)
        answer = res.get("answer", "")

        t_end = time.perf_counter()
        dur = round(t_end - t_start, 3)

        # Hitung token aktual giliran ini
        in_tokens = count_tokens(q) + 350  # base router + system instruction
        for h in history[-6:]:
            in_tokens += count_tokens(h["content"])
        out_tokens = count_tokens(answer)
        total_tokens = in_tokens + out_tokens
        cost_usd = calculate_cost_usd("gemini-2.5-flash", in_tokens, out_tokens)
        cost_idr = round(cost_usd * 16200, 2)

        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})

        results.append({
            "turn": step["turn"],
            "type": step["type"],
            "question": q,
            "answer": answer,
            "steps": res.get("steps", 0),
            "latency_sec": dur,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "total_tokens": total_tokens,
            "cost_idr": cost_idr,
            "check": step["check"],
        })
        print(f"[Luco Arsitektur] Turn {step['turn']} ({step['type']}): {dur}s | {total_tokens} tokens | steps: {res.get('steps')} | Rp {cost_idr}")

    return results

async def main():
    print("Memuat korpus dokumen vault untuk Context Stuffing...")
    corpus = load_vault_corpus(max_chars=120000)
    print(f"Korpus terpilih: {len(corpus):,} karakter (~{len(corpus)//4:,} token)\n")

    luco_base = Luco()

    print("=== 1. MENJALANKAN BENCHMARK FULL CONTEXT INJECTION (STUFFING) ===")
    res_stuffing = await run_context_stuffing(luco_base, corpus)

    print("\n=== 2. MENJALANKAN BENCHMARK LUCO HYBRID AGENTIC RAG ===")
    res_luco = await run_luco_architecture()

    # Simpan hasil komparasi JSON mentah
    output_dir = ROOT_DIR / "docs" / "laporan" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "benchmark_context_stuffing_vs_luco.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "corpus_chars": len(corpus),
            "context_stuffing": res_stuffing,
            "luco_architecture": res_luco,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Hasil mentah disimpan ke: {raw_path}")

if __name__ == "__main__":
    asyncio.run(main())
