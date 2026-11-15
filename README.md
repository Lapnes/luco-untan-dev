# Luco 🐦 (luco-untan)

Chatbot Asisten Informasi Program Studi Informatika, Fakultas Teknik, Universitas Tanjungpura.  
Berawal dari topik skripsi/Tugas Akhir **Balin Niswah**, yang kemudian dikembangkan menjadi sistem *production-ready* (Agentic, semi-GraphRAG, dan *tool calling*) sebagai asisten Informatika dan dosen oleh **Ragil Amirzaky**, **Andrean Stephanus**, dan **Edwin Hermili** (progres saat ini ~80%).

Modul RAG-nya (*RAG only*) kemudian dirombak dari semi-GraphRAG menjadi **Hybrid Agentic RAG** (integrasi OpenViking & lookup deterministik) sebagai **Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan 2026** oleh:
- **Ragil Amirzaky** (Lead Developer & Systems/Cloud Architect)
- **Andrean Stephanus** (Co-Developer & Evaluation Engineer)
- **Adjie Prasetya** (Co-Developer & Knowledge Curation Engineer)

Sistem menerapkan arsitektur **Hybrid Agentic RAG (Retrieval-Augmented Generation)**: memadukan penalaran otonom **LlamaIndex** (`FunctionAgent`), mesin pencari dokumen hierarkis **OpenViking** (Docker), dan jalur deterministik **vault/lookup.json** untuk data presisi tanpa halusinasi (seperti NIP dan surel dosen).

---

## 📌 Dokumen Penting Proyek

| Dokumen | Deskripsi |
| :--- | :--- |
| 📊 **[CURRENT_STATE.md](file:///home/luco/luco-untan/CURRENT_STATE.md)** | **Status Terkini Sistem**: Matriks kesiapan komponen, hasil pengujian, dan rencana aksi tim. |
| 📑 **[Laporan Hasil Pengujian & Benchmark](file:///home/luco/luco-untan/docs/laporan/final/laporan_pengujian_keseluruhan_aplikasi.md)** | **Data Pengujian Menyeluruh**: Laporan pengujian end-to-end, hasil benchmark IndoBERT vs IndoLEM, dan verifikasi sitasi. |
| 🚶 **[WALKTHROUGH.md](file:///home/luco/luco-untan/WALKTHROUGH.md)** | **Panduan Lengkap Langkah Demi Langkah**: Tutorial dari awal setup, pengujian, kurasi data, hingga evaluasi. |
| 📚 **[Pusat Dokumentasi (docs/)](file:///home/luco/luco-untan/docs/README.md)** | Indeks dokumentasi mendalam: [Arsitektur](file:///home/luco/luco-untan/docs/architecture.md), [Referensi API](file:///home/luco/luco-untan/docs/api-reference.md), [Database](file:///home/luco/luco-untan/docs/database.md), [Rate Limiting](file:///home/luco/luco-untan/docs/rate-limiting.md), [Vault](file:///home/luco/luco-untan/docs/vault-and-knowledge.md), [Deployment](file:///home/luco/luco-untan/docs/deployment.md), dan [Evaluasi](file:///home/luco/luco-untan/docs/evaluation.md). |
| 📜 **[AGENTS.md](file:///home/luco/luco-untan/AGENTS.md)** | Pedoman kontribusi kode, aturan repo, dan batasan lingkup akademik. |

---

## 🏗️ Arsitektur Sistem Singkat

```
vault/ (Markdown + YAML Frontmatter) ──► scripts/build_lookup.py ──► vault/lookup.json (Data Pasti NIP/Email)
        │ 
        ▼ scripts/ingest.py
OpenViking (Docker :1933) ◄── openviking-sdk
                                    │
                                    ▼
[Pengguna / UI] ──► FastAPI Router (:8000) ──► JWT Auth & Identity Rate Limiter (Anti-Ban IP)
                                    │
                                    ▼
                       Dual-LLM Step 1: Upfront Router (Fast Reject / Pengalihan Kontak)
                                    │ (Jika IN_SCOPE)
                                    ▼
                       Dual-LLM Step 2: LlamaIndex FunctionAgent
                                    ├── cari_profil_dosen (lookup.json)
                                    ├── telusuri_direktori_prodi (OpenViking find)
                                    ├── baca_dokumen_lengkap (OpenViking read)
                                    └── list_docs (OpenViking ls)
                                    │
                                    ▼
                      citations.py (Validasi Tautan Sumber Jawaban)
                                    │
                                    ▼
                      PostgreSQL 16: asyncpg (:5432)
                      (Single Active Session with Archiving + Audit Token Logs)
```

---

## ⚡ Perintah Cepat (Pixi)

Proyek ini dikelola menggunakan package manager [Pixi](https://pixi.sh/). Seluruh task dapat dijalankan dengan perintah `pixi run <task>`:

```bash
# 1. Menyiapkan environment & dependensi
pixi install

# 2. Menjalankan seluruh pengujian unit otomatis
pixi run test

# 3. Menghasilkan vault/lookup.json dari frontmatter dosen
pixi run build-lookup

# 4. Menghasilkan JSON Tree Manifest pemetaan heading (Lembar Konsultasi)
pixi run build-manifest

# 5. Memeriksa integritas tautan antar-catatan di vault
pixi run check-links

# 6. Menjalankan sub-services Docker (PostgreSQL, OpenViking, Antigravity Proxy, IndoBERT)
pixi run up:deps

# 7. Menjalankan server REST API di http://localhost:8000
pixi run serve

# 8. Menjalankan antarmuka terminal interaktif (REPL)
pixi run chat

# 9. Membuka dashboard pemantauan live & ringkasan audit token/biaya
pixi run monitor

# 10. Menjalankan evaluasi tolok ukur (Luco RAG vs Baseline tanpa RAG)
pixi run eval -- --judge

# 11. Benchmark 3 mode inferensi (IndoBERT + Viking vs Fast vs Direct LLM)
pixi run benchmark-modes

# 12. Benchmark komparasi varian embedding IndoBERT (Indo4B p1 vs p2 vs IndoLEM)
pixi run benchmark-bert

# 13. Benchmark empiris Context Stuffing vs Luco Hybrid RAG
pixi run benchmark-context
```

---

## 🚦 Mulai Cepat (Quickstart)

1. **Instalasi Dependensi:**
   ```bash
   pixi install
   cp .env.example .env
   cp ov.conf.example ov.conf
   ```
2. **Mode Lokal (Tanpa OpenViking terlebih dahulu):**
   - Pastikan di `.env`: `LUCO_BACKEND=local`.
   - Jalankan `pixi run build-lookup && pixi run build-manifest`.
   - Coba obrolan langsung via CLI: `pixi run chat` atau API: `pixi run serve`.
3. **Mode Produksi Penuh (Dengan OpenViking & PostgreSQL):**
   - Jalankan dependensi: `pixi run up:deps`.
   - Buka `http://localhost:3000` untuk login akun Google di dashboard proxy.
   - Unggah vault ke OpenViking: `pixi run ingest`.
   - Uji validasi retriever: `pixi run spike`.
   - Ubah di `.env`: `LUCO_BACKEND=viking`, lalu jalankan server: `pixi run serve`.

---

## 🛡️ Status Verifikasi Sistem

- ✅ **Teruji 100% Otomatis (`pytest`):** **78 passed in ~5.2s** (100% lulus bersih tanpa warning pada 13 modul pengujian).
  - **Penalaran Agen & Guardrail (`test_agent.py` & `test_clarifications.py`):** Eksekusi alur kerja `FunctionAgent` LlamaIndex otentik, protokol klarifikasi aktif (*active clarification*) kueri ambigu, pertahanan injeksi prompt (*prompt injection defense*), panduan antislop copywriting/human, dan proteksi format 4-backtick.
  - **Kontrak REST API & Autentikasi (`test_api_contract.py` & `test_auth.py`):** Validasi endpoint `/v1/chat/completions`, login & callback Google OAuth, detail dokumen vault (fuzzy & exact), shared session, ekspor markdown, message feedback, otentikasi JWT, password hashing bcrypt, dan CORS middleware.
  - **Ketahanan LLM & Failover Streaming (`test_llm_resilience.py`):** Resilient transport HTTP, intersepsi anomali streaming Bifrost 500 SSE, dan mekanisme automatic failover `MultiProviderLLM` (Primary Antigravity Proxy + Fallback Bifrost Gateway).
  - **Akurasi Data Dosen & Resolusi Gelar (`test_lookup.py`):** Akses deterministik 33 profil dosen, pencarian exact nama, normalisasi gelar/honorifik, validasi NIP 18-digit, surel, KBK, dan OpenAlex ID bebas halusinasi.
  - **Integritas Vault & Grounding Sitasi (`test_core.py`):** Generator tree manifest heading (`manifest.json`), integritas tautan relatif vault, pencegahan path traversal, dan verifikasi sitasi tiga lapis (`citations.py`).
  - **Rate Limiting & Anti-Ban Kampus (`test_ratelimit.py`):** Identity-first sliding window (RPM/TPM) berbasis User ID JWT untuk mencegah *collateral IP ban* pada jaringan CGNAT/WiFi kampus, batas login per akun, dan pembersihan otomatis bucket RAM (*auto-eviction* 5 menit).
  - **Manajemen Sesi & Database (`test_sessions_and_db.py`):** Penegakan aturan tunggal *single active session per user* dengan pengarsipan otomatis di PostgreSQL 16 dan penanganan error UUID safe fallback (anti HTTP 500).
  - **Intersepsi Upfront Router (`test_router.py`):** Klasifikasi kueri deterministik 0 ms & 0 token untuk fast-reject kueri *out-of-scope* dan pengalihan kontak resmi sekretariat prodi.
  - **Integrasi Live OpenViking & Hybrid Backend (`test_viking_live.py` & `test_backends.py`):** Validasi endpoint live health OpenViking (:1933), navigasi `ls` vault, normalisasi query `find`, pembacaan dokumen `read`, serta fallback offline `LocalBackend` dengan *title & stopword boosting*.
  - **Audit Logging & Telemetri Biaya (`test_monitoring.py`):** Pencatatan audit trail real-time, token count (cl100k_base), kalkulasi estimasi biaya USD/IDR, dan antarmuka CLI dashboard monitor.
- ✅ **Terverifikasi Live Lapangan (*Live Spike* & *Ingest*):**
  - **Embedding Mikroservice IndoBERT:** Menggunakan `indobenchmark/indobert-base-p1` (port `:8001`) yang terbukti unggul dengan Top-1 Accuracy 80% dan margin separasi +0,2657 tanpa keruntuhan representasi.
  - **Indeks OpenViking DB:** Seluruh 10 direktori dan 104 dokumen vault terindeks penuh (470+ chunk) pada container `luco-openviking` (:1933).
  - **OpenViking Semantic Retrieval:** `pixi run spike` sukses menghasilkan skor kesamaan vektor 0.76–0.84 tanpa hambatan.
- 🔄 **Langkah Evaluasi & Pengujian Lanjutan:**
  - Akun Google telah terhubung aktif pada dashboard proxy Antigravity (`http://localhost:3000`).
  - Evaluasi tolok ukur: `pixi run eval -- --judge`.
  - Benchmark komparasi mode & embedding: `pixi run benchmark-modes` dan `pixi run benchmark-bert`.
