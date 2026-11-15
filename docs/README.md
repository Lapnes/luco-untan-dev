# Dokumentasi Luco (Informatika UNTAN)

Selamat datang di pusat dokumentasi teknis **Luco 🐦**, asisten kecerdasan buatan berbasis *Hybrid Agentic Retrieval-Augmented Generation (RAG)* untuk Program Studi Informatika, Fakultas Teknik, Universitas Tanjungpura.

Dokumentasi ini disusun dengan standar proyek perangkat lunak skala produksi untuk memudahkan pengembangan, pengujian, pemeliharaan, serta penulisan laporan akademik Tugas Besar UAS Kecerdasan Buatan 2026.

---

## 🗺️ Peta Dokumentasi (Sitemap)

| Dokumen | Topik & Cakupan Utama | Sasaran Pembaca |
| :--- | :--- | :--- |
| **[Arsitektur Sistem](file:///home/luco/luco-untan/docs/architecture.md)** | Desain sistem Dual-LLM, alur Agentic RAG, diagram alir, router heuristik mutakhir, dan paradigma memori *"Single Active Session with Archiving"*. | Pengembang Backend, Arsitek Sistem, Penguji Akademik |
| **[Referensi API](file:///home/luco/luco-untan/docs/api-reference.md)** | Kontrak lengkap REST API (Auth, Google OAuth, Sesi Aktif, Chat, Katalog 26 Berkas Resmi Directus, OpenAI Compatible, Monitoring). | Pengembang Frontend UI, Integrator Pihak Ketiga |
| **[Desain Database](file:///home/luco/luco-untan/docs/database.md)** | Skema PostgreSQL 16, kolom klarifikasi interaktif, indeks parsial unik, integritas data, dan visualisasi ERD. | Database Administrator, Backend Developer |
| **[Sistem Rate Limiting](file:///home/luco/luco-untan/docs/rate-limiting.md)** | Analisis teknis *Anti-Ban IP* di lingkungan CGNAT, algoritma *sliding window* RPM & TPM, dan keunggulan efisiensi token RAG vs Context Stuffing. | DevOps, Backend & Security Engineer |
| **[Manajemen Pengetahuan (Vault)](file:///home/luco/luco-untan/docs/vault-and-knowledge.md)** | Panduan 104 dokumen Markdown (7 kategori semantik), generator `lookup.json` (33 dosen), katalog 26 berkas Directus, dan validasi tautan. | Kurator Data, Pengelola Konten Akademik |
| **[Panduan Deployment & Operasional](file:///home/luco/luco-untan/docs/deployment.md)** | Petunjuk instalasi dependensi via Pixi, orkestrasi 4 container Docker (PostgreSQL, OpenViking, IndoBERT, Proxy), konfigurasi environment. | DevOps, System Administrator |
| **[Evaluasi & Benchmark RAG](file:///home/luco/luco-untan/docs/evaluation.md)** | Metodologi evaluasi LLM-as-a-judge, dataset benchmark `questions.jsonl`, komparasi 3 mode inferensi, dan benchmark Context Stuffing vs RAG. | Peneliti AI, Evaluator Akademik |
| **[Naskah Master Laporan Akhir (Bab I–VI)](file:///home/luco/luco-untan/docs/laporan/final/laporan_lengkap_tugas_besar_ai_luco.md)** | Dokumen master komprehensif Tugas Besar Pengganti UAS AI 2026 (Pendahuluan, Teori, Perancangan, Implementasi, Pengujian, Penutup). | Dosen Penguji, Tim Pengembang, Mahasiswa |
| **[Laporan Pengujian Menyeluruh Sistem](file:///home/luco/luco-untan/docs/laporan/final/laporan_pengujian_keseluruhan_aplikasi.md)** | Hasil pengujian empiris menyeluruh seluruh aplikasi, 78/78 Pytest lolos 100%, multi-provider LLM failover, OpenViking, dan verifikasi sitasi. | Dosen Penguji, Tim Pengembang |
| **[Evaluasi Context Stuffing vs Hybrid RAG](file:///home/luco/luco-untan/docs/laporan/final/perbandingan_context_stuffing_vs_arsitektur_luco.md)** | Bukti empiris keunggulan Hybrid RAG atas inject langsung pada percakapan multi-turn (hemat 97,76% token, hemat 96,66% biaya, bebas lost-in-the-middle). | Dosen Penguji, Peneliti AI |
| **[Komparasi Embedding IndoBERT](file:///home/luco/luco-untan/docs/laporan/final/perbandingan_embedding_indobert.md)** | Kajian komparatif empiris IndoBenchmark vs IndoLEM (akurasi, margin separasi, mitigasi collapse representasi). | Dosen Penguji, Peneliti NLP |
| **[Benchmark 3 Mode Inferensi](file:///home/luco/luco-untan/docs/laporan/final/benchmark_3_mode_inferensi.md)** | Analisis komparasi performa IndoBERT + OpenViking, OpenViking Cepat, dan Direct LLM Standar. | Dosen Penguji, Pengembang Sistem |

---

## 📞 Kontak Resmi Program Studi Informatika UNTAN
- **WhatsApp / Telepon**: [+62 851-7165-5161](https://wa.me/6285171655161)
- **Surel (Email)**: [info@informatika.untan.ac.id](mailto:info@informatika.untan.ac.id)
- **Instagram**: [@informatika.untan](https://instagram.com/informatika.untan)
- **Alamat**: Lantai 2 Gedung Jurusan Teknik Elektro, Fakultas Teknik Universitas Tanjungpura, Jl. Prof. Dr. H. Hadari Nawawi, Pontianak 78124.

---

## 🚀 Jalur Membaca Rekomendasi (Reading Paths)

### 1. Untuk Pengembang Baru (Quick Start Developer)
1. Baca ringkasan kondisi sistem saat ini di [CURRENT_STATE.md](file:///home/luco/luco-untan/CURRENT_STATE.md).
2. Ikuti langkah instalasi lokal di [Panduan Deployment](file:///home/luco/luco-untan/docs/deployment.md).
3. Pahami cara agen bekerja di [Arsitektur Sistem](file:///home/luco/luco-untan/docs/architecture.md).

### 2. Untuk Pengembang Frontend UI
1. Pelajari alur otentikasi dan sesi aktif di [Referensi API](file:///home/luco/luco-untan/docs/api-reference.md).
2. Pahami bagaimana token rate limit dan header respons `Retry-After` bekerja di [Sistem Rate Limiting](file:///home/luco/luco-untan/docs/rate-limiting.md).

### 3. Untuk Tim Kurator Konten & Data Prodi
1. Pelajari struktur penulisan profil dosen dan kurikulum di [Manajemen Pengetahuan (Vault)](file:///home/luco/luco-untan/docs/vault-and-knowledge.md).
2. Jalankan perintah `pixi run build-lookup` dan `pixi run check-links` setiap kali memperbarui vault.

