# Laporan Komparasi Model Embedding Bahasa Indonesia: IndoBenchmark IndoBERT vs IndoLEM IndoBERT

Dokumen ini menyajikan hasil pengujian empiris dan komparasi model *dense embedding* berbasis BERT Bahasa Indonesia untuk sistem chatbot asisten akademik **Luco** (Program Studi Informatika, Universitas Tanjungpura). Pengujian ini disusun sebagai data pendukung Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan 2026 oleh kelompok mahasiswa:
- Ragil Amirzaky
- Andrean Stephanus
- Adjie Prasetya

---

## 1. Latar Belakang & Motivasi

Berdasarkan lembar konsultasi dan proposal rancangan Tugas Besar, sistem Luco mengadopsi arsitektur **Hybrid Agentic RAG**:
$$\text{Query} \xrightarrow{\text{Upfront Router}} \begin{cases} \text{Bypass Cepat} & (\text{Sapaan / Out-of-Scope}) \\ \text{Lookup Tepat} & (\text{NIP / Email / Dosen via } \texttt{lookup.json}) \\ \text{Dense Vector Search} & (\text{OpenViking} + \text{IndoBERT 768-dim}) \end{cases}$$

### Mengapa Evaluasi Embedding Bahasa Indonesia Krusial?
1. **Penghindaran Model Asing Tanpa Evaluasi**: Banyak sistem RAG secara naif menggunakan model multilingual atau model asal Tiongkok (seperti `bge-small-zh` default OpenViking) yang menghasilkan representasi semantik buruk (*cross-lingual degradation*) ketika memproses istilah khas akademik Indonesia seperti *SKS*, *seminar proposal (sempro)*, *yudisium*, *kerja praktik (KP)*, dan *kelompok keahlian (KBK)*.
2. **Kebutuhan Vektor 768-Dimensi yang Diskriminatif**: Diperlukan model BERT yang mampu membedakan teks regulasi akademik dari teks pengganggu (*distractor*) dengan margin separasi yang lebar, sehingga agen LlamaIndex tidak salah membaca konteks.

Dua kandidat utama model transformer Bahasa Indonesia berskala *base* (124,5 juta parameter) adalah:
- **Keluarga IndoBenchmark**: `indobenchmark/indobert-base-p1` dan `indobenchmark/indobert-base-p2`.
- **Keluarga IndoLEM**: `indolem/indobert-base-uncased`.

---

## 2. Spesifikasi Model yang Diuji

| Parameter / Fitur | IndoBenchmark IndoBERT-Base Phase 1 | IndoBenchmark IndoBERT-Base Phase 2 | IndoLEM IndoBERT-Base Uncased |
| :--- | :--- | :--- | :--- |
| **Identitas HuggingFace** | `indobenchmark/indobert-base-p1` | `indobenchmark/indobert-base-p2` | `indolem/indobert-base-uncased` |
| **Arsitektur Dasar** | BERT-Base (12 layer, 12 heads) | BERT-Base (12 layer, 12 heads) | BERT-Base (12 layer, 12 heads) |
| **Dimensi Hidden ($d$)** | 768 | 768 | 768 |
| **Jumlah Parameter** | 124,5 Juta | 124,5 Juta | 124,5 Juta |
| **Korpus Pre-training** | **Indo4B** (~3,6 Miliar kata) | **Indo4B** (~3,6 Miliar kata) | **IndoLEM Corpus** (~220 Juta kata) |
| **Keberagaman Korpus** | Berita, Wikipedia, Twitter/X, Web, Blog, Kaskus (ragam formal & kasual) | Berita, Wikipedia, Twitter/X, Web, Blog, Kaskus (ragam formal & kasual) | Kompas, Tempo, Wikipedia Indonesia (formal jurnalistik) |
| **Max Sequence Pre-train** | 128 token (Phase 1) | 512 token (Phase 2) | 512 token |
| **Casing** | Cased | Cased | Uncased |

> [!NOTE]
> Kedua varian model dijalankan dengan teknik *mean pooling* pada seluruh representasi token terakhir, diikuti dengan *L2 Normalization*:
> $$\mathbf{v} = \frac{\sum_{i=1}^{L} \mathbf{h}_i \cdot m_i}{\sum_{i=1}^{L} m_i}, \quad \mathbf{\hat{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$
> Dengan normalisasi ini, nilai kesamaan kosinus (*cosine similarity*) ekuivalen dengan operasi *dot product* $\mathbf{\hat{q}} \cdot \mathbf{\hat{d}}$.

---

## 3. Metodologi Pengujian

Pengujian dilakukan menggunakan microservice `luco-indobert` yang berjalan di atas CPU container Docker pada lingkungan pengembangan Luco.

### 3.1. Dataset Evaluasi
Pengujian menggunakan **10 pasang Query & Dokumen Ground Truth** riil lingkungan Program Studi Informatika UNTAN, dipadukan dengan **6 Dokumen Distractor** dari berbagai ranah umum yang tidak relevan (geologi minyak bumi, varietas padi kementan, resep kuliner, klasemen bola eropa, suku bunga makroekonomi, dan mekanik hidrolik).

Daftar 10 Skenario Pertanyaan:
1. **TC01 (KP)**: "Bagaimana alur dan syarat pengajuan Kerja Praktik (KP)?"
2. **TC02 (TA/Skripsi)**: "Berapa minimal SKS untuk bisa seminar proposal skripsi atau tugas akhir?"
3. **TC03 (Dosen & KBK)**: "Siapa dosen yang fokus penelitiannya di bidang Artificial Intelligence dan Machine Learning?"
4. **TC04 (Kurikulum)**: "Mata kuliah apa saja yang wajib diambil pada semester 4 kurikulum informatika?"
5. **TC05 (Struktur Prodi)**: "Siapa koordinator program studi Informatika UNTAN saat ini?"
6. **TC06 (Laboratorium)**: "Apa saja topik penelitian di laboratorium Sistem Cerdas dan Robotika?"
7. **TC07 (Yudisium)**: "Bagaimana mekanisme pendaftaran yudisium dan berkas yang harus disiapkan?"
8. **TC08 (UKT & Finansial)**: "Berapa biaya UKT dan cara mengajukan keringanan banding UKT?"
9. **TC09 (Peraturan Akademik)**: "Apakah boleh mengulang mata kuliah yang sudah dapat nilai B?"
10. **TC10 (Fasilitas & Ruang)**: "Di mana ruang sekretariat jurusan Teknik Informatika?"

### 3.2. Metrik Pengukuran
- **Top-1 Accuracy**: Persentase query di mana dokumen *ground truth* menempati peringkat ke-1 di atas seluruh distractor.
- **Top-3 Recall**: Persentase query di mana dokumen target berada pada 3 kandidat teratas.
- **Margin Separasi ($\Delta$)**:
  $$\Delta = S_{\text{GroundTruth}} - \max(S_{\text{Distractors}})$$
  Margin positif menunjukkan dokumen target memiliki skor lebih tinggi daripada distractor terdekat. Semakin besar nilai $\Delta$, semakin kebal model terhadap halusinasi retrieval.
- **Latensi Rata-rata**: Waktu inferensi per query dalam milidetik (ms).

---

## 4. Hasil Pengujian Empiris

Data mentah pengujian terekam di [`benchmark_embedding_indobert_comparison.json`](file:///home/luco/luco-untan/docs/laporan/raw/benchmark_embedding_indobert_comparison.json) dan log eksekusi [`benchmark_embedding_indobert_comparison.log`](file:///home/luco/luco-untan/docs/laporan/raw/benchmark_embedding_indobert_comparison.log).

### 4.1. Tabel Ringkasan Kinerja Utama

| Metrik Evaluasi | IndoBenchmark p1 | IndoBenchmark p2 | IndoLEM Uncased | Keunggulan IndoBenchmark |
| :--- | :---: | :---: | :---: | :---: |
| **Top-1 Retrieval Accuracy** | **80,0%** (8/10) | **80,0%** (8/10) | **40,0%** (4/10) | **+40,0% (2x lipat)** |
| **Top-3 Retrieval Recall** | **100,0%** (10/10) | **100,0%** (10/10) | **60,0%** (6/10) | **+40,0%** |
| **Rata-rata Margin Separasi ($\Delta$)** | **+0,2657** | **+0,2606** | **+0,0373** | **7,1x lebih tegas** |
| **Minimum Margin Separasi** | **+0,1442** | **+0,1368** | **-0,0815** (Gagal) | Stabil positif |
| **Maksimum Margin Separasi** | **+0,3693** | **+0,3594** | **+0,1187** | Pemisahan sangat kuat |
| **Rata-rata Latensi Inferensi** | 66,58 ms | 63,91 ms | 55,65 ms | Setara (~60 ms CPU) |

---

### 4.2. Detail Perbandingan Tiap Kasus Uji (Breakdown)

```
TC01 [Kerja Praktik (KP)]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.1442 (GT: 0.5110, Dist: 0.3667)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.1441 (GT: 0.4982, Dist: 0.3541)
- IndoLEM Uncased : GAGAL [Top-2] | Margin: +0.0266 (GT: 0.6276, Dist: 0.6009)

TC02 [Tugas Akhir / Skripsi]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.3020 (GT: 0.6402, Dist: 0.3382)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.3032 (GT: 0.6334, Dist: 0.3303)
- IndoLEM Uncased : OK [Top-1] | Margin: +0.0725 (GT: 0.7098, Dist: 0.6373)

TC03 [Profil Dosen AI & KBK]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.2909 (GT: 0.6836, Dist: 0.3927)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.2801 (GT: 0.6781, Dist: 0.3981)
- IndoLEM Uncased : GAGAL [Rank #8] | Margin: -0.0815 (GT: 0.6187, Distractor Cekungan Minyak: 0.7002!)

TC04 [Kurikulum Semester 4]
- IndoBenchmark p1: Rank #2 (kandidat prodi lain) | Margin: +0.2457 vs distractor
- IndoBenchmark p2: Rank #2 (kandidat prodi lain) | Margin: +0.2472 vs distractor
- IndoLEM Uncased : Rank #4 | Margin: +0.0588 vs distractor

TC07 [Yudisium & Kelulusan]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.2513 (GT: 0.5559, Dist: 0.3045)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.2567 (GT: 0.5616, Dist: 0.3049)
- IndoLEM Uncased : GAGAL [Rank #6] | Margin: -0.0343 (GT: 0.5375, Distractor Ekskavator: 0.5717!)

TC08 [Administrasi & UKT]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.3303 (GT: 0.6760, Dist: 0.3456)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.3153 (GT: 0.6434, Dist: 0.3282)
- IndoLEM Uncased : GAGAL [Top-2] | Margin: +0.0484 (GT: 0.5787, Dist: 0.5303)

TC09 [Peraturan Mengulang Matkul]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.3442 (GT: 0.6881, Dist: 0.3439)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.3568 (GT: 0.6851, Dist: 0.3282)
- IndoLEM Uncased : GAGAL [Rank #4] | Margin: +0.0201 (GT: 0.5432, Dist: 0.5232)

TC10 [Fasilitas & Sekretariat]
- IndoBenchmark p1: OK [Top-1] | Margin: +0.3693 (GT: 0.7122, Dist: 0.3429)
- IndoBenchmark p2: OK [Top-1] | Margin: +0.3594 (GT: 0.6870, Dist: 0.3276)
- IndoLEM Uncased : OK [Top-1] | Margin: +0.1187 (GT: 0.6999, Dist: 0.5812)
```

---

## 5. Analisis Mendalam: Mengapa IndoBenchmark Jauh Mengungguli IndoLEM?

### 5.1. Masalah Keruntuhan Representasi (*Representation Collapse*) pada IndoLEM
Pada pengujian IndoLEM, seluruh nilai kemiripan (*similarity score*) terkumpul dalam rentang yang sangat sempit dan tinggi (0,52 – 0,77), baik untuk teks relevan maupun teks distractor acak:
- **Kasus TC03 (Dosen AI)**: Dokumen distractor geologi batuan sedimen memperoleh skor **0,7002**, mengalahkan profil dosen AI Pak Izuardo (**0,6187**).
- **Kasus TC07 (Yudisium)**: Dokumen transmisi hidrolik ekskavator batubara memperoleh skor **0,5717**, mengalahkan berkas yudisium (**0,5375**).

Penyebab ilmiah:
1. **Volume Korpus IndoLEM Terlalu Kecil**: IndoLEM hanya dilatih pada ~220 juta kata dari portal berita (Kompas, Tempo) dan Wikipedia. Vektor representasi kalimat belum terpolarisasi dengan baik (*anisotropic embedding space*).
2. **Ketiadaan Konteks Percakapan/Akademik Mahasiswa**: Korpus berita formal tidak mencakup istilah percakapan, tanya-jawab, atau ragam teks interaktif kampus.

### 5.2. Keunggulan Korpus Indo4B pada IndoBenchmark
IndoBenchmark dilatih menggunakan korpus **Indo4B** (~3,6 miliar kata, sekitar 16 kali lipat lebih masif dibanding IndoLEM):
- Korpus mencakup ragam sumber yang jauh lebih kaya: Wikipedia, berita, artikel web, blog, dan media sosial.
- Model belajar memahami variasi gaya penulisan pertanyaan mahasiswa ("gimana alur", "syarat sempro", "ruang prodi") dan memetakannya secara tepat ke dokumen regulasi formal.
- **Margin Pemisahan yang Tegas**: Dokumen yang tidak relevan konsisten mendapatkan skor rendah di bawah 0,39, sedangkan dokumen ground truth memperoleh skor 0,55 – 0,71. Ini menghasilkan margin separasi rata-rata **+0,2657**, yang memberikan *safety boundary* kuat bagi retrieval OpenViking.

### 5.3. Pemilihan IndoBenchmark Phase 1 (`p1`) vs Phase 2 (`p2`)
- **IndoBenchmark p1** memiliki margin separasi rata-rata sedikit lebih tajam (**+0,2657**) dibandingkan p2 (**+0,2606**) untuk retrieval kalimat pertanyaan pendek (*short-query retrieval*).
- Keduanya sama-sama mencatat **100% Top-3 Recall**, menjamin bahwa teks yang dibutuhkan agen RAG selalu masuk ke jendela pembacaan agen.
- Oleh karena itu, arsitektur produksi Luco secara tepat menetapkan **`indobenchmark/indobert-base-p1`** sebagai dense embedding utama.

---

## 6. Poin Kunci untuk Presentasi ke Dosen Penguji

Saat mempresentasikan bagian sistem *Retrieval-Augmented Generation* (RAG) dan Vektor Semantik kepada dosen penguji, kelompok dapat menyampaikan argumen terstruktur berikut:

1. **Kesesuaian dengan Proposal Tugas Besar**:
   Sistem tidak mengandalkan model bahasa asing default seperti yang lazim terjadi di template tutorial, melainkan secara spesifik membangun microservice `luco-indobert` berbasis arsitektur BERT Bahasa Indonesia resmi.
2. **Kajian Komparatif Berbasis Data Nyata**:
   Telah diuji 3 varian BERT lokal (`indobenchmark/indobert-base-p1`, `indobenchmark/indobert-base-p2`, dan `indolem/indobert-base-uncased`) dengan 10 skenario pertanyaan nyata prodi dan 6 dokumen distractor.
3. **Temuan Ilmiah**:
   `indobenchmark/indobert-base-p1` mencatat **Top-1 Accuracy 80%** dan **Top-3 Recall 100%**, dengan margin separasi **+0,2657** (7x lebih tinggi dari IndoLEM yang hanya +0,0373). IndoLEM terbukti mengalami keruntuhan separasi representasi sehingga dokumen geologi atau hidrolik dapat mengalahkan dokumen akademik prodi.
4. **Efisiensi Sumber Daya**:
   Inference model hanya membutuhkan rata-rata **~66 ms** pada CPU standar tanpa memerlukan kartu grafis (GPU) mahal, sangat ideal untuk operasional server prodi.

---

## 7. Referensi File Terkait

- Data Mentah Benchmark JSON: [`benchmark_embedding_indobert_comparison.json`](file:///home/luco/luco-untan/docs/laporan/raw/benchmark_embedding_indobert_comparison.json)
- Log Eksekusi Uji: [`benchmark_embedding_indobert_comparison.log`](file:///home/luco/luco-untan/docs/laporan/raw/benchmark_embedding_indobert_comparison.log)
- Script Pengujian Mandiri: [`benchmark_embeddings.py`](file:///home/luco/luco-untan/scripts/benchmark_embeddings.py)
- Microservice Embedding Service: [`app.py`](file:///home/luco/luco-untan/dependencies/indobert-embedder/app.py)
- Konfigurasi OpenViking: [`ov.conf`](file:///home/luco/luco-untan/ov.conf)

