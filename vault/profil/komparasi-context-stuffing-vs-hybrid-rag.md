---
judul: "Perbandingan Full Context Injection vs Arsitektur Hybrid Agentic RAG Luco"
kategori: "profil"
slug: "komparasi-context-stuffing-vs-hybrid-rag"
sumber: "Laporan Evaluasi Multi-Turn Percakapan Luco 2026"
terakhir_diperbarui: "2026-11-15"
ringkasan: "Hasil pengujian empiris kuantitatif komparasi metode konvensional Full Context Injection (Context Stuffing) melawan Arsitektur Hybrid Agentic RAG Luco pada percakapan multi-turn."
---

# Perbandingan Full Context Injection vs Arsitektur Hybrid Agentic RAG Luco

Dalam pengembangan sistem berbasis LLM untuk dokumen kampus, terdapat dua pendekatan utama yang dapat dipilih:
1. **Pendekatan Konvensional: Full Context Injection (*Brute-Force Context Stuffing*)**  
   Menyuntikkan (*inject*) seluruh naskah dokumen basis pengetahuan kampus (133.752 karakter / ~33.438 token) secara statis ke dalam *system prompt* LLM pada setiap giliran percakapan.
2. **Pendekatan Luco: Hybrid Agentic RAG (Retrieval-Augmented Generation)**  
   Menggunakan arsitektur cerdas berlapis: **Upfront Router** untuk fast-reject sapaan/non-akademik (0 ms), **OpenViking + IndoBERT (768 dimensi)** untuk penelusuran dinamis hanya pada potongan dokumen yang relevan, **`lookup.json` deterministik** untuk data kritis presisi (seperti NIP 18 digit dosen), dan **Sliding-Window Memory** (maksimal 6 pesan terakhir).

---

## 1. Berapa Banyak yang Dihemat oleh Arsitektur Hybrid RAG Luco?

Berdasarkan hasil pengujian empiris langsung pada percakapan panjang (*multi-turn conversation* berurutan sebanyak 6 pesan mahasiswa):

| Metrik Evaluasi | Full Context Injection (Inject Langsung) | Arsitektur Luco (Hybrid Agentic RAG) | Jumlah yang Dihemat (*Savings*) |
| :--- | :---: | :---: | :--- |
| **Total Token Kumulatif (6 Turn)** | **300.049 token** | **6.723 token** | **Dihemat 293.326 token (97,76% lebih hemat / 44,6x lipat)** |
| **Rata-rata Token per Pesan** | **50.008 token** | **1.120 token** | Penghematan masif di setiap interaksi |
| **Biaya 1 Sesi Percakapan (6 Turn)** | **Rp 495,53** | **Rp 16,54** | **Dihemat Rp 478,99 per sesi (96,66% lebih murah / 30x lipat)** |
| **Biaya Skala 10.000 Sesi/Bulan** | **Rp 4.955.300 / bulan** | **Rp 165.400 / bulan** | **Menghemat anggaran Rp 4,79 Juta setiap bulan** |
| **Token Sapaan / Greeting (Turn 1)** | 49.063 token (Rp 81,84) | **598 token (Rp 2,07)** | Menghemat 98,8% token hanya untuk menyapa |
| **Token Kueri Di Luar Prodi (Turn 6)** | 50.691 token (Rp 82,72) | **1.250 token (Rp 2,41)** | Ditangkal router tanpa membuang token membaca ratusan dokumen |

---

## 2. Mengapa Arsitektur Hybrid Jauh Lebih Unggul?

### A. Mengatasi Fenomena "Lost in the Middle" (Needle in a Haystack)
- **Kelemahan Inject Langsung**: Saat seluruh dokumen disuntikkan (133 ribu karakter), mekanisme *self-attention* model mengalami pelemahan konsentrasi (*attention dilution*). Pada pengujian pencarian NIP 18 digit Prof. Dr. Herry Sujaini, metode inject langsung **GAGAL** menemukan NIP dan menyatakan data tidak ada di dokumen.
- **Keunggulan Hybrid Luco**: Luco menggunakan jalur deterministik `cari_profil_dosen` yang membaca `vault/lookup.json`. NIP `196806291997021001` dan KBK *Computation & Artificial Intelligence* dikembalikan dalam **1,891 detik** dengan **akurasi 100% tanpa risiko halusinasi angka**.

### B. Keterlacakan dan Integritas Sitasi (*Grounded Citations*)
- **Inject Langsung**: Menghasilkan paragraf teks tanpa tautan rujukan resmi yang dapat diverifikasi (*citation rate: 0%*).
- **Hybrid Luco**: Menghasilkan jawaban yang selalu disertai chip rujukan resmi (`[Panduan KP](kp-ta/panduan-kp.md)`) yang diverifikasi programatik oleh `citations.py` (*citation rate: 100%*).

### C. Ketahanan Terhadap Batas Laju (*TPM Rate Limit*)
- **Inject Langsung**: Sangat rentan memicu error `429 Too Many Requests`. Jika ada 3 mahasiswa yang bertanya bersamaan dalam 1 menit, konsumsi token mencapai $\sim 900.000$ token dan langsung menabrak batas kuota *Tokens Per Minute* (TPM) penyedia API.
- **Hybrid Luco**: Karena hanya mengonsumsi $\sim 1.000$ token per pesan, sistem mampu melayani ratusan mahasiswa secara bersamaan secara stabil dan tanpa gangguan *rate limit*.
