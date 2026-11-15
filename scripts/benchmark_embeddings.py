"""Script Benchmark Komparasi Model Embedding IndoBERT.

Membandingkan performa retrieval dense vektor:
1. indobenchmark/indobert-base-p1 (Indo4B corpus, 3.6B words, Phase 1 seq_len 128)
2. indobenchmark/indobert-base-p2 (Indo4B corpus, 3.6B words, Phase 2 seq_len 512)
3. indolem/indobert-base-uncased (IndoLEM corpus, 220M words, Wikipedia & News)

Metrik yang dihitung:
- Top-1 Retrieval Accuracy (%)
- Top-3 Recall (%)
- Mean Separation Margin (Score_GT - max(Score_Distractor))
- Min Separation Margin
- Mean Inference Latency per query (ms)
- Cosine similarity matrix

Data mentah disimpan di: docs/laporan/raw/benchmark_embedding_indobert_comparison.json
"""
import json
import os
import sys
import time
from typing import Dict, List, Any

import torch
from transformers import AutoModel, AutoTokenizer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 10 Test Cases riil domain Informatika UNTAN
TEST_CASES = [
    {
        "id": "TC01",
        "category": "Kerja Praktik (KP)",
        "query": "Bagaimana alur dan syarat pengajuan Kerja Praktik (KP)?",
        "ground_truth": "Mahasiswa dapat mengajukan Kerja Praktik setelah menempuh minimal 80 SKS dan lulus mata kuliah prasyarat dengan mengajukan surat permohonan ke Koordinator KP prodi.",
    },
    {
        "id": "TC02",
        "category": "Tugas Akhir (TA / Skripsi)",
        "query": "Berapa minimal SKS untuk bisa seminar proposal skripsi atau tugas akhir?",
        "ground_truth": "Syarat seminar proposal Tugas Akhir adalah telah lulus minimal 110 SKS dengan IPK minimal 2.50 dan telah menyusun draf proposal yang disetujui dosen pembimbing.",
    },
    {
        "id": "TC03",
        "category": "Profil Dosen & KBK",
        "query": "Siapa dosen yang fokus penelitiannya di bidang Artificial Intelligence dan Machine Learning?",
        "ground_truth": "Izuardo Zulkarnain, S.Pd., M.T. merupakan dosen tetap kelompok keahlian Computation & Artificial Intelligence dengan fokus riset AI, machine learning, dan optimasi.",
    },
    {
        "id": "TC04",
        "category": "Kurikulum & Mata Kuliah",
        "query": "Mata kuliah apa saja yang wajib diambil pada semester 4 kurikulum informatika?",
        "ground_truth": "Struktur kurikulum semester 4 mencakup mata kuliah wajib Sistem Operasi, Pemrograman Berorientasi Objek, Analisis dan Desain Perangkat Lunak, serta Basis Data Lanjut.",
    },
    {
        "id": "TC05",
        "category": "Struktur Organisasi Prodi",
        "query": "Siapa koordinator program studi Informatika UNTAN saat ini?",
        "ground_truth": "Program Studi Informatika Jurusan Informatika Fakultas Teknik Universitas Tanjungpura dipimpin oleh Koordinator Program Studi yang bertanggung jawab atas penyelenggaraan akademik.",
    },
    {
        "id": "TC06",
        "category": "Laboratorium & Riset",
        "query": "Apa saja topik penelitian di laboratorium Sistem Cerdas dan Robotika?",
        "ground_truth": "Laboratorium Sistem Cerdas dan Robotika melayani riset visi komputer, pengolahan citra digital, robotika otonom, drone navigasi, serta pemodelan jaringan saraf tiruan.",
    },
    {
        "id": "TC07",
        "category": "Yudisium & Kelulusan",
        "query": "Bagaimana mekanisme pendaftaran yudisium dan berkas yang harus disiapkan?",
        "ground_truth": "Pendaftaran yudisium dilakukan secara daring melalui sistem informasi akademik dengan melampirkan bebas tanggungan perpus, naskah publikasi, dan bukti bebas laboratorium.",
    },
    {
        "id": "TC08",
        "category": "Administrasi & UKT",
        "query": "Berapa biaya UKT dan cara mengajukan keringanan banding UKT?",
        "ground_truth": "Pengajuan keringanan dan banding UKT diatur oleh rektorat universitas dengan melampirkan slip gaji orang tua, rekening listrik, dan surat keterangan tidak mampu dari kelurahan.",
    },
    {
        "id": "TC09",
        "category": "Peraturan Akademik",
        "query": "Apakah boleh mengulang mata kuliah yang sudah dapat nilai B?",
        "ground_truth": "Berdasarkan buku pedoman akademik, perbaikan nilai mata kuliah diperbolehkan untuk nilai C, D, dan E, sedangkan nilai B hanya dapat diulang jika kuota kelas mencukupi.",
    },
    {
        "id": "TC10",
        "category": "Fasilitas & Gedung",
        "query": "Di mana ruang sekretariat jurusan Teknik Informatika?",
        "ground_truth": "Ruang administrasi dan sekretariat program studi informatika berada di lantai dua Gedung Jurusan Informatika Fakultas Teknik UNTAN dekat ruang dosen.",
    },
]

# 6 Distractor Chunks dari berbagai topik yang tidak relevan
DISTRACTORS = [
    {
        "id": "DIST_01",
        "text": "Studi struktur batuan sedimen vulkanik di cekungan Sumatera bagian tengah menunjukkan adanya potensi panas bumi dan reservoir minyak bumi masa lampau.",
    },
    {
        "id": "DIST_02",
        "text": "Kementerian Pertanian merilis bibit padi varietas unggul tahan hama wereng coklat untuk meningkatkan produksi beras nasional di lumbung pangan Jawa Timur.",
    },
    {
        "id": "DIST_03",
        "text": "Resep pembuatan roti sobek manis dengan teknik autolisis menggunakan tepung terigu protein tinggi, ragi instan, susu bubuk, dan mentega tawar.",
    },
    {
        "id": "DIST_04",
        "text": "Klasemen sementara liga sepak bola eropa menunjukkan persaingan ketat di papan atas perebutan tiket kualifikasi piala liga musim depan.",
    },
    {
        "id": "DIST_05",
        "text": "Analisis dampak kenaikan suku bunga acuan bank sentral Amerika Serikat terhadap nilai tukar rupiah dan inflasi indeks harga konsumen negara berkembang.",
    },
    {
        "id": "DIST_06",
        "text": "Perbaikan sistem transmisi hidrolik pada ekskavator tambang batubara memerlukan pembersihan filter oli secara berkala dan penggantian seal silinder.",
    },
]

MODELS_TO_EVALUATE = [
    {
        "name": "indobenchmark/indobert-base-p1",
        "label": "IndoBenchmark IndoBERT-Base Phase 1",
        "pretraining": "Indo4B (3.6 Miliar Kata), Phase 1 (seq_len 128)",
        "params": "124.5M",
    },
    {
        "name": "indobenchmark/indobert-base-p2",
        "label": "IndoBenchmark IndoBERT-Base Phase 2",
        "pretraining": "Indo4B (3.6 Miliar Kata), Phase 2 (seq_len 512)",
        "params": "124.5M",
    },
    {
        "name": "indolem/indobert-base-uncased",
        "label": "IndoLEM IndoBERT-Base Uncased",
        "pretraining": "IndoLEM Corpus (220 Juta Kata, Kompas, Tempo, Wikipedia)",
        "params": "124.5M",
    },
]


def mean_pooling(model_output, attention_mask):
    """Mean pooling representasi token menjadi vektor kalimat."""
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask


def embed_texts(texts: List[str], tokenizer, model, max_length: int = 512) -> torch.Tensor:
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    ).to(DEVICE)
    with torch.no_grad():
        outputs = model(**encoded)
        embeddings = mean_pooling(outputs, encoded["attention_mask"])
        # Normalisasi L2 untuk standard dot product setara cosine similarity
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
    return embeddings


def evaluate_model(model_info: Dict[str, str]) -> Dict[str, Any]:
    model_name = model_info["name"]
    print(f"\n=======================================================")
    print(f"Evaluasi Model: {model_name}")
    print(f"Deskripsi: {model_info['label']}")
    print(f"Korpus Pretraining: {model_info['pretraining']}")
    print(f"=======================================================")

    t0_load = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(DEVICE)
    model.eval()
    load_time_sec = round(time.time() - t0_load, 2)
    print(f"Waktu load model: {load_time_sec} detik")

    # Siapkan semua teks kandidat: 10 ground truth + 6 distractor = 16 dokumen
    candidate_texts = []
    candidate_metadata = []

    for tc in TEST_CASES:
        candidate_texts.append(tc["ground_truth"])
        candidate_metadata.append({"id": tc["id"], "type": "ground_truth", "category": tc["category"]})

    for dist in DISTRACTORS:
        candidate_texts.append(dist["text"])
        candidate_metadata.append({"id": dist["id"], "type": "distractor", "category": "Distractor"})

    # Embed seluruh corpus kandidat
    candidate_embs = embed_texts(candidate_texts, tokenizer, model)

    results_per_tc = []
    top1_correct = 0
    top3_correct = 0
    total_margin = 0.0
    latencies_ms = []

    for idx, tc in enumerate(TEST_CASES):
        t0_query = time.time()
        query_emb = embed_texts([tc["query"]], tokenizer, model)
        latency_ms = (time.time() - t0_query) * 1000
        latencies_ms.append(latency_ms)

        # Hitung dot product (karena sudah dinormalisasi L2, setara cosine similarity)
        sims = torch.mm(query_emb, candidate_embs.t()).squeeze(0).cpu().tolist()

        # Target ground truth berada di indeks idx
        gt_score = sims[idx]

        # Ranking semua kandidat
        ranked = sorted(
            [
                {
                    "cand_idx": i,
                    "meta": candidate_metadata[i],
                    "score": round(sims[i], 4),
                }
                for i in range(len(candidate_texts))
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        rank_gt = next(r_idx for r_idx, r in enumerate(ranked) if r["cand_idx"] == idx) + 1
        is_top1 = (rank_gt == 1)
        is_top3 = (rank_gt <= 3)

        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1

        # Hitung max distractor score
        distractor_scores = [sims[i] for i, m in enumerate(candidate_metadata) if m["type"] == "distractor"]
        max_distractor_score = max(distractor_scores)
        margin = gt_score - max_distractor_score
        total_margin += margin

        results_per_tc.append({
            "id": tc["id"],
            "category": tc["category"],
            "query": tc["query"],
            "gt_score": round(gt_score, 4),
            "max_distractor_score": round(max_distractor_score, 4),
            "separation_margin": round(margin, 4),
            "rank_ground_truth": rank_gt,
            "top1_match": is_top1,
            "top3_match": is_top3,
            "top1_candidate_id": ranked[0]["meta"]["id"],
            "top1_candidate_type": ranked[0]["meta"]["type"],
            "latency_ms": round(latency_ms, 2),
        })

        status = "OK [Top-1]" if is_top1 else f"GAGAL (Rank #{rank_gt})"
        print(f"  {tc['id']} [{tc['category'][:18]:<18}]: {status:<15} Margin={margin:+.4f} (GT={gt_score:.4f}, MaxDist={max_distractor_score:.4f})")

    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    avg_margin = round(total_margin / len(TEST_CASES), 4)
    top1_acc = round((top1_correct / len(TEST_CASES)) * 100, 1)
    top3_acc = round((top3_correct / len(TEST_CASES)) * 100, 1)

    print(f"\n--- Ringkasan Model {model_name} ---")
    print(f"Top-1 Accuracy: {top1_acc}% ({top1_correct}/{len(TEST_CASES)})")
    print(f"Top-3 Recall:   {top3_acc}% ({top3_correct}/{len(TEST_CASES)})")
    print(f"Average Margin: {avg_margin:+.4f}")
    print(f"Rata-rata Latensi: {avg_latency} ms / query")

    return {
        "model_name": model_name,
        "label": model_info["label"],
        "pretraining": model_info["pretraining"],
        "parameters": model_info["params"],
        "top1_accuracy_percent": top1_acc,
        "top1_correct_count": top1_correct,
        "top3_recall_percent": top3_acc,
        "top3_correct_count": top3_correct,
        "total_test_cases": len(TEST_CASES),
        "average_separation_margin": avg_margin,
        "min_separation_margin": round(min(r["separation_margin"] for r in results_per_tc), 4),
        "max_separation_margin": round(max(r["separation_margin"] for r in results_per_tc), 4),
        "average_latency_ms": avg_latency,
        "load_time_sec": load_time_sec,
        "details_per_test_case": results_per_tc,
    }


def main():
    print("Memulai Benchmark Komparasi Embedding IndoBERT...")
    results = {}
    for minfo in MODELS_TO_EVALUATE:
        results[minfo["name"]] = evaluate_model(minfo)

    output_dir = "docs/laporan/raw"
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "benchmark_embedding_indobert_comparison.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nHasil benchmark JSON berhasil disimpan ke: {json_path}")


if __name__ == "__main__":
    main()

