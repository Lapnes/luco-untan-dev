---
judul: "Hasil Benchmark Model & Evaluasi Performa Luco"
kategori: "profil"
slug: "benchmark-dan-evaluasi-model"
sumber: "Laporan Pengujian Menyeluruh Sistem Luco 2026"
terakhir_diperbarui: "2026-11-15"
ringkasan: "Hasil pengujian kuantitatif benchmark model embedding IndoBERT, benchmark komparasi 3 mode inferensi, evaluasi LLM-as-a-judge, dan uji keamanan sistem Luco."
---

# Hasil Benchmark Model & Evaluasi Performa Luco

Sistem asisten cerdas **Luco (luco-untan)** telah melalui serangkaian pengujian kuantitatif dan benchmark empiris menyeluruh untuk Tugas Besar Pengganti UAS Kecerdasan Buatan 2026 (oleh Ragil Amirzaky, Andrean Stephanus, dan Adjie Prasetya).

---

## 1. Hasil Benchmark Model Dense Embedding IndoBERT

Pengujian membandingkan performa model representasi vektor 768 dimensi pada mikroservis `luco-indobert` (port `8001`) terhadap 10 query prodi riil dan 6 dokumen distractor pengganggu:

| Metrik Evaluasi | IndoBenchmark p1 (`indobenchmark/indobert-base-p1`) | IndoLEM Uncased (`indolem/indobert-base-uncased`) | Keterangan & Keunggulan |
| :--- | :---: | :---: | :--- |
| **Top-1 Retrieval Accuracy** | **80,0%** (8/10) | 40,0% (4/10) | IndoBenchmark **2x lipat lebih akurat** (+40%) |
| **Top-3 Retrieval Recall** | **100,0%** (10/10) | 60,0% (6/10) | Dokumen target selalu masuk 3 besar kandidat |
| **Rata-rata Margin Separasi ($\Delta$)** | **+0,2657** | +0,0373 | IndoBenchmark **7,1x lebih tegas** memisahkan dokumen relevan |
| **Minimum Margin Separasi** | **+0,1442** (Stabil Positif) | **-0,0815** (Tertembus Distractor) | IndoLEM tertembus dokumen tidak relevan |
| **Latensi Inferensi (CPU)** | **66,58 ms** | 55,65 ms | Sangat cepat dan efisien pada CPU container |

### Fenomena *Representation Collapse* pada IndoLEM:
Model `indolem/indobert-base-uncased` mengalami pemadatan ruang vektor (*anisotropic space*). Pada kueri dosen AI, dokumen distractor batuan sedimen memperoleh skor **0,7002**, mengalahkan profil dosen AI Pak Izuardo (**0,6187**). Sementara itu, korpus masif Indo4B (~3,6 miliar kata) pada `indobenchmark/indobert-base-p1` terbukti kebal dari fenomena ini dan ditetapkan sebagai standar embedding Luco.

---

## 2. Hasil Benchmark Komparasi 3 Mode Inferensi

Pengujian 11 kueri terstandardisasi mengukur trade-off antara akurasi, latensi, dan biaya komputasi:

| Metrik Pengujian | IndoBERT + OpenViking (Mode Lengkap) | OpenViking Cepat (One-shot) | Direct LLM Standar (Bypass Retrieval) |
| :--- | :---: | :---: | :---: |
| **Rata-rata Latensi (*Mean Latency*)** | **4,62 detik** | **1,85 detik** (2,5x lebih cepat) | **1,20 detik** (3,9x lebih cepat) |
| **Rata-rata Tool Steps** | **2,0 langkah** | 0,6 langkah | **0,0 langkah** |
| **Rata-rata Konsumsi Token** | **739 token** | 660 token | 684 token |
| **Estimasi Biaya per Kueri** | **Rp 3,37** | Rp 2,62 | Rp 2,85 |
| **Skor Kualitas (*Judge 1-5*)** | **4,91 / 5,0** | 4,27 / 5,0 | 3,73 / 5,0 |
| **Sitasi Terverifikasi (*In-Scope*)** | **100,0% (3/3)** | 33,3% | 0,0% |
| **Kepatuhan Guardrail Router** | **100,0%** | **100,0%** | **100,0%** |

---

## 3. Hasil Pengujian Unit & Integrasi Sistem (Pytest Suite)
- **Status Kelulusan**: **100% Lulus (77 dari 77 pengujian)** dalam waktu **5,40 detik**.
- **Cakupan 13 Modul**: Menguji siklus agen (`test_agent.py`), API contract (`test_api_contract.py`), autentikasi JWT (`test_auth.py`), retrieval backend (`test_backends.py`), deteksi klarifikasi aktif (`test_clarifications.py`), ketahanan LLM Bifrost failover (`test_llm_resilience.py`), lookup profil 33 dosen (`test_lookup.py`), rate limiting token bucket (`test_ratelimit.py`), router heuristik (`test_router.py`), sesi PostgreSQL (`test_sessions_and_db.py`), dan integrasi hidup OpenViking (`test_viking_live.py`).

---

## 4. Hasil Pengujian Keamanan & Prompt Injection
- **Imutabilitas Persona**: Kebal dari serangan *DAN (Do Anything Now)* dan instruksi manipulasi identitas.
- **Kerahasiaan Kredensial**: Memblokir 100% upaya ekstraksi teks *system prompt*, password database, atau kunci API.
- **Pencegahan Joki Akademik**: Menolak pembuatan naskah skripsi utuh dan mengarahkan ke kaidah penulisan ilmiah serta bimbingan Dosen PA.
- **Directory Traversal**: Memblokir serangan path `../../etc/passwd` dengan fungsi `safe_rel()` yang aman.
