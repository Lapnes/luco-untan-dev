# Evaluasi & Benchmark Sistem RAG

Dokumen ini menjelaskan metodologi pengujian, dataset tolok ukur (*benchmark*), metrik penilaian, serta panduan menjalankan evaluasi komparatif antara sistem RAG Luco dan model dasar (*baseline*) tanpa RAG untuk keperluan laporan ilmiah Tugas Besar UAS Kecerdasan Buatan 2026.

---

## 1. Tujuan Evaluasi

Tujuan evaluasi akademik ini adalah untuk membuktikan secara empiris bahwa:
1. **Peningkatan Akurasi Faktual:** Penambahan *retrieval* dokumen prodi secara signifikan meningkatkan kebenaran jawaban pada ranah spesifik institusi.
2. **Eliminasi Halusinasi:** Pengecekan sitasi dan grounding dokumen berhasil menekan angka halusinasi pada data penting (seperti NIP dosen dan prasyarat SKS).
3. **Ketepatan Batas Cakupan (*Scope Guardrails*):** Upfront Router secara akurat menolak pertanyaan di luar wewenang prodi tanpa membuang token dan waktu komputasi.

---

## 2. Taksonomi Dataset Benchmark (`eval/questions.jsonl`)

Dataset evaluasi disimpan di [`eval/questions.jsonl`](file:///home/luco/luco-untan/eval/questions.jsonl). Setiap entri pertanyaan memiliki struktur:

```json
{
  "id": "q01",
  "category": "in_scope",
  "question": "Gimana alur pendaftaran Kerja Praktik di Informatika UNTAN?",
  "reference": "Mahasiswa menempuh minimal 80 SKS, mengajukan permohonan ke koordinator KP...",
  "expected_sources": ["kp-ta/panduan-kp.md"]
}
```

### Empat Kategori Pengujian:
| Kategori | Definisi & Contoh Pertanyaan | Perilaku yang Diharapkan |
| :--- | :--- | :--- |
| `in_scope` | Pertanyaan resmi seputar akademik, dosen, KP, dan TA UNTAN (misal: *"Apa syarat seminar proposal TA?"*). | Menjawab dengan tepat dan menyertakan sitasi tautan terverifikasi. |
| `out_of_scope` | Pertanyaan umum non-akademik (misal: *"Tolong kerjain tugas kalkulus"* atau *"Siapa presiden sekarang?"*). | Menolak secara sopan (*Fast-Reject*, 0 langkah RAG). |
| `not_in_docs` | Topik prodi namun faktanya tidak tercantum dalam dokumen resmi (misal: *"Berapa biaya UKT prodi tahun 2030?"*). | Menyatakan dengan jujur bahwa informasi tidak ditemukan di dokumen dan mengarahkan ke sekretariat. |
| `saran_kerjasama` | Kritik, keluhan, saran perbaikan fasilitas, atau ajakan kerjasama magang industri. | Mengarahkan ke kanal komunikasi resmi sekretariat prodi. |

---

## 3. Metodologi Penilaian (LLM-as-a-Judge)

Evaluasi otomatis memanfaatkan model bahasa tingkat lanjut sebagai juri (*LLM-as-a-judge*) dengan prompt ketat:

- **Skor Ketepatan (Skala 1–5):**
  - **5:** Jawaban tepat penuh, seluruh fakta sesuai dengan acuan resmi.
  - **3:** Jawaban sebagian benar, namun ada detail kecil yang terlewat.
  - **1:** Jawaban salah total atau menyesatkan.
- **Deteksi Halusinasi (`true`/`false`):** Bernilai `true` apabila jawaban chatbot memuat klaim spesifik yang tidak didukung oleh dokumen acuan.
- **Perilaku Benar (`true`/`false`):** 
  - Untuk `in_scope`: Bernilai `true` jika bot menjawab secara substantif (bukan menolak).
  - Untuk kategori lainnya: Bernilai `true` jika bot menolak/mengarahkan sesuai harapan.

---

## 4. Cara Menjalankan Evaluasi & Benchmark

Eksekusi evaluasi dan benchmark dilakukan melalui task Pixi yang telah dikonfigurasi:

### A. Evaluasi Tolok Ukur (Luco RAG vs Baseline tanpa RAG)
Menjalankan Luco RAG dan model vanilla tanpa RAG pada `eval/questions.jsonl`, lalu dinilai oleh juri LLM:
```bash
pixi run eval -- --judge
```
*Opsi lain:*
- `pixi run eval` (evaluasi cepat tanpa juri LLM).
- `pixi run eval -- --judge --no-baseline` (melewati baseline vanilla).

### B. Benchmark 3 Mode Inferensi (IndoBERT+Viking vs Fast vs Direct LLM)
Menguji performa head-to-head 3 mode inferensi Luco (latensi, konsumsi token, biaya, dan akurasi guardrail):
```bash
pixi run benchmark-modes
```
*Atau eksekusi manual:* `pixi run python scripts/benchmark_modes.py --judge`

### C. Benchmark Komparasi Varian Embedding IndoBERT
Menguji perbandingan akurasi retrieval antara varian model IndoBERT (`indobenchmark/indobert-base-p1` vs `p2` vs `indolem/indobert-base-uncased`):
```bash
pixi run benchmark-bert
```

### D. Benchmark Empiris Context Stuffing vs Luco Hybrid RAG
Menguji komparasi percakapan multi-turn panjang antara pendekatan *full context injection* (tanpa RAG) vs Luco Hybrid RAG:
```bash
pixi run benchmark-context
```

Hasil evaluasi dan benchmark disimpan otomatis dalam format JSON dan Markdown di `eval/reports/` dan `docs/laporan/raw/` untuk analisis statistik lanjutan.

---

## 5. Ringkasan Metrik Hasil Evaluasi Ilmiah

Hasil akhir evaluasi empiris membuktikan keunggulan komprehensif arsitektur Hybrid Agentic RAG Luco:

### A. Evaluasi Baseline LLM vs Luco RAG (LLM-as-a-Judge)
| Metrik Evaluasi | Baseline (Vanilla LLM Tanpa RAG) | Luco (Hybrid Agentic RAG) | Delta Performa |
| :--- | :--- | :--- | :--- |
| **Rata-rata Skor Akurasi (1–5)** | 2.80 | **4.91** | **+75,4%** |
| **Tingkat Halusinasi (%)** | 45.0% | **0.0%** | **-100% (Halusinasi Tereliminasi)** |
| **Tingkat Perilaku Benar (%)** | 60.0% | **100.0%** | **+40.0%** |
| **Rasio Sitasi Terverifikasi** | 0% (Tanpa rujukan) | **100% (Semua tautan terverifikasi)** | **Terverifikasi Penuh** |
| **Rata-rata Langkah Agen** | 0 langkah | **2.0 langkah** | *Multi-step reasoning* |
| **Rata-rata Biaya per Query** | Rp 2,85 | **Rp 3,37** | *Sangat ekonomis* |

### B. Evaluasi Embedding IndoBERT (IndoBenchmark vs IndoLEM)
- **Top-1 Retrieval Accuracy**: IndoBenchmark p1 **80,0%** vs IndoLEM **40,0%** (2x lipat lebih akurat).
- **Margin Separasi Semantik ($\Delta$)**: IndoBenchmark **+0,2657** vs IndoLEM **+0,0373** (7,1x lebih tegas dan kebal dari *representation collapse*).
- **Latensi CPU**: **66,58 ms**.

### C. Komparasi Percakapan Multi-Turn: Full Context Injection vs Hybrid RAG
- **Efisiensi Token**: Hybrid Luco menghemat **97,76% token** (dari 300.049 token menjadi 6.723 token pada percakapan 6-turn).
- **Efisiensi Biaya**: Menghemat **96,66% biaya** (dari Rp 495,53 menjadi Rp 16,54 per sesi).
- **Resolusi Fenomena *Lost in the Middle***: Context stuffing gagal menemukan NIP 18 digit dosen; Hybrid RAG Luco 100% tepat via `vault/lookup.json` dalam 1,89 detik.

---

## 6. Berkas Laporan Pengujian Final di Repositori

1. **[Naskah Master Laporan Akhir (Bab I–VI)](file:///home/luco/luco-untan/docs/laporan/final/laporan_lengkap_tugas_besar_ai_luco.md)**: Dokumen lengkap naskah akademik siap salin ke laporan akhir.
2. **[Laporan Pengujian Menyeluruh Sistem](file:///home/luco/luco-untan/docs/laporan/final/laporan_pengujian_keseluruhan_aplikasi.md)**: Laporan eksekutif 17 komponen arsitektur dan matriks 78 unit tests Pytest (100% lulus).
3. **[Evaluasi Context Stuffing vs Hybrid RAG](file:///home/luco/luco-untan/docs/laporan/final/perbandingan_context_stuffing_vs_arsitektur_luco.md)**: Analisis kuantitatif multi-turn per giliran obrolan.
4. **[Komparasi Embedding IndoBERT](file:///home/luco/luco-untan/docs/laporan/final/perbandingan_embedding_indobert.md)**: Pengujian mendalam representasi 768-dimensi IndoBERT vs IndoLEM.
5. **[Benchmark 3 Mode Inferensi](file:///home/luco/luco-untan/docs/laporan/final/benchmark_3_mode_inferensi.md)**: Komparasi latensi, token, dan trade-off akurasi 3 mode sistem Luco.

