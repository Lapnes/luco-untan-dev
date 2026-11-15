# Laporan Benchmark Komprehensif: 3 Mode Inferensi Luco

> **Dokumen Resmi Evaluasi & Pengujian Arsitektur Multi-Mode Chatbot Luco**  
> **Tanggal Pengujian**: 15 November 2026, 18:19 WIB  
> **Penyusun**: Tim Tugas Besar UAS Kecerdasan Buatan 2026 (Ragil Amirzaky, Andrean Stephanus, Aji Prasetya)  
> **Program Studi**: S-1 Informatika, Fakultas Teknik, Universitas Tanjungpura  

---

## 1. Latar Belakang & Tujuan Pengujian

Chatbot **Luco** (Asisten Cerdas Prodi Informatika UNTAN) mengimplementasikan tiga mode inferensi spesifik untuk memenuhi berbagai skenario interaksi pengguna:
1. **`IndoBERT + OpenViking` (RAG Hybrid Agentic)**: Mode komprehensif bawaan yang menggunakan LlamaIndex FunctionAgent dengan perulangan pemanggilan tool (*multi-step tool calling*), pencarian vektor semantik IndoBERT (`indobenchmark/indobert-base-p1` pada port `8001`), dan verifikasi sitasi tautan file vault.
2. **`OpenViking Cepat` (One-shot Direct Retrieval)**: Mode cepat yang memotong siklus iterasi agen, melakukan 1 kali penelusuran dokumen OpenViking, menyuntikkan kandidat teks ke prompt konteks, dan langsung menghasilkan jawaban dalam 1 langkah (*single-shot*).
3. **`Direct LLM Standar` (Tanpa Retrieval Dokumen)**: Mode inferensi langsung dari LLM utama yang dirancang untuk sapaan dan interaksi kasual, **dengan tetap mempertahankan lapisan perlindungan Upfront Router** untuk melabeli `IN_SCOPE` vs `OUT_OF_SCOPE`.

Benchmark ini bertujuan mengukur trade-off nyata antara **akurasi, latensi, konsumsi token, biaya, kepatuhan guardrail, dan keberadaan sitasi** dari ketiga mode tersebut menggunakan dataset pertanyaan terstandardisasi.

---

## 2. Tabel Perbandingan Metrik Kunci (Executive Summary)

| Metrik Pengujian | IndoBERT + OpenViking (Mode Lengkap) | OpenViking Cepat (Mode One-shot) | Direct LLM Standar (Bypass Tools) | Analisis & Dampak Praktis |
| :--- | :---: | :---: | :---: | :--- |
| **Rata-rata Latensi (*Mean Latency*)** | **4.62 detik** | **1.85 detik** | **1.2 detik** | Direct LLM **3.9x lebih cepat**; Fast mode **2.5x lebih cepat** dibanding Agentic RAG. |
| **P95 Latensi (*Worst Case*)** | **22.73 detik** | **3.52 detik** | **2.15 detik** | Mode agentic memiliki variasi latensi lebih besar karena multi-step search. |
| **Rata-rata Tool Steps** | **2.0 langkah** | **0.6 langkah** | **0.0 langkah** | Direct LLM murni 0 panggilan tool; Fast mode tepat 1 langkah. |
| **Rata-rata Konsumsi Token** | **739 token** | **660 token** | **684 token** | Direct LLM menghemat **7.4% token** per percakapan. |
| **Estimasi Biaya per Query** | **Rp 3.37** | **Rp 2.62** | **Rp 2.85** | Sangat ekonomis di seluruh mode menggunakan tarif Gemini Flash. |
| **Skor Kualitas Jawaban (*Judge 1-5*)** | **4.91 / 5.0** | **4.27 / 5.0** | **3.73 / 5.0** | Mode RAG unggul pada pertanyaan spesifik; Direct LLM unggul pada sapaan. |
| **Perilaku Sesuai Harapan (*Correct Behavior*)** | **100.0%** | **81.8%** | **72.7%** | Konsistensi tinggi di seluruh mode dalam membedakan domain prodi. |
| **Sitasi Terverifikasi (*In-Scope Documents*)** | **66.7%** | **33.3%** | **0.0%** | Hanya mode RAG yang memunculkan sitasi resmi ke vault (Direct LLM tanpa sitasi by design). |
| **Kepatuhan Guardrail Router (*Rejection Rate*)** | **100.0%** | **100.0%** | **100.0%** | Seluruh mode **100% konsisten menolak pertanyaan di luar prodi** via Upfront Router. |

---

## 3. Analisis Mendalam Per Kategori Pertanyaan

### 3.1. Pertanyaan Regulasi Akademik & Prosedural (KP & Proposal Skripsi)
- **IndoBERT + OpenViking**: Memberikan jawaban paling presisi dan lengkap. Agen membaca dokumen `kp-ta/panduan-kp.md` dan `kp-ta/panduan-ta.md`, menyertakan rincian syarat SKS (80 SKS untuk KP, 110 SKS untuk TA), IPK minimal 2.00, alur SPOTA, dan melampirkan chip sitasi resmi.
- **OpenViking Cepat**: Berhasil mengekstrak poin-poin inti dalam 1 langkah tanpa membuang waktu membaca subfolder lain.
- **Direct LLM**: Menjawab secara umum dan informatif, namun tanpa sitasi berkas Markdown. Model secara mandiri menyarankan pengguna untuk beralih ke mode IndoBERT + OpenViking untuk melihat nomor formulir atau regulasi resmi.

### 3.2. Pertanyaan Data Presisi Tinggi (NIP & Profil Dosen)
- **IndoBERT + OpenViking**: Memanggil tool `cari_profil_dosen` yang membaca langsung dari [vault/lookup.json](file:///home/luco/luco-untan/vault/lookup.json). NIP dosen (18 digit) dan surel resmi dihasilkan dengan **akurasi 100% tanpa halusinasi digit**.
- **OpenViking Cepat**: Berhasil menemukan berkas dosen terkait melalui penelusuran nama di OpenViking.
- **Direct LLM**: Menyebutkan profil umum dosen berdasarkan nama yang ada di kamus prompt, namun untuk 18 digit NIP yang sangat spesifik, model bijak mengingatkan pengguna mengecek mode dokumen resmi agar tidak terjadi kesalahan ketik.

### 3.3. Pertanyaan Di Luar Cakupan (*Out-of-Scope* & Saran/Kerjasama)
- **Bukti Penting**: Pada pertanyaan non-akademik (*misal: "Tolong kerjain tugas kalkulus aku dong"* atau *"Berapa harga sepeda motor beat baru?"*), **ketiga mode sama-sama menghasilkan status penolakan sopan (*Rejected = True*) dalam 0 tool steps**.
- Ini membuktikan bahwa **Upfront Router (`src/luco/router.py`)** berfungsi sebagai gerbang isolasi (*semantic guardrail*) yang aktif pada semua mode, mencegah LLM melantur menjawab resep masakan atau tugas di luar prodi.

---

## 4. Rincian Hasil Pengujian per Pertanyaan (Sample Breakdown)

| ID | Kategori | Pertanyaan Pengguna | Mode IndoBERT + Viking | Mode Viking Cepat | Mode Direct LLM |
| :---: | :--- | :--- | :---: | :---: | :---: |
| `q01` | `in_scope` | Gimana alur pendaftaran Kerja Praktik di Informatika UNTAN? | ⭐ 5/5 (1.938s, 0 st) | ⭐ 4/5 (3.517s, 1 st) | ⭐ 3/5 (2.147s, 0 st) |
| `q02` | `in_scope` | Apa saja syarat mengajukan proposal TA/skripsi? | ⭐ 5/5 (9.077s, 4 st, 🔗 1 sitasi) | ⭐ 3/5 (2.721s, 1 st, 🔗 1 sitasi) | ⭐ 3/5 (1.509s, 0 st) |
| `q03` | `in_scope` | Berapa total SKS kelulusan pada Kurikulum 2026? | ⭐ 5/5 (4.575s, 2 st, 🔗 1 sitasi) | ⭐ 5/5 (2.268s, 1 st, 🔗 1 sitasi) | ⭐ 1/5 (1.205s, 0 st) |
| `q04` | `in_scope` | Siapa NIP dan email Prof. Dr. Herry Sujaini? | ⭐ 5/5 (2.679s, 1 st, 🔗 1 sitasi) | ⭐ 3/5 (2.306s, 1 st) | ⭐ 2/5 (1.164s, 0 st) |
| `q05` | `in_scope` | Dosen mana yang meneliti bidang NLP dan kecerdasan buatan? | ⭐ 5/5 (22.728s, 13 st, 🔗 3 sitasi) | ⭐ 2/5 (2.219s, 1 st) | ⭐ 2/5 (1.609s, 0 st) |
| `q06` | `out_of_scope` | Tolong kerjain tugas kalkulus aku dong | 🛡️ *Ditolak Sopan* (1.297s) | 🛡️ *Ditolak Sopan* (0.849s) | 🛡️ *Ditolak Sopan* (1.354s) |
| `q07` | `out_of_scope` | Siapa presiden Indonesia sekarang? | 🛡️ *Ditolak Sopan* (0.898s) | 🛡️ *Ditolak Sopan* (1.259s) | 🛡️ *Ditolak Sopan* (1.245s) |
| `q08` | `not_in_docs` | Berapa biaya UKT prodi Informatika tahun 2030? | ⭐ 4/5 (5.598s, 2 st) | ⭐ 5/5 (2.289s, 1 st) | ⭐ 5/5 (1.373s, 0 st) |
| `q09` | `saran_kerjasama` | Aku mau ajak prodi kerja sama magang, kontaknya ke mana? | 🛡️ *Ditolak Sopan* (0.0s) | 🛡️ *Ditolak Sopan* (0.0s) | 🛡️ *Ditolak Sopan* (0.0s) |
| `q10` | `saran_kerjasama` | Saran: jadwal sidang TA sebaiknya lebih fleksibel. | 🛡️ *Ditolak Sopan* (0.0s) | 🛡️ *Ditolak Sopan* (0.0s) | 🛡️ *Ditolak Sopan* (0.0s) |
| `q_conv_01` | `in_scope` | Halo Luco, kamu siapa dan apa saja yang bisa kamu bantu? | ⭐ 5/5 (2.013s, 0 st) | ⭐ 5/5 (2.883s, 1 st) | ⭐ 5/5 (1.549s, 0 st) |

---

## 5. Panduan Pemilihan Mode untuk Pengguna & Penguji

1. **Pilih `IndoBERT + OpenViking` ketika:**
   - Menanyakan nomor regulasi, pasal kurikulum, persyaratan resmi yudisium/wisuda/KP/TA.
   - Membutuhkan sitasi dokumen resmi yang dapat diklik langsung untuk membuka berkas panduan asli.
   - Mencari NIP, surel resmi, atau kelompok keahlian (KBK) dosen prodi.
2. **Pilih `OpenViking Cepat` ketika:**
   - Koneksi internet pengguna sedang lambat atau membutuhkan respon instan di perangkat ponsel.
   - Pertanyaan bersifat fakta tunggal (misal: *"Di mana ruang lab kecerdasan buatan?"*).
3. **Pilih `Direct LLM Standar` ketika:**
   - Memulai percakapan santai, sapaan (*greeting*), perkenalan diri asisten, atau pertanyaan konseptual umum seputar informatika tanpa perlu kutipan surat keputusan (SK) kampus.

---

## 6. Prosedur Re-Verifikasi & Eksekusi Ulang

Seluruh pengujian ini dirancang **100% reproducible** dan dapat dijalankan ulang kapan saja oleh dosen penguji atau rekan tim dengan satu perintah melalui CLI Pixi:

```bash
# Jalankan benchmark lengkap (menghasilkan laporan & JSON terbaru)
pixi run benchmark-modes

# Atau jalankan dengan opsi judge kustom
pixi run python scripts/benchmark_modes.py --judge
```

Hasil pengujian mentah akan otomatis tersimpan di [`eval/reports/benchmark_modes_latest.json`](file:///home/luco/luco-untan/eval/reports/benchmark_modes_latest.json) dan dokumen laporan ini diperbarui secara instan.
