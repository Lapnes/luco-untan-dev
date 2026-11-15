---
tipe: profil_pengembang
judul: "Sejarah & Tim Pengembang Luco — Chatbot RAG Informatika UNTAN"
mata_kuliah: "Kecerdasan Buatan (Tugas Besar Pengganti UAS 2026)"
program_studi: S1 Informatika
fakultas: Fakultas Teknik
universitas: Universitas Tanjungpura
tahun: 2026
anggota_ai_uas:
  - nama: Ragil Amirzaky
    nim: D1041241069
    peran: Lead Developer & Systems/Cloud Architect
    profil_url: "../kemahasiswaan/ragil-amirzaky.md"
  - nama: Andrean Stephanus
    nim: D1041241027
    peran: Co-Developer & Data/Evaluation Engineer
  - nama: Adjie Prasetya
    nim: D1041241038
    peran: Co-Developer & Knowledge Vault Curation
kontributor_dan_sejarah:
  - nama: Balin Niswah
    peran: Topik Skripsi / Inisiator Awal
  - nama: Edwin Hermili
    peran: Tim Sistem Production-Ready (Agentic, RAG & Tool Calling)
sumber:
  - https://www.ragilamirzaky.com
  - https://tenzly.pro
  - https://www.linkedin.com/in/balin-niswah-4855a0261/
  - https://www.linkedin.com/in/etherift
  - https://www.etherift.website/en
  - https://github.com/etherift
  - https://www.linkedin.com/in/edwinhermili/
  - https://github.com/problem-setter
  - https://www.linkedin.com/in/ajiii/
  - https://github.com/AdjiePrasetya
---

# Sejarah & Tim Pengembang Luco (luco-untan)

**Luco 🐦** adalah sistem asisten informasi cerdas Program Studi S1 Informatika, Fakultas Teknik, Universitas Tanjungpura (UNTAN). 

Perjalanan pengembangan Luco memiliki kronologi dan silsilah teknis yang jelas:

---

## 📜 Kronologi & Silsilah Pengembangan Luco

### 1. Fase Skripsi Awal
Proyek ini awalnya bermula dari **topik skripsi/Tugas Akhir yang diinisiasi oleh [Balin Niswah](https://www.linkedin.com/in/balin-niswah-4855a0261/)**, yang merumuskan riset awal kebutuhan asisten informasi akademik di lingkungan Informatika UNTAN.

### 2. Fase Pembangunan Sistem Production-Ready (Asisten Prodi & Dosen)
Setelah inisiasi skripsi tersebut, pengembangan dilanjutkan oleh tim pengembang inti:
- **Ragil Amirzaky**: Lead Developer ([Portofolio](https://www.ragilamirzaky.com) · [GitHub](https://github.com/Lapnes))
- **Andrean Stephanus**: Co-Developer & Evaluator ([Website](https://www.etherift.website/en) · [GitHub](https://github.com/etherift) · [LinkedIn](https://www.linkedin.com/in/etherift?originalSubdomain=id))
- **Edwin Hermili**: Co-Developer Sistem Production-Ready ([GitHub](https://github.com/problem-setter) · [LinkedIn](https://www.linkedin.com/in/edwinhermili/))

> [!IMPORTANT]
> **Pemisahan Tautan & Identitas Resmi**:
> - **Andrean Stephanus**: Menggunakan identitas alias **Etherift** dengan website pribadi [etherift.website](https://www.etherift.website/en), GitHub [github.com/etherift](https://github.com/etherift), dan LinkedIn [linkedin.com/in/etherift](https://www.linkedin.com/in/etherift?originalSubdomain=id).
> - **Edwin Hermili**: Memiliki GitHub [github.com/problem-setter](https://github.com/problem-setter) dan LinkedIn [linkedin.com/in/edwinhermili](https://www.linkedin.com/in/edwinhermili/). Edwin **TIDAK memiliki afiliasi dengan website etherift.website**, jangan mencampuradukkan tautan Andrean Stephanus ke Edwin Hermili!

Pada tahap ini, mereka bertiga merancang dan membangun sistem yang *Production-Ready* dengan kapabilitas **Agentic, RAG (yang awalnya berbasis semi-GraphRAG), dan Tool Calling** sebagai asisten resmi Informatika UNTAN. Target sistem ini dirancang agar dapat digunakan langsung oleh dosen-dosen Informatika sebagai asisten pribadi/akademik mereka. Saat ini, inisiatif asisten dosen tersebut masih dalam tahap pengembangan (~80%) dan belum resmi digunakan oleh para dosen.

### 3. Fase Perombakan RAG: Hybrid Agentic RAG (Tugas Besar AI 2026)
Ketika ada tugas akademik **Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan (AI) Tahun Ajaran 2026**, tim beranggotakan:
- **Ragil Amirzaky** (D1041241069) — *Lead Developer & Systems/Cloud Architect* ([Profil Detail](../kemahasiswaan/ragil-amirzaky.md))
- **Andrean Stephanus** (D1041241027) — *Co-Developer & Evaluation Engineer* ([Profil Detail](../kemahasiswaan/andrean-stephanus.md))
- **Adjie Prasetya** (D1041241038) — *Co-Developer & Knowledge Curation Engineer* ([GitHub](https://github.com/AdjiePrasetya) · [LinkedIn](https://www.linkedin.com/in/ajiii/) · [Profil Detail](../kemahasiswaan/adjie-prasetya.md))

Fokus tim ini adalah **merombak khusus modul RAG-nya saja (RAG-nya doang)**. Modul RAG yang awalnya berbasis *semi-GraphRAG* dirombak secara komprehensif menjadi **Hybrid Agentic RAG**:
1. **Integrasi OpenViking Retrieval**: Mengadopsi mesin pencari dokumen hierarkis OpenViking dalam kontainer Docker (:1933) untuk navigasi dokumen akademik bertingkat (L0 direktori $\rightarrow$ L1 ringkasan $\rightarrow$ L2 teks lengkap).
2. **Jalur Deterministik Tanpa Halusinasi**: Membangun `vault/lookup.json` khusus untuk data presisi 33 dosen Informatika UNTAN (NIP, email, kelompok keahlian).
3. **Dual-Model Inference & Fast Router**: Mengembangkan router dua tahap (*heuristics fast-path* + LLM ringan) untuk klasifikasi cepat pertanyaan *in-scope*, pengalihan kontak, dan pencegahan halusinasi.
4. **Antarmuka Web Modern & Verifikasi Sitasi**: Mengembangkan UI interaktif berbasis React, TypeScript, dan Tailwind CSS, lengkap dengan drawer rujukan dokumen resmi dan verifikasi sitasi *footnote*.

---

## 👥 Direktori Tim & Kontributor

| Nama | Peran & Kontribusi | Tautan Resmi & Profil | Berkas Profil Vault |
| :--- | :--- | :--- | :--- |
| **Ragil Amirzaky** | Lead Developer & Systems/Cloud Architect (Pembangunan sistem production-ready bersama Andrean & Edwin; perombakan modul RAG menjadi Hybrid Agentic RAG bersama Andrean & Adjie) | [ragilamirzaky.com](https://www.ragilamirzaky.com) · [GitHub](https://github.com/Lapnes) | [ragil-amirzaky.md](../kemahasiswaan/ragil-amirzaky.md) |
| **Andrean Stephanus** | Co-Developer & Data/Evaluation Engineer (Pengembangan sistem production-ready; evaluasi & benchmark perombakan RAG) | [etherift.website](https://www.etherift.website/en) · [GitHub](https://github.com/etherift) · [LinkedIn](https://www.linkedin.com/in/etherift?originalSubdomain=id) | [andrean-stephanus.md](../kemahasiswaan/andrean-stephanus.md) |
| **Adjie Prasetya** | Co-Developer & Knowledge Vault Curation (Perombakan modul RAG untuk Tugas Besar AI 2026, kurasi dokumen vault & panduan akademik) | [GitHub](https://github.com/AdjiePrasetya) · [LinkedIn](https://www.linkedin.com/in/ajiii/) | [adjie-prasetya.md](../kemahasiswaan/adjie-prasetya.md) |
| **Edwin Hermili** | Co-Developer Sistem Production-Ready (Pembangunan fondasi sistem Agentic, semi-GraphRAG, dan tool calling bersama Ragil & Andrean) | [GitHub](https://github.com/problem-setter) · [LinkedIn](https://www.linkedin.com/in/edwinhermili/) | [edwin-hermili.md](../kemahasiswaan/edwin-hermili.md) |
| **Balin Niswah** | Penggagas & Topik Skripsi Awal (Riset awal asisten informasi prodi Informatika UNTAN) | [LinkedIn](https://www.linkedin.com/in/balin-niswah-4855a0261/) | [balin-niswah.md](../kemahasiswaan/balin-niswah.md) |

---

## 🎯 Tujuan dan Inovasi Proyek
1. **Mengatasi Halusinasi LLM**: Menggunakan jalur data deterministik (`vault/lookup.json`) untuk informasi sensitif seperti NIP dan surel dosen, serta validasi sitasi ketat (*grounded generation*).
2. **Navigasi Hierarkis Dokumen**: Mengadopsi teknologi pencarian hierarkis OpenViking untuk memudahkan penelusuran aturan akademik berlapis (KP, TA, Seminar Proposal, Sidang Skripsi).
3. **Privasi & Efisiensi Kampus**: Mengedepankan arsitektur mandiri (*self-hosted stack*) yang dapat dioperasikan secara lokal pada server kampus tanpa ketergantungan berlebihan pada pihak ketiga.

---

## 🔗 Tautan Dokumen Terkait
- [Hasil Benchmark Model & Evaluasi Performa Luco](benchmark-dan-evaluasi-model.md)
- [Perbandingan Full Context Injection vs Hybrid RAG Luco](komparasi-context-stuffing-vs-hybrid-rag.md)
- [Kontak Resmi Program Studi Informatika UNTAN](kontak.md)
- [Profil Detail Ragil Amirzaky](../kemahasiswaan/ragil-amirzaky.md)
- [Struktur Organisasi Jurusan & Prodi](struktur-organisasi.md)
- [Visi, Misi, dan Tujuan Prodi](visi-misi.md)
- [Indeks Utama Basis Pengetahuan](../README.md)
