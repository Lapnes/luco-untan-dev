# CURRENT_STATE.md — Status Terkini Sistem Luco

**Terakhir Diperbarui:** 14 November 2026  
**Proyek:** Luco 🐦 (Chatbot Asisten Informasi Prodi Informatika UNTAN)  
**Tujuan:** Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan 2026  
**Tim Pengembang:** Ragil Amirzaky, Andrean Stephanus, Aji Prasetya  

---

## 1. Ringkasan Eksekutif

Sistem Luco saat ini berada dalam kondisi **Stabil, Ramping (Anti-Bloat), dan Siap Integrasi Data**. Seluruh arsitektur telah melalui proses peninjauan mendalam (*grill-me* & *quality audit*) untuk membersihkan fitur berlebih (*over-engineered*) dan menyelaraskannya dengan batasan tugas besar akademik.

### Indikator Kunci Kesiapan
- **Unit & Live Integration Test Suite Otentik:** `78 passed in ~5.0s` (100% tes lolos bersih dengan 0 error/failure di 13 modul pengujian; mencakup tes kontrak API, umpan balik pesan, Google OAuth redirect/callback, 4 tes integrasi live kontainer OpenViking :1933, pengujian otentik alur `FunctionAgent` LlamaIndex, failover streaming multi-provider, validasi generator JSON Tree Manifest, normalisasi lookup dosen, alur chat sesi aktif & arsip, dan isolasi identitas rate limiter).
- **Aplikasi Web Interaktif & Google OAuth 2.0:** Frontend SPA modern berbasis React + Vite + Tailwind (desain shadcn/ui) di `frontend/`, terintegrasi dengan Google OAuth 2.0 Client ID untuk login mahasiswa & dosen saat beta testing. Menyediakan antarmuka percakapan interaktif (markdown, rujukan sitasi, drawer penalaran agen) dan Dashboard Pemantauan & Audit real-time. Port 5173 untuk mode development dan otomatis di-mount pada port 8000 untuk produksi.
- **Arsitektur Memori:** Menerapkan paradigma **"Single Active Session with Archiving"** (1 pengguna = tepat 1 sesi aktif di PostgreSQL, tanpa sliding-window vector bloat atau cross-session injection).
- **Perlindungan Beban Produksi (Rate Limiting):** Menggunakan **Identity-First Limiting** berbasis `user_id` dan `email`, **bukan IP**. Dilengkapi auto-eviction bucket non-aktif berkala untuk mencegah kebocoran memori jangka panjang.
- **Retriever & Knowledge:** Hybrid Agentic RAG menggunakan **LlamaIndex FunctionAgent** yang terhubung ke **OpenViking** (pencarian semantik terstandarisasi dengan output normalisasi `uri`, `score`, dan `snippet`), **vault/manifest.json** (JSON Tree Manifest pemetaan hirarki heading & nomor baris sesuai Lembar Konsultasi), dan **vault/lookup.json** (pencarian deterministik data pasti seperti NIP dan email dosen).
- **Multi-Provider LLM & Resilient Transport:** Arsitektur Primary (`Antigravity Proxy` di :3000) dan Fallback otomatis (`Bifrost Gateway`). Dilengkapi generator streaming tangguh (`_resilient_stream`) yang mencegat kegagalan chunk upstream (seperti 403 Access Denied, 404, atau 500) dan mengalihkan ke provider cadangan tanpa memutuskan koneksi pengguna.
- **Klarifikasi Aktif (Active Clarification):** System prompt menegakkan klarifikasi aktif saat mahasiswa bertanya ambigu (misalnya "ingin bimbingan dengan dosen X", menyodorkan 4 jalur: TA, KP, PA, atau Lomba/Riset).
- **Docker & Proxy Stack:** Seluruh 4 container (`luco-postgres`, `luco-openviking`, `luco-antigravity-proxy`, `luco-indobert`) berjalan sehat (`healthy`). Konfigurasi OpenViking menerapkan `auth_mode: trusted` dengan dense embedding IndoBERT (`indobenchmark/indobert-base-p1`, 768-dim). Antigravity Proxy telah diperbaiki penanganan tool calling-nya (pencocokan nama fungsi otomatis dari pesan sebelumnya, sanitasi ID panggilan, dan propagasi `thoughtSignature`).

---

## 2. Matriks Status Komponen

| Komponen | File Utama | Status | Catatan Teknis |
| :--- | :--- | :--- | :--- |
| **Upfront Router (Step 1)** | [`src/luco/router.py`](file:///home/luco/luco-untan/src/luco/router.py) | ✅ **Selesai & Teruji** | Menangani klasifikasi instan (0 RAG calls) untuk saran/kritik/kontak resmi serta memilah `IN_SCOPE` vs `OUT_OF_SCOPE` dengan konteks 4–6 pesan terakhir. |
| **Agentic RAG Runtime (Step 2)** | [`src/luco/agent.py`](file:///home/luco/luco-untan/src/luco/agent.py) | ✅ **Selesai & Teruji** | LlamaIndex `FunctionAgent` dengan 4 tool inti. Membatasi riwayat pesan maksimal 6 pesan terakhir untuk efisiensi context window LLM. |
| **Core Tool Registry** | [`src/luco/tools.py`](file:///home/luco/luco-untan/src/luco/tools.py) | ✅ **Selesai** | Tersedia 4 alat: `cari_profil_dosen`, `telusuri_direktori_prodi`, `baca_dokumen_lengkap`, dan `list_docs`. Tool `search_past_chats` telah dihapus. |
| **Pengecek Sitasi** | [`src/luco/citations.py`](file:///home/luco/luco-untan/src/luco/citations.py) | ✅ **Selesai & Teruji** | Memverifikasi bahwa setiap tautan markdown di jawaban benar-benar muncul di output tool (groundedness). Gambar markdown `![alt](url)` diabaikan agar tidak dianggap sitasi salah. |
| **Lookup Deterministik** | [`src/luco/lookup.py`](file:///home/luco/luco-untan/src/luco/lookup.py) | ✅ **Selesai & Teruji** | Pencarian data dosen dari `vault/lookup.json` dengan normalisasi gelar akademik (`Dr.`, `Prof.`, `Ir.`, `Pak`). |
| **Database & Sesi Aktif** | [`src/luco/db.py`](file:///home/luco/luco-untan/src/luco/db.py)<br>[`src/luco/schema.sql`](file:///home/luco/luco-untan/src/luco/schema.sql) | ✅ **Selesai & Teruji** | PostgreSQL 16 asyncpg. Menegakkan partial unique index `idx_one_active_session_per_user`. Menyediakan fungsi clear chat, switch session, dan append-only messages. |
| **Knowledge Backends** | [`src/luco/backends.py`](file:///home/luco/luco-untan/src/luco/backends.py) | ✅ **Selesai & Teruji** | Mendukung OpenViking (HTTP SDK) dan LocalBackend. Output `find()` dinormalisasi seragam (`uri`, `score`, `snippet`) dan path URI diselaraskan. Teruji live di port :1933. |
| **Manifest Heading Generator** | [`scripts/build_manifest.py`](file:///home/luco/luco-untan/scripts/build_manifest.py)<br>[`vault/manifest.json`](file:///home/luco/luco-untan/vault/manifest.json) | ✅ **Selesai & Teruji** | Menghasilkan JSON Tree Manifest yang memetakan hirarki heading dokumen vault beserta nomor baris awal/akhirnya pada fase build-time sesuai Lembar Konsultasi. |
| **Rate Limiter & Token Budget** | [`src/luco/ratelimit.py`](file:///home/luco/luco-untan/src/luco/ratelimit.py) | ✅ **Selesai & Teruji** | Pembatasan laju berbasis identitas (RPM, TPM, TPD) dengan pre-flight token check menggunakan `tiktoken`. Dilengkapi pembersihan bucket tidak aktif berkala (5 menit) untuk stabilitas memori. Anti ban IP. |
| **Autentikasi & Keamanan** | [`src/luco/auth.py`](file:///home/luco/luco-untan/src/luco/auth.py) | ✅ **Selesai & Teruji** | JWT Bearer (access token 2 jam, refresh token 7 hari). Password hashing dengan bcrypt. Fallback generator rahasia acak 32-byte jika `.env` belum diatur. |
| **FastAPI REST Endpoints** | [`src/luco/api.py`](file:///home/luco/luco-untan/src/luco/api.py) | ✅ **Selesai & Teruji** | Dilengkapi CORS middleware, endpoint sesi aktif (`/v1/session/active`, `/v1/chat`, `/v1/session/clear`, `/v1/session/{id}/switch`), dan endpoint `/v1/chat/completions` (OpenAI format). |
| **Audit & Monitoring** | [`src/luco/monitoring.py`](file:///home/luco/luco-untan/src/luco/monitoring.py) | ✅ **Selesai & Teruji** | Menghitung token input/output, latensi, estimasi biaya USD & IDR (kurs dinamis), penulisan file JSONL asinkron tanpa memblokir event loop. |
| **Knowledge Vault** | [`vault/`](file:///home/luco/luco-untan/vault/) | ✅ **Selesai Diisi & Terorganisir** | Basis pengetahuan 6 kategori modular (`profil`, `akademik`, `kp-ta`, `dosen`, `fasilitas-lab`, `kemahasiswaan`). Memuat 33 profil dosen terpadu per subfolder KBK dengan metrik riset OpenAlex (sitasi & h-index), Kurikulum 2026 (140 SKS) & 2016 (144 SKS). Tervalidasi 0 tautan rusak via `check-links` dan 33 dosen terdaftar di `lookup.json`. |
| **Crawler OpenAlex** | [`scripts/crawl_openalex.py`](file:///home/luco/luco-untan/scripts/crawl_openalex.py) | ✅ **Selesai** | Crawler berbasis Python (httpx) untuk mengambil publikasi dosen ke folder staging `crawl-output/`. Versi duplikat Go telah dihapus. |
| **Evaluasi & Benchmark** | [`eval/run_eval.py`](file:///home/luco/luco-untan/eval/run_eval.py) | ✅ **Siap Dijalankan** | Dataset `questions.jsonl` (10 pertanyaan benchmark). Skrip evaluasi mendukung LLM-as-a-judge dan perbandingan performa vs baseline tanpa RAG. |
| **Container & Orchestrator** | [`docker-compose.yml`](file:///home/luco/luco-untan/docker-compose.yml)<br>[`Dockerfile`](file:///home/luco/luco-untan/Dockerfile) | ✅ **Selesai** | Multi-stage Dockerfile berbasis Pixi, docker-compose orchestrator mengintegrasikan `luco-app`, `postgres`, `openviking`, dan `antigravity-proxy`. |

---

## 3. Yang Sudah Teruji vs Perlu Uji Lapangan (Live Spike)

### A. Sudah Teruji Penuh Secara Otomatis (`pytest`)
1. **Logika Router:** Heuristik saran/kerjasama langsung memicu penolakan sopan (0 ms latency). Router fallback berjalan mulus tanpa LLM.
2. **Pencarian Data Dosen:** Lookup NIP tepat, toleran terhadap variasi penulisan gelar akademis seperti *"Dr. Budi"* maupun *"Pak Budi"*.
3. **Pengecekan Sitasi:** Algoritma mencocokkan tautan markdown terhadap output tool dan mengabaikan gambar.
4. **Keamanan Sesi & UUID:** Penanganan UUID cacat atau tidak valid selalu mengembalikan `404 Not Found` atau fallback aman tanpa menyebabkan server crash (500).
5. **Siklus Sesi Aktif:** Endpoint `/v1/session/active`, `/v1/session/clear`, dan switch sesi berjalan sesuai kontrak.
6. **Rate Limiting & Token Budget:** Tes simulasi RPM melampaui batas mengembalikan HTTP 429 dengan header `Retry-After`. Tes pembuktian anti-ban IP menunjukkan 2 user di IP yang sama tetap terisolasi.
7. **Keamanan Token & CORS:** Endpoint yang diproteksi menolak request tanpa token atau token rusak. Header CORS merespons origin client dengan benar.

### B. Terverifikasi Live Lapangan (Live Spike & Production Stack)
1. **Embedding Vektor IndoBERT & Ingest (`pixi run ingest`):** Microservice `luco-indobert` (`indobenchmark/indobert-base-p1`, 768 dimensi) terintegrasi via endpoint OpenAI-compatible (`http://indobert:8001/v1`). Seluruh 65 berkas vault terproses sempurna menghasilkan 463 chunks teks ter-embed ke `viking://resources/luco` tanpa error, sepenuhnya menggantikan model default Mandarin BGE lama sesuai proposal Lembar Konsultasi.
2. **Retrieval Semantik Vektor (`pixi run spike`):** Teruji live langsung dari OpenViking dengan hasil ternormalisasi. Pertanyaan akademik ("Apa saja syarat mengajukan proposal TA/skripsi?") langsung tepat sasaran mencocokkan dokumen `kp-ta/panduan-ta/` dan `kp-ta/README/`.
3. **Multi-Provider LLM & Resilient Transport:** Primary terhubung ke `http://127.0.0.1:3000/v1` (Antigravity Proxy) dan otomatis failover ke `https://bifrost.tenzly.pro/v1` (Bifrost Gateway) jika proxy belum login. `ResilientBifrostTransport` mencegat error unmarshal HTTP 500 Bifrost secara transparan via SSE stream.
4. **Active Clarification (Grill-Me Intent):** Agen tidak lagi berasumsi liar saat menerima pertanyaan ambigu (misal "cara bimbingan pak X"), melainkan langsung menanyakan jalur spesifik (TA, KP, PA, atau Lomba).

---

## 4. Batasan & Lingkup yang Disepakati (Sesuai AGENTS.md)

Demi menjaga fokus dan penyelesaian tepat waktu untuk Tugas Besar UAS AI 2026, fitur-fitur berikut **secara sengaja tidak dibuat** dan akan dicantumkan pada Bab Saran Pengembangan di laporan akhir:
- Sistem otorisasi bertingkat (RBAC) atau admin role matrix yang rumit.
- Redis cluster terdistribusi (digantikan dengan in-memory sliding window + async PostgreSQL).
- Knowledge Graph (GraphRAG / Neo4j / Qdrant).
- Fitur input suara / speech-to-text (Whisper).
- Multi-session drag-and-drop context injection.

---

## 5. Rencana Aksi Segera (Next Steps)

2. **Laporan Pengujian Menyeluruh & Komparasi Embedding (`docs/laporan/`):**
   - ✅ **Struktur Laporan Tersedia:** Subfolder `docs/laporan/raw/` (data mentah eksekusi) dan `docs/laporan/final/` (laporan terstruktur untuk presentasi dosen).
   - ✅ **Hasil Benchmark Embedding Vektor:** `indobenchmark/indobert-base-p1` mencatat **Top-1 Accuracy 80%**, **Top-3 Recall 100%**, dan margin separasi **+0,2657** (unggul 7x lipat atas `indolem/indobert-base-uncased` yang mengalami *representation collapse* dengan margin hanya +0,0373). Dokumen laporan: [`perbandingan_embedding_indobert.md`](file:///home/luco/luco-untan/docs/laporan/final/perbandingan_embedding_indobert.md).
   - ✅ **Laporan Pengujian Menyeluruh:** Dokumentasi lengkap 78/78 passing automated tests (13 modul pengujian), OpenViking live retrieval, router fast reject, dan PostgreSQL active session: [`laporan_pengujian_keseluruhan_aplikasi.md`](file:///home/luco/luco-untan/docs/laporan/final/laporan_pengujian_keseluruhan_aplikasi.md).
3. **Status Autentikasi Akun Google di Antigravity Proxy:**
   - ✅ **Telah Terhubung & Terverifikasi:** Akun aktif (`tenutyquwil1@gmail.com`) pada dasbor `http://localhost:3000`.
   - Tool calling dan completions via `gemini-2.5-flash-lite` dan model lainnya berjalan dengan ketersediaan (health) 100%.

