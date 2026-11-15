# Panduan Lengkap Arsitektur & Analisis Sistem Luco (luco-untan)

Dokumen ini disusun sebagai bahan komprehensif untuk memahami seluruh isi proyek, arsitektur, alur kerja komponen cerdas, dan penjelasan berkas pada sistem **Luco 🐦**.

---

## 📌 Daftar Isi
1. [Ringkasan Proyek & Tujuan Akademik](#1-ringkasan-proyek--tujuan-akademik)
2. [Arsitektur Sistem & Diagram Alir](#2-arsitektur-sistem--diagram-alir)
3. [Bedah Komponen Cerdas Utama](#3-bedah-komponen-cerdas-utama)
   - [A. Pengelolaan RAG (Retrieval-Augmented Generation)](#a-pengelolaan-rag-retrieval-augmented-generation)
   - [B. Pengelolaan Embedding & Vektor](#b-pengelolaan-embedding--vektor)
   - [C. Pengelolaan Model IndoBERT](#c-pengelolaan-model-indobert)
   - [D. Pengelolaan Routing Model (Dual-LLM & Provider Failover)](#d-pengelolaan-routing-model-dual-llm--provider-failover)
4. [Penjelasan Rinci Seluruh Berkas di `src/luco/`](#4-penjelasan-rinci-seluruh-berkas-di-srcluco)
5. [Penjelasan Folder & Berkas Lainnya (di luar Frontend)](#5-penjelasan-folder--berkas-lainnya-di-luar-frontend)
6. [Struktur Direktori Proyek (Tree View)](#6-struktur-direktori-proyek-tree-view)

---

## 1. Ringkasan Proyek & Tujuan Akademik

* **Nama Proyek:** Luco 🐦 (`luco-untan`)
* **Peruntukan:** Chatbot Asisten Informasi Program Studi Informatika, Fakultas Teknik, Universitas Tanjungpura (UNTAN).
* **Konteks:** Tugas Besar Pengganti Ujian Akhir Semester (UAS) Mata Kuliah Kecerdasan Buatan 2026.
* **Tim Pengembang:** Ragil Amirzaky, Andrean Stephanus, Aji Prasetya.
* **Tujuan Utama:** Membangun asisten AI kampus yang ramah dan cepat, namun **bebas halusinasi** terhadap data-data kritis (NIP dosen, surel resmi, kurikulum 140 SKS, alur KP/TA, dan CPL) menggunakan perpaduan pencarian semantik vektor dan pencarian deterministik terstruktur.

---

## 2. Arsitektur Sistem & Diagram Alir

Sistem menerapkan paradigma **Hybrid Agentic RAG**:

```
[ Pengguna / Client ]
         │ (HTTP / WebSocket)
         ▼
[ FastAPI Server: src/luco/api.py ]
         │ (JWT Auth & Identity-based Rate Limiter)
         ▼
[ Step 1: Upfront Router (src/luco/router.py) ] ──► OUT_OF_SCOPE / CONTACT_REDIRECT (Fast Reject 0 ms)
         │ (Jika IN_SCOPE)
         ▼
[ Step 2: LlamaIndex FunctionAgent (src/luco/agent.py) ]
         │
         ├──► cari_profil_dosen ──────► vault/lookup.json (Data Pasti NIP/Email tanpa LLM Hallucination)
         ├──► telusuri_direktori_prodi ─► VikingBackend (openviking-sdk :1933)
         │                                       │
         │                                       ▼
         │                               IndoBERT Embedder (:8001)
         │                               (indobenchmark/indobert-base-p1: 768-dim)
         ├──► baca_dokumen_lengkap ───► Baca teks Markdown (dibatasi MAX_READ_CHARS = 12000)
         └──► list_docs ──────────────► Daftar isi direktori vault
         │
         ▼
[ Citations Verifier: src/luco/citations.py ] ──► Validasi Groundedness Tautan Sumber
         │
         ▼
[ Database PostgreSQL 16: src/luco/db.py ] ──► Single Active Session & Token Audit Logs
```

---

## 3. Bedah Komponen Cerdas Utama

### A. Pengelolaan RAG (Retrieval-Augmented Generation)

Pengelolaan RAG terletak pada kolaborasi antara **Agentic Loop**, **Tools**, dan **Knowledge Backends**:

1. **Orkestrator Agen (`src/luco/agent.py`):**
   * Menggunakan `FunctionAgent` dari LlamaIndex (`llama_index.core.agent.workflow`).
   * Membatasi riwayat obrolan maksimal 6 pesan terakhir (`recent_history = history[-6:]`) agar *context window* LLM tidak membengkak dan respon tetap fokus.
   * Mengatur 3 mode inferensi:
     * `viking_indobert`: Mode default lengkap dengan penalaran iteratif agen (*multi-step tool call*).
     * `viking_fast`: Mode *one-shot direct retrieval*, memanggil `backend.find()` sekali dan langsung menyintesis jawaban dalam satu panggilan LLM.
     * `direct_llm`: Mode tanya-jawab langsung tanpa penelusuran dokumen (tetap melewati saringan Router).

2. **Pendaftaran Alat / Tools (`src/luco/tools.py`):**
   * Mengonversi fungsi-fungsi Python menjadi `FunctionTool` LlamaIndex:
     * `cari_profil_dosen`: Menghubungkan ke `lookup.py`.
     * `telusuri_direktori_prodi`: Menghubungkan ke fungsi `find()` backend.
     * `baca_dokumen_lengkap`: Menghubungkan ke fungsi `read()` backend dengan pemotongan teks jika melebihi 12.000 karakter (`MAX_READ_CHARS`).
     * `list_docs`: Menghubungkan ke fungsi `ls()` backend untuk melihat struktur indeks folder.
   * Dilengkapi kelas `Recorder` yang merekam semua argumen input dan teks output setiap tool untuk verifikasi sitasi dan audit jejak (*trajectory*).

3. **Backend Abstraction (`src/luco/backends.py`):**
   * Mendefinisikan antarmuka `Backend(Protocol)` seragam: `find(query, limit)`, `read(uri)`, dan `ls(uri)`.
   * `VikingBackend`: Menghubungkan aplikasi ke server OpenViking (port 1933). Menormalisasi hasil pencarian mentah engine menjadi daftar objek terstruktur: `[{"uri": ..., "score": ..., "snippet": ...}]`.
   * `LocalBackend`: Mekanisme pencarian cadangan berbasis pencocokan kata kunci lokal dan *caching mtime* dokumen Markdown di `vault/` jika container OpenViking offline.

4. **Pencarian Deterministik (`src/luco/lookup.py`):**
   * Komponen pelengkap RAG untuk mengatasi kelemahan model vektor pada string presisi (seperti 18 digit NIP atau alamat surel).
   * Membaca `vault/lookup.json` ke dalam memori dan menormalisasi sapaan/gelar akademik (`Dr.`, `Prof.`, `Ir.`, `S.Kom.`, `M.Cs.`, `Pak`, `Ibu`) sehingga pencarian nama fleksibel dan akurat 100%.

5. **Pengecekan Sitasi (`src/luco/citations.py`):**
   * Mengekstrak tautan markdown `[Nama Dokumen](uri)` pada jawaban LLM menggunakan regex dengan *negative lookbehind* `(?<!!)\[([^\]]+)\]\(([^)\s]+)\)` agar tautan gambar markdown `![alt](url)` tidak dianggap sitasi.
   * Mencocokkan tautan tersebut dengan output yang benar-benar dikembalikan oleh tool. Jika LLM mencantumkan tautan fiktif yang tidak pernah dibaca, sitasi akan ditandai `unverified`.

---

### B. Pengelolaan Embedding & Vektor

1. **Konfigurasi Embedding Server:**
   * Terletak pada file [`ov.conf`](file:///home/luco/luco-untan/ov.conf).
   * Mengatur engine OpenViking untuk menggunakan model embedding kustom melalui antarmuka OpenAI-compatible:
     ```json
     "embedding": {
       "dense": {
         "provider": "openai",
         "model": "indobenchmark/indobert-base-p1",
         "api_base": "http://indobert:8001/v1",
         "api_key": "none",
         "dimension": 768
       }
     }
     ```
2. **Proses Ingesti Dokumen (`scripts/ingest.py`):**
   * Memindai seluruh direktori `vault/` (104 berkas Markdown dalam 7 kategori semantik, termasuk 26 berkas formulir & pedoman resmi Directus).
   * Membagi berkas menjadi potongan teks (*chunks*) logis.
   * Mengirim chunk ke OpenViking, yang kemudian memanggil endpoint embedding IndoBERT untuk menghasilkan representasi dense vektor 768 dimensi dan menyimpannya di workspace `viking://resources/luco`.

---

### C. Pengelolaan Model IndoBERT

Model BERT dikelola sebagai microservice terisolasi di dalam container Docker:

1. **Kode Microservice IndoBERT:**
   * Terletak di [`dependencies/indobert-embedder/app.py`](file:///home/luco/luco-untan/dependencies/indobert-embedder/app.py).
   * Dibangun menggunakan **FastAPI**, **PyTorch**, dan pustaka **Hugging Face Transformers**.
   * Model yang digunakan: `indobenchmark/indobert-base-p1`.
   * Arsitektur Pooling: Menerapkan fungsi `mean_pooling` pada token representasi lapisan terakhir dengan memperhitungkan `attention_mask` untuk mereduksi output menjadi 1 vektor kalimat berdimensi 768:
     ```python
     def mean_pooling(model_output, attention_mask):
         token_embeddings = model_output[0]
         input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
         sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
         sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
         return sum_embeddings / sum_mask
     ```
   * Endpoint yang disediakan:
     * `POST /v1/embeddings`: Menerima input teks tunggal atau list teks dan mengembalikan JSON berformat OpenAI embedding.
     * `GET /health`: Memeriksa status kesiapan model, perangkat komputasi (`cuda` atau `cpu`), dan dimensi output (768).
2. **Container & Penyimpanan Bobot:**
   * [`dependencies/indobert-embedder/Dockerfile`](file:///home/luco/luco-untan/dependencies/indobert-embedder/Dockerfile): Lingkungan container Python mandiri.
   * [`dependencies/indobert-cache/`](file:///home/luco/luco-untan/dependencies/indobert-cache/): Direktori cache persisten di host mesin agar bobot model dari Hugging Face Hub tidak diunduh ulang setiap container dinyalakan.

---

### D. Pengelolaan Routing Model (Dual-LLM & Provider Failover)

Routing model terbagi menjadi dua level:

#### 1. Level Semantik & Guardrail (Upfront Router di `src/luco/router.py`)
Sebagai langkah pertama (Step 1) dalam arsitektur Dual-LLM untuk memastikan keamanan dan efisiensi:
* **Heuristik Cepat (0 ms Latensi):**
  * `classify_heuristics()`: Mengecek kata kunci `PRODI_KEYWORDS` (misalnya: *skripsi, kp, ta, kurikulum, krs, spota*, dan nama-nama 33 dosen prodi) serta `CONVERSATIONAL_WORDS` (*halo, makasih, apa maksudmu*). Jika ditemukan, langsung diloloskan sebagai `IN_SCOPE`.
  * Mengecek kata kunci kontak resmi (*pengaduan, saran, kerjasama*). Jika bukan komplain terhadap bot, diarahkan ke `CONTACT_REDIRECT`.
* **Klasifikasi LLM Terfokus:**
  * Jika heuristik tidak yakin, sistem mengeksekusi `classify_query()` dengan menyertakan ringkasan percakapan sebelumnya.
  * Menggunakan [`ROUTER_PROMPT`](file:///home/luco/luco-untan/src/luco/prompts.py) yang memaksa LLM mengembalikan format JSON tunggal:
    `{"category": "IN_SCOPE" | "OUT_OF_SCOPE" | "CONTACT_REDIRECT", "reason": "..."}`
  * Jika bernilai `OUT_OF_SCOPE` atau `CONTACT_REDIRECT`, permintaan langsung dijawab dengan pesan penolakan sopan tanpa menyentuh database vektor OpenViking (menghemat komputasi dan biaya).

#### 2. Level Infrastruktur & Resiliensi (Multi-Provider di `src/luco/llm.py`)
Menjamin ketersediaan layanan inferensi LLM:
* **`MultiProviderLLM`:**
  * Membungkus dua instans LLM: **Primary Provider** (Antigravity Proxy di `http://127.0.0.1:3000/v1` yang mengakses Google Gemini) dan **Fallback Provider** (Bifrost Gateway).
  * Method `achat()` dan `astream_chat()` secara otomatis mengalihkan permintaan ke provider cadangan jika provider utama mengalami kegagalan (HTTP 403, 404, 500, atau koneksi terputus).
* **`ResilientBifrostTransport`:**
  * Transport asinkron khusus berbasis `httpx.AsyncHTTPTransport` yang menangani kesalahan *unmarshal* 500 jika gateway upstream mengirimkan format stream Server-Sent Events (SSE) saat dipanggil dalam mode non-streaming. Transport ini otomatis merakit ulang potongan event menjadi objek JSON chat completion yang utuh.

---

## 4. Penjelasan Rinci Seluruh Berkas di `src/luco/`

Berikut adalah rincian lengkap tugas dan mekanisme dari ke-18 berkas di dalam paket `src/luco/`:

### 1. [`__init__.py`](file:///home/luco/luco-untan/src/luco/__init__.py)
* **Fungsi:** Menandai direktori `src/luco` sebagai modul Python.
* **Isi:** Menyediakan metadata dasar paket Luco.

### 2. [`agent.py`](file:///home/luco/luco-untan/src/luco/agent.py)
* **Fungsi:** Orkestrator utama siklus percakapan dan agen penalaran.
* **Mekanisme Utama:**
  * Mengelola kelas `Luco` dengan method utama `ask()`.
  * Memotong riwayat pesan menjadi maksimal 6 pesan terakhir (`history[-6:]`).
  * Mengeksekusi Step 1: Upfront Router (`classify_query`).
  * Mengeksekusi Step 2: Deteksi Klarifikasi Aktif (`detect_clarification`).
  * Mengeksekusi Step 3: Memilih mode inferensi (`direct_llm`, `viking_fast`, atau `viking_indobert`).
  * Menjalankan LlamaIndex `FunctionAgent` dengan batasan iterasi (`max_steps`).
  * Memvalidasi sitasi output dan mencatat log trajectory serta audit token.

### 3. [`api.py`](file:///home/luco/luco-untan/src/luco/api.py)
* **Fungsi:** Server backend web REST API berbasis framework FastAPI.
* **Mekanisme Utama:**
  * Mengatur middleware CORS untuk komunikasi dengan frontend.
  * Menyediakan endpoint autentikasi (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/google/login`, `/auth/google/callback`).
  * Mengatur siklus sesi aktif tunggal (`/v1/session/active`, `/v1/session/clear`, `/v1/session/{id}/switch`, `/v1/session/{id}/archive`).
  * Menyediakan endpoint chat interaktif (`/v1/chat`) dan endpoint yang kompatibel dengan format OpenAI API (`/v1/chat/completions`).
  * Menyediakan endpoint pemantauan kesehatan sistem (`/health`).

### 4. [`auth.py`](file:///home/luco/luco-untan/src/luco/auth.py)
* **Fungsi:** Modul otentikasi, enkripsi, dan tokenisasi keamanan.
* **Mekanisme Utama:**
  * `hash_password()` & `verify_password()`: Enkripsi dan verifikasi password menggunakan pustaka `bcrypt`.
  * `create_access_token()`: Menghasilkan token JWT dengan masa aktif 2 jam.
  * `create_refresh_token()`: Menghasilkan refresh token JWT dengan masa aktif 7 hari.
  * `decode_token()`: Membaca dan memvalidasi payload token JWT.
  * Otomatis membuat kunci acak 32-byte aman jika `JWT_SECRET` belum didefinisikan di lingkungan.

### 5. [`backends.py`](file:///home/luco/luco-untan/src/luco/backends.py)
* **Fungsi:** Layer penghubung ke repositori dokumen dan mesin pencari.
* **Mekanisme Utama:**
  * Protokol antarmuka `Backend` dengan fungsi `find()`, `read()`, dan `ls()`.
  * `VikingBackend`: Menggunakan `SyncHTTPClient` dari `openviking-sdk` untuk mengambil vektor dari OpenViking, menormalisasi path URI, dan mengembalikan skor relevansi serta cuplikan snippet.
  * `LocalBackend`: Implementasi pencarian teks lokal berbasis frekuensi kata kunci (TF-like) dan bobot judul untuk keperluan cadangan offline.
  * Fungsi pengaman `_safe_rel()` untuk mencegah serangan *directory traversal* keluar dari root vault.

### 6. [`citations.py`](file:///home/luco/luco-untan/src/luco/citations.py)
* **Fungsi:** Pemeriksa keabsahan sumber rujukan (*grounding*) jawaban agen.
* **Mekanisme Utama:**
  * `extract_links()`: Mengekstrak tautan format Markdown `[teks](target)`.
  * Menerapkan regex khusus untuk mengecualikan gambar markdown `![alt](url)`.
  * `check_citations()`: Membandingkan semua tautan dokumen pada jawaban LLM dengan kumpulan URI atau URL yang benar-benar ada di output tool eksekusi. Menghasilkan status `all_verified: True/False`.

### 7. [`clarifications.py`](file:///home/luco/luco-untan/src/luco/clarifications.py)
* **Fungsi:** Sistem wawancara aktif (*active interview / grill-me*) untuk pertanyaan ambigu.
* **Mekanisme Utama:**
  * Mendefinisikan preset ambiguitas `CLARIFICATION_PRESETS` (topik bimbingan, syarat ujian, legalisir, pengajuan judul).
  * `detect_clarification()`: Jika pengguna menanyakan hal yang konteksnya bercabang (seperti "ingin bimbingan"), agen tidak berasumsi sepihak, melainkan menyajikan 4 pilihan jalur: Tugas Akhir (TA), Kerja Praktik (KP), Pembimbing Akademik (PA), atau Lomba/Riset.

### 8. [`cli.py`](file:///home/luco/luco-untan/src/luco/cli.py)
* **Fungsi:** Antarmuka baris perintah interaktif (Terminal REPL).
* **Mekanisme Utama:**
  * Dijalankan melalui `pixi run chat`.
  * Menangani loop input-output obrolan pengguna di terminal.
  * Menampilkan format teks berwarna ANSI, durasi latensi eksekusi, rincian sitasi dokumen yang terverifikasi, dan opsi pencetakan jejak *trajectory*.

### 9. [`config.py`](file:///home/luco/luco-untan/src/luco/config.py)
* **Fungsi:** Pusat manajemen konfigurasi aplikasi.
* **Mekanisme Utama:**
  * Membaca dan memvalidasi variabel lingkungan dari berkas `.env` menggunakan `dataclass Settings`.
  * Mengatur URL database PostgreSQL, URL OpenViking, API key LLM, direktori vault, ambang batas pembacaan dokumen, dan batasan token.
  * Menggunakan dekorator `@lru_cache` pada fungsi `get_settings()` agar konfigurasi hanya dibaca sekali saat inisialisasi.

### 10. [`db.py`](file:///home/luco/luco-untan/src/luco/db.py)
* **Fungsi:** Manajemen koneksi dan operasi CRUD ke database PostgreSQL.
* **Mekanisme Utama:**
  * Mengelola *connection pool* asinkron menggunakan pustaka `asyncpg`.
  * Menegakkan arsitektur **Single Active Session with Archiving**: fungsi `get_or_create_active_session()`, `archive_all_active_sessions()`, dan `archive_session()`.
  * Menyimpan dan memuat pesan percakapan (`add_message()`, `get_session_messages()`).
  * Menyimpan catatan log audit token ke tabel `audit_logs`.

### 11. [`llm.py`](file:///home/luco/luco-untan/src/luco/llm.py)
* **Fungsi:** Pengendali adaptor LLM dan ketahanan koneksi (*resilience*).
* **Mekanisme Utama:**
  * Mengimplementasikan turunan `FunctionCallingLLM` dari LlamaIndex.
  * Kelas `MultiProviderLLM`: Mengatur alur failover otomatis antara Primary LLM (Antigravity Proxy port 3000) dan Fallback LLM (Bifrost Gateway).
  * Kelas `ResilientBifrostTransport`: Menangani parsing data streaming Server-Sent Events (SSE) saat gateway upstream mengalami kendala unmarshal HTTP 500.

### 12. [`lookup.py`](file:///home/luco/luco-untan/src/luco/lookup.py)
* **Fungsi:** Mesin pencari data dosen secara deterministik (anti-halusinasi).
* **Mekanisme Utama:**
  * Memuat basis data `vault/lookup.json` ke dalam memori aplikasi.
  * Fungsi `strip_titles()` dan `normalize_name()`: Menghilangkan gelar akademis (`Dr.`, `Prof.`, `Ir.`, `M.Kom.`, dll.) serta sapaan personal.
  * Fungsi `lookup_records()`: Melakukan pencarian bertingkat (pencocokan eksak, pencocokan substring nama, dan pencocokan token nama) untuk mengembalikan NIP, surel, jabatan, dan kelompok keahlian dosen secara akurat 100%.

### 13. [`monitoring.py`](file:///home/luco/luco-untan/src/luco/monitoring.py)
* **Fungsi:** Pelacakan konsumsi token terperinci, telemetri mikrofonis multi-fase, kalkulasi biaya, dan audit analitik.
* **Mekanisme Utama:**
  * Menghitung token menggunakan tokenizer resmi `tiktoken` (`cl100k_base`).
  * Memecah token ke dalam 3 tier akurat: `user_prompt_tokens` (kueri mahasiswa), `system_prompt_tokens` (persona sistem), dan `context_tokens` (data ekstraksi tool RAG).
  * Mencatat `timing_breakdown`: durasi router, total durasi tools beserta rincian per-tool, waktu inferensi akhir LLM, dan total latensi.
  * Menghitung estimasi biaya inferensi dalam USD dan IDR berdasarkan tarif token model.
  * Fungsi `record_audit_log()`: Menyimpan rekaman audit ke database PostgreSQL dan file JSONL `logs/audit.jsonl` menggunakan `asyncio.to_thread`.
  * Fungsi `get_audit_summary()`, `query_audit_logs()`, dan `export_audit_csv()` dengan dukungan filter rentang waktu (`start_time`, `end_time`) dan filter model.

### 14. [`prompts.py`](file:///home/luco/luco-untan/src/luco/prompts.py)
* **Fungsi:** Kumpulan prompt sistem dan panduan persona agen.
* **Mekanisme Utama:**
  * `SYSTEM_PROMPT`: Menetapkan persona Luco (ramah, kasual sopan khas mahasiswa Informatika UNTAN, menggunakan emoji burung 🐦), kewajiban menyertakan sitasi sumber Markdown resmi, aturan larangan keras mengarang NIP dosen, dan instruksi alur pemanggilan tool.
  * `ROUTER_PROMPT`: Template instruksi terstruktur untuk model router dalam mengklasifikasikan intent pertanyaan pengguna menjadi format JSON tunggal.

### 15. [`ratelimit.py`](file:///home/luco/luco-untan/src/luco/ratelimit.py)
* **Fungsi:** Sistem pembatasan laju (*rate limiter*) berbasis identitas pengguna.
* **Mekanisme Utama:**
  * **Anti IP-Ban Kampus:** Pembatasan kuota dilacak berdasarkan `user_id` atau `email` JWT pengguna, bukan IP publik (mencegah ribuan mahasiswa dalam satu WiFi kampus/CGNAT saling memblokir).
  * Menghitung batas kuota: RPM (*Requests per Minute*), TPM (*Tokens per Minute*), dan TPD (*Tokens per Day*).
  * Menggunakan *pre-flight token estimation* dengan `tiktoken`.
  * Dilengkapi background task *auto-eviction* berkala (setiap 5 menit) untuk membersihkan bucket pengguna yang tidak aktif guna mencegah kebocoran memori RAM.

### 16. [`router.py`](file:///home/luco/luco-untan/src/luco/router.py)
* **Fungsi:** Upfront Router (Dual-LLM Langkah 1) untuk pemilahan cakupan pertanyaan.
* **Mekanisme Utama:**
  * `classify_heuristics()`: Penyaringan kata kunci cepat (0 ms) dengan pencegahan *false positive*:
    * Daftar putih nama dosen dan pengembang prodi selalu diloloskan sebagai `IN_SCOPE`.
    * Pola regex `ADVICE_REQUEST_PATTERNS` & `ACADEMIC_COLLAB_PATTERNS` memastikan mahasiswa yang meminta saran akademik/topik riset kolaborasi tidak salah dialihkan ke kontak formal.
    * Pola regex `FORMAL_CONTACT_PATTERNS` mengarahkan pengaduan resmi fasilitas atau permohonan kerjasama kemitraan kampus ke `CONTACT_REDIRECT`.
  * `classify_query()`: Evaluasi intent menggunakan LLM jika heuristik tidak konklusif, dengan mempertimbangkan konteks percakapan sebelumnya untuk kata ganti atau pertanyaan bersambung.
  * Mengembalikan objek `RouteResult` yang berisi kategori (`IN_SCOPE`, `OUT_OF_SCOPE`, `CONTACT_REDIRECT`) dan pesan balasan instan.

### 17. [`schema.sql`](file:///home/luco/luco-untan/src/luco/schema.sql)
* **Fungsi:** Definisi DDL skema basis data relasional PostgreSQL.
* **Mekanisme Utama:**
  * Tabel `users`: Data identitas pengguna (ID UUID, email, password hash, provider Google OAuth).
  * Tabel `chat_sessions`: Riwayat sesi obrolan dengan penegakan indeks parsial unik `idx_one_active_session_per_user` (`WHERE is_active = TRUE`).
  * Tabel `chat_messages`: Rekaman riwayat pesan (role user/assistant, data tool calls, metadata sitasi, klarifikasi, kolom `feedback`, dan `feedback_at`).
  * Tabel `audit_logs`: Data analisis penggunaan token bertingkat (`user_prompt_tokens`, `system_prompt_tokens`, `context_tokens`), latensi multi-fase (`timing_breakdown`), relasi `message_id`, estimasi biaya, dan status feedback.

### 18. [`tools.py`](file:///home/luco/luco-untan/src/luco/tools.py)
* **Fungsi:** Definisi fungsi alat bantu (*tools*) yang diekspos ke LlamaIndex.
* **Mekanisme Utama:**
  * Mengemas fungsi `cari_profil_dosen`, `telusuri_direktori_prodi`, `baca_dokumen_lengkap`, dan `list_docs` ke dalam `FunctionTool`.
  * Membatasi karakter baca teks maksimal 12.000 karakter (`MAX_READ_CHARS`) untuk mencegah jebolnya context window LLM.
  * Menggunakan kelas `Recorder` yang secara otomatis mencatat nama alat, parameter input, durasi milidetik (`duration_ms`), daftar berkas yang diakses (`files_accessed`), baris/entri terbaca (`lines_accessed`), serta cuplikan aman untuk validasi sitasi dan pelacakan *trajectory*.

### 19. [`trajectory.py`](file:///home/luco/luco-untan/src/luco/trajectory.py)
* **Fungsi:** Pencatatan jejak langkah reasoning dan eksekusi tool.
* **Mekanisme Utama:**
  * Menyediakan fungsi `log_trajectory(path, record)`.
  * Menuliskan setiap interaksi ke berkas `logs/trajectory.jsonl` dalam format JSON Lines yang mencakup timestamp ISO, pertanyaan pengguna, langkah-langkah tool yang dipanggil, output masing-masing tool, hasil cek sitasi, dan durasi latensi.

---

## 5. Penjelasan Folder & Berkas Lainnya (di luar Frontend)

### A. Berkas Root Proyek
* [`README.md`](file:///home/luco/luco-untan/README.md): Dokumentasi ringkas sistem, diagram arsitektur, daftar task Pixi, dan panduan mulai cepat.
* [`CURRENT_STATE.md`](file:///home/luco/luco-untan/CURRENT_STATE.md): Matriks kesiapan komponen, ringkasan pengujian otomatis, dan batasan lingkup akademik.
* [`WALKTHROUGH.md`](file:///home/luco/luco-untan/WALKTHROUGH.md): Panduan tutorial langkah demi langkah operasional Luco dari instalasi hingga evaluasi.
* [`AGENTS.md`](file:///home/luco/luco-untan/AGENTS.md): Pedoman kontribusi kode, aturan basis data vault, dan batasan lingkup tugas besar.
* [`CLAUDE.md`](file:///home/luco/luco-untan/CLAUDE.md) & [`GEMINI.md`](file:///home/luco/luco-untan/GEMINI.md): Konfigurasi pedoman agentic workflow.
* [`Dockerfile`](file:///home/luco/luco-untan/Dockerfile): Berkas pembuatan container image aplikasi backend Luco berbasis Pixi environment.
* [`docker-compose.yml`](file:///home/luco/luco-untan/docker-compose.yml): Konfigurasi orkestrator multi-container produksi (menggabungkan luco-app, postgres, openviking, antigravity-proxy, dan indobert).
* [`pixi.toml`](file:///home/luco/luco-untan/pixi.toml) & [`pixi.lock`](file:///home/luco/luco-untan/pixi.lock): File konfigurasi package manager Pixi yang mengunci versi Python 3.13, dependensi Conda/PyPI, serta mendefinisikan otomasi script perintah (`pixi run ...`).
* [`pytest.ini`](file:///home/luco/luco-untan/pytest.ini): Konfigurasi test runner pytest dengan dukungan pengujian asinkron.
* [`ov.conf`](file:///home/luco/luco-untan/ov.conf) & [`ov.conf.example`](file:///home/luco/luco-untan/ov.conf.example): Berkas konfigurasi OpenViking server.
* [`.env.example`](file:///home/luco/luco-untan/.env.example): Contoh variabel lingkungan yang dibutuhkan sistem.
* [`skills-lock.json`](file:///home/luco/luco-untan/skills-lock.json): Catatan integritas plugin keahlian agent.

### B. Basis Pengetahuan Kampus (`vault/`)
Merupakan *Single Source of Truth* informasi prodi dalam format Markdown ber-frontmatter YAML:
* `akademik/`: Kurikulum 2026 (140 SKS), Kurikulum 2016 (144 SKS), Capaian Pembelajaran Lulusan (CPL), dan pedoman akademik.
* `dosen/`: Profil 33 dosen Informatika UNTAN yang terkelompokkan dalam 5 KBK: `ai-komputasi`, `jaringan-keamanan`, `rpl-mobile`, `si-spasial`, dan `umum`.
* `fasilitas-lab/`: Profil laboratorium komputer dan deskripsi kelompok bidang keahlian.
* `kemahasiswaan/`: Catatan organisasi HMIF dan hasil tracer study alumni.
* `kp-ta/`: Pedoman lengkap Kerja Praktik (KP), Seminar Proposal, dan Tugas Akhir / Skripsi.
* `profil/`: Visi, misi, sejarah, struktur organisasi, dan akreditasi prodi.
* [`lookup.json`](file:///home/luco/luco-untan/vault/lookup.json): Berkas data kompilasi dosen hasil ekstraksi otomatis dari frontmatter (dilarang diedit manual).
* [`manifest.json`](file:///home/luco/luco-untan/vault/manifest.json): JSON Tree Manifest pemetaan hierarki heading dokumen vault dan nomor barisnya.

### C. Skrip Otomasi & Benchmark (`scripts/`)
* [`benchmark_context_stuffing_vs_luco.py`](file:///home/luco/luco-untan/scripts/benchmark_context_stuffing_vs_luco.py): Skrip pengujian empiris multi-turn antara Context Stuffing (inject semua dokumen ke LLM) vs Luco Hybrid RAG.
* [`benchmark_embeddings.py`](file:///home/luco/luco-untan/scripts/benchmark_embeddings.py): Menjalankan pengujian perbandingan akurasi retrieval antara varian model IndoBERT (Indo4B p1 vs p2 vs IndoLEM).
* [`benchmark_modes.py`](file:///home/luco/luco-untan/scripts/benchmark_modes.py): Menguji perbandingan head-to-head 3 mode inferensi Luco (latensi, konsumsi token, biaya, dan akurasi sitasi).
* [`build_lookup.py`](file:///home/luco/luco-untan/scripts/build_lookup.py): Memindai frontmatter berkas dosen di `vault/dosen/` dan menyusun berkas `vault/lookup.json`.
* [`build_manifest.py`](file:///home/luco/luco-untan/scripts/build_manifest.py): Memindai seluruh heading dokumen vault dan menyusun `vault/manifest.json`.
* [`check_links.py`](file:///home/luco/luco-untan/scripts/check_links.py): Memeriksa integritas tautan relatif antar-dokumen Markdown di vault guna memastikan 0 tautan rusak.
* [`crawl_openalex.py`](file:///home/luco/luco-untan/scripts/crawl_openalex.py): Crawler berbasis Python HTTPX untuk mengumpulkan daftar publikasi dan sitasi dosen dari OpenAlex ke folder staging.
* [`fetch_and_convert_dokumen.py`](file:///home/luco/luco-untan/scripts/fetch_and_convert_dokumen.py): Skrip pengunduh dan konversi 26 berkas resmi Directus menjadi Markdown via PyMuPDF4LLM & Mammoth.
* [`ingest.py`](file:///home/luco/luco-untan/scripts/ingest.py): Skrip pengunggah basis data vault ke server OpenViking.
* [`monitor.py`](file:///home/luco/luco-untan/scripts/monitor.py): Dashboard CLI interaktif pemantauan status container Docker dan statistik audit token.
* [`reorganize_vault.py`](file:///home/luco/luco-untan/scripts/reorganize_vault.py): Skrip migrasi saat menstrukturkan ulang data lama ke dalam 6 kategori modular.
* [`spike.py`](file:///home/luco/luco-untan/scripts/spike.py): Skrip pengujian cepat integrasi koneksi dan pencarian semantik vektor OpenViking secara langsung.

### D. Sub-Layanan Eksternal (`dependencies/`)
* [`dependencies/docker-compose.yml`](file:///home/luco/luco-untan/dependencies/docker-compose.yml): Orkestrator untuk menjalankan sub-services dependensi saja (`postgres`, `openviking`, `antigravity-proxy`, `indobert`).
* `antigravity-proxy/`: Layanan proxy berbasis TypeScript/Bun untuk menjembatani autentikasi Google OAuth dengan endpoint OpenAI-compatible pada model Gemini.
* `indobert-embedder/`: Microservice Python FastAPI pembungkus model IndoBERT.
* `indobert-cache/`: Direktori penyimpanan cache bobot model Hugging Face.
* `postgres-data/`: Direktori mount penyimpanan fisik data PostgreSQL.

### E. Dokumentasi & Laporan (`docs/`)
* [`docs/README.md`](file:///home/luco/luco-untan/docs/README.md): Indeks pusat dokumentasi teknis.
* [`architecture.md`](file:///home/luco/luco-untan/docs/architecture.md): Dokumen desain arsitektur mendalam.
* [`api-reference.md`](file:///home/luco/luco-untan/docs/api-reference.md): Spesifikasi lengkap seluruh endpoint REST API.
* [`database.md`](file:///home/luco/luco-untan/docs/database.md): Dokumentasi basis data PostgreSQL dan aturan sesi aktif tunggal.
* [`rate-limiting.md`](file:///home/luco/luco-untan/docs/rate-limiting.md): Desain dan strategi rate limiter berbasis identitas.
* [`vault-and-knowledge.md`](file:///home/luco/luco-untan/docs/vault-and-knowledge.md): Standar kurasi dokumen dan taksonomi vault.
* [`deployment.md`](file:///home/luco/luco-untan/docs/deployment.md): Panduan instalasi dan deployment server produksi.
* [`evaluation.md`](file:///home/luco/luco-untan/docs/evaluation.md): Metodologi pengujian dan benchmark akurasi RAG.
* [`ERD_v1.png`](file:///home/luco/luco-untan/docs/ERD_v1.png): Diagram relasi entitas basis data.
* `laporan/`: Berisi arsip laporan akhir pengujian komparasi model embedding dan pengujian menyeluruh aplikasi.

### F. Pengujian & Evaluasi (`eval/` & `tests/`)
* [`eval/questions.jsonl`](file:///home/luco/luco-untan/eval/questions.jsonl): Dataset benchmark pertanyaan akademik, profil dosen, dan pertanyaan out-of-scope.
* [`eval/run_eval.py`](file:///home/luco/luco-untan/eval/run_eval.py): Skrip runner evaluasi performa Luco RAG dibandingkan baseline non-RAG menggunakan LLM-as-a-judge.
* `eval/reports/`: Kumpulan berkas laporan log hasil eksekusi benchmark evaluasi.
* `tests/`: Kumpulan 13 berkas unit test otomatis (78/78 tests passed 100%) yang mencakup pengujian agen, API, autentikasi, backend, lookup, monitoring, rate limiting, router, sesi PostgreSQL, resilience transport, dan live integration test OpenViking.

### G. Folder Pendukung
* `Motivation/`: Berisi lembar konsultasi resmi Tugas Besar UAS AI 2026 dalam format PDF.
* `crawl-output/`: Staging area untuk menyimpan hasil mentah scraping crawler sebelum diverifikasi masuk ke vault.
* `data-raw/`: Berkas zip historis sumber data awal sebelum restrukturisasi.
* `logs/`: Tempat penyimpanan rekaman aktivitas sistem ([audit.jsonl](file:///home/luco/luco-untan/logs/audit.jsonl) dan [trajectory.jsonl](file:///home/luco/luco-untan/logs/trajectory.jsonl)).

---

## 6. Struktur Direktori Proyek (Tree View)

```text
luco-untan/
├── AGENTS.md                  # Pedoman agen AI, aturan kode, dan batasan lingkup akademik
├── CURRENT_STATE.md           # Status terkini sistem, matriks kesiapan, & ringkasan tes
├── Dockerfile                 # Konfigurasi container image untuk aplikasi Luco
├── docker-compose.yml         # Orkestrasi seluruh container layanan (full-stack)
├── ov.conf, ov.conf.example   # Konfigurasi server OpenViking & dense embedding IndoBERT
├── pixi.toml, pixi.lock       # Manajemen paket dependensi Conda/Python & otomasi task
├── pytest.ini                 # Konfigurasi testing otomatis pytest
├── README.md, WALKTHROUGH.md  # Panduan dokumentasi utama dan alur operasional sistem
│
├── src/luco/                  # [KODE UTAMA BACKEND PYTHON]
│   ├── __init__.py            # Inisialisasi modul paket Python luco
│   ├── agent.py               # LlamaIndex FunctionAgent & siklus penalaran RAG
│   ├── api.py                 # FastAPI server (Auth, Session, Chat, OpenAI spec)
│   ├── auth.py                # Autentikasi JWT, bcrypt password, & Google OAuth
│   ├── backends.py            # Layer abstraksi retrieval (OpenViking SDK & Local fallback)
│   ├── citations.py           # Validasi sumber tautan rujukan jawaban (groundedness)
│   ├── clarifications.py      # Modul deteksi pertanyaan ambigu (Active Clarification)
│   ├── cli.py                 # Antarmuka chat interaktif di terminal (REPL)
│   ├── config.py              # Konfigurasi lingkungan & settings aplikasi
│   ├── db.py, schema.sql      # Database PostgreSQL asyncpg & aturan sesi tunggal aktif
│   ├── llm.py                 # Multi-provider LLM (Antigravity Proxy & Bifrost failover)
│   ├── lookup.py              # Mesin pencari data dosen pasti (NIP/Email) anti-halusinasi
│   ├── monitoring.py          # Perhitungan token, latensi, estimasi biaya, & audit logging
│   ├── prompts.py             # System prompt agen, router, & panduan instruksi
│   ├── ratelimit.py           # Identity-based rate limiter (anti IP-ban kampus)
│   ├── router.py              # Upfront Router penepis pertanyaan out-of-scope (Dual-LLM step 1)
│   ├── tools.py               # Definisi 4 tool agen (cari dosen, telusuri prodi, baca, list)
│   └── trajectory.py          # Perekam jejak langkah reasoning agen (JSONL)
│
├── vault/                     # [BASIS PENGETAHUAN KAMPUS / GROUND TRUTH]
│   ├── akademik/              # Kurikulum 2026/2016, CPL, & panduan akademik
│   ├── dosen/                 # Profil 33 dosen prodi dibagi per kelompok keahlian (KBK)
│   ├── fasilitas-lab/         # Direktori laboratorium & kelompok riset
│   ├── kemahasiswaan/         # Informasi HMIF & tracer study alumni
│   ├── kp-ta/                 # Panduan Kerja Praktik, Proposal, & Skripsi/TA
│   ├── profil/                # Visi-misi, sejarah, & akreditasi prodi
│   ├── lookup.json            # Kamus data dosen terstruktur untuk lookup pasti
│   └── manifest.json          # JSON Tree Manifest pemetaan heading & nomor baris dokumen
│
├── dependencies/              # [SUB-SERVICES & MICROSERVICES DOCKER]
│   ├── docker-compose.yml     # Orkestrasi PostgreSQL, OpenViking, Proxy, & IndoBERT
│   ├── antigravity-proxy/     # Proxy Google OAuth menuju Gemini (Primary LLM)
│   ├── indobert-embedder/     # Microservice embedding IndoBERT (768-dim, /v1/embeddings)
│   ├── indobert-cache/        # Cache lokal penyimpanan bobot model Hugging Face
│   └── postgres-data/         # Volume persisten database PostgreSQL
│
├── scripts/                   # [SKRIP BUILD, CRAWLER, & PEMELIHARAAN]
│   ├── benchmark_embeddings.py# Komparasi akurasi model embedding IndoBERT
│   ├── benchmark_modes.py     # Benchmark perbandingan 3 mode inferensi Luco
│   ├── build_lookup.py        # Kompilasi frontmatter dosen ke lookup.json
│   ├── build_manifest.py      # Pembuatan JSON Tree Manifest heading vault
│   ├── check_links.py         # Pengecekan integritas tautan antar-dokumen vault
│   ├── crawl_openalex.py      # Pengambil data publikasi dosen dari API OpenAlex
│   ├── ingest.py              # Ingesti & chunking dokumen vault ke OpenViking
│   ├── monitor.py             # Dashboard CLI status container & pemantauan audit
│   └── spike.py               # Pengujian langsung integrasi retrieval OpenViking
│
├── docs/                      # [DOKUMENTASI TEKNIS & ARSIP LAPORAN]
│   ├── architecture.md        # Arsitektur detail sistem Hybrid Agentic RAG
│   ├── api-reference.md       # Spesifikasi seluruh endpoint REST API
│   ├── database.md, ERD_v1.png# Dokumentasi ERD dan tabel relasional database
│   ├── rate-limiting.md       # Penjelasan desain rate limiter anti IP-ban
│   ├── vault-and-knowledge.md # Panduan struktur dan kurasi dokumen pengetahuan
│   └── laporan/               # Data mentah dan laporan akhir pengujian aplikasi
│
├── eval/                      # [EVALUASI TOLOK UKUR & PERTANYAAN BENCHMARK]
│   ├── questions.jsonl        # Kumpulan pertanyaan benchmark prodi
│   ├── run_eval.py            # Skrip evaluasi LLM-as-a-judge vs non-RAG baseline
│   └── reports/               # Riwayat laporan hasil eksekusi evaluasi
│
├── tests/                     # [TEST SUITE PYTEST - 100% PASSED]
│   ├── test_agent.py, test_router.py, test_lookup.py, ... (12 berkas pengujian)
│
├── crawl-output/              # Staging hasil ekstraksi crawler sebelum masuk vault
├── data-raw/                  # Arsip zip data mentah awal (referensi historis)
├── logs/                      # Log jejak reasoning (trajectory) & catatan token audit
└── Motivation/                # Berkas proposal & lembar konsultasi Tugas Besar UAS
```
