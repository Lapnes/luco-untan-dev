# Referensi REST API Luco

Dokumen ini menyediakan spesifikasi lengkap antarmuka pemrograman aplikasi (REST API) Luco, mencakup otentikasi JWT, pengelolaan sesi aktif, interaksi obrolan agen, dan endpoint pemantauan audit.

**Base URL:** `http://localhost:8000` (atau host server terpasang)  
**Format Payload:** `application/json`  
**Otentikasi:** Header `Authorization: Bearer <access_token>`

---

## 1. Otentikasi & Akun Pengguna

### A. Registrasi Pengguna
Mendaftarkan akun mahasiswa atau dosen baru, sekaligus secara otomatis membuatkan sesi percakapan aktif awal.

- **Endpoint:** `POST /v1/auth/register`
- **Akses:** Publik
- **Request Body:**
  ```json
  {
    "email": "mahasiswa@untan.ac.id",
    "password": "PasswordKuat123!",
    "full_name": "Budi Mahasiswa",
    "nim_or_nip": "F1051201001",
    "angkatan": 2022
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "user": {
      "id": "e4b6c310-9c2e-4b2a-88cb-527e02df0821",
      "email": "mahasiswa@untan.ac.id",
      "full_name": "Budi Mahasiswa",
      "nim_or_nip": "F1051201001",
      "angkatan": 2022,
      "created_at": "2026-11-14T10:00:00Z"
    },
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

### B. Login Pengguna
Memvalidasi kredensial dan menerbitkan access token (berlaku 2 jam) serta refresh token (berlaku 7 hari).

- **Endpoint:** `POST /v1/auth/login`
- **Akses:** Publik *(Dibatasi laju per alamat email untuk mencegah brute-force)*
- **Request Body:**
  ```json
  {
    "email": "mahasiswa@untan.ac.id",
    "password": "PasswordKuat123!"
  }
  ```
- **Response (200 OK):** Sama dengan respons registrasi di atas.

---

### C. Refresh Access Token
Menerbitkan access token baru menggunakan refresh token yang valid tanpa perlu login ulang.

- **Endpoint:** `POST /v1/auth/refresh`
- **Akses:** Publik
- **Request Body:**
  ```json
  {
    "refresh_token": "eyJhbGciOi..."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

### D. Profil Pengguna Saat Ini
- **Endpoint:** `GET /v1/auth/me`
- **Akses:** Memerlukan JWT Bearer Token
- **Response (200 OK):** Mengembalikan data objek profil pengguna yang sedang login.

---

## 2. Endpoint Sesi Aktif & Chat Otomatis

Kumpulan endpoint ini dirancang khusus untuk antarmuka pengguna (Frontend UI). Pengembang frontend tidak perlu menyimpan atau mengelola `session_id` di setiap request obrolan.

### A. Ambil Sesi Aktif Saat Ini
Mengambil kanvas percakapan yang sedang aktif beserta seluruh riwayat pesannya untuk langsung dirender di layar obrolan.

- **Endpoint:** `GET /v1/session/active`
- **Akses:** Memerlukan JWT Bearer Token
- **Response (200 OK):**
  ```json
  {
    "session": {
      "id": "7fa1bc82-0129-4562-b9cf-9876543210ab",
      "title": "Alur Pengajuan Judul KP",
      "is_active": true,
      "created_at": "2026-11-14T10:05:00Z",
      "updated_at": "2026-11-14T10:15:00Z"
    },
    "messages": [
      {
        "id": "11111111-2222-3333-4444-555555555555",
        "role": "user",
        "content": "Gimana syarat mulai KP?",
        "citations": [],
        "created_at": "2026-11-14T10:06:00Z"
      },
      {
        "id": "66666666-7777-8888-9999-000000000000",
        "role": "assistant",
        "content": "Syarat memulai Kerja Praktik adalah telah menempuh minimal 80 SKS...",
        "citations": [
          {"text": "Buku Panduan KP", "target": "kp-ta/index.md"}
        ],
        "created_at": "2026-11-14T10:06:02Z"
      }
    ]
  }
  ```

---

### B. Kirim Pesan ke Sesi Aktif (Chat Utama)
Mengirim pertanyaan pengguna langsung ke sesi yang sedang aktif. Backend secara otomatis menyaring pertanyaan via Upfront Router, membatasi konteks 6 pesan terakhir ke LlamaIndex, merekam jawaban dan sitasi, serta membuat judul sesi otomatis jika merupakan pesan pertama.

- **Endpoint:** `POST /v1/chat`
- **Akses:** Memerlukan JWT Bearer Token
- **Rate Limit:** Terikat pada `user_id` (20 req/menit, 40.000 token/menit, 200.000 token/hari)
- **Request Body:**
  ```json
  {
    "content": "Siapa saja dosen pembimbing untuk bidang Rekayasa Perangkat Lunak?"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "id": "chatcmpl-a1b2c3d4e5f6",
    "object": "chat.completion",
    "created": 1794558000,
    "model": "luco",
    "session_id": "7fa1bc82-0129-4562-b9cf-9876543210ab",
    "choices": [
      {
        "index": 0,
        "message": {
          "id": "66666666-7777-8888-9999-000000000000",
          "role": "assistant",
          "content": "Dosen di bidang Rekayasa Perangkat Lunak antara lain...",
          "clarification": null
        },
        "finish_reason": "stop"
      }
    ],
    "luco": {
      "steps": 2,
      "citations": {
        "links": 1,
        "verified": [{"text": "Profil Dosen", "target": "dosen/index.md"}],
        "unverified": [],
        "all_verified": true,
        "has_citations": true
      },
      "trajectory": [
        {"tool": "cari_profil_dosen", "args": {"query": "RPL"}, "output_chars": 340}
      ],
      "rejected": false,
      "reason": null
    },
    "usage": {
      "prompt_tokens": 420,
      "completion_tokens": 150,
      "total_tokens": 570,
      "estimated_cost_usd": 0.000102,
      "estimated_cost_idr": 1.65
    }
  }
  ```

---

### C. Clear Chat (Arsipkan Sesi & Buat Kanvas Baru)
Mengubah status sesi saat ini menjadi arsip (`is_active = false`), lalu membuat dan mengaktifkan sesi baru yang bersih (`is_active = true`).

- **Endpoint:** `POST /v1/session/clear`
- **Akses:** Memerlukan JWT Bearer Token
- **Response (200 OK):**
  ```json
  {
    "status": "cleared",
    "session": {
      "id": "99999999-aaaa-bbbb-cccc-dddddddddddd",
      "title": "Percakapan Baru",
      "is_active": true,
      "created_at": "2026-11-14T10:30:00Z",
      "updated_at": "2026-11-14T10:30:00Z"
    },
    "messages": []
  }
  ```

---

### D. Pindah Sesi (Switch Session)
Mengaktifkan kembali sesi lama yang ada di arsip, menonaktifkan sesi yang sedang berjalan, dan mengembalikan riwayat pesan sesi tersebut agar pengguna dapat membaca dan melanjutkannya.

- **Endpoint:** `POST /v1/session/{session_id}/switch`
- **Akses:** Memerlukan JWT Bearer Token
- **Response (200 OK):** Mengembalikan objek sesi yang baru diaktifkan beserta riwayat pesannya.

---

### E. Umpan Balik Pesan (Like / Dislike Feedback)
Mencatat reaksi pengguna (*like*, *dislike*, atau *none*) terhadap jawaban asisten. Data ini disimpan pada tabel `chat_messages` dan disinkronisasikan ke `audit_logs` sebagai bahan evaluasi kepuasan pengguna (*user satisfaction*) dan analisis kualitas RAG.

- **Endpoint:** `POST /v1/messages/{message_id}/feedback`
- **Akses:** Memerlukan JWT Bearer Token
- **Request Body:**
  ```json
  {
    "feedback": "like"
  }
  ```
  *(Nilai yang diizinkan: `"like"`, `"dislike"`, `"none"`)*
- **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "message_id": "66666666-7777-8888-9999-000000000000",
    "feedback": "like"
  }
  ```

---

## 3. Manajemen Riwayat Sesi & Berbagi

- `GET /v1/sessions`: Mengambil daftar seluruh sesi milik pengguna (baik aktif maupun arsip) untuk ditampilkan pada sidebar riwayat.
- `GET /v1/sessions/{session_id}`: Mengambil detail dan pesan spesifik dari sebuah sesi riwayat.
- `DELETE /v1/sessions/{session_id}`: Menghapus sebuah sesi riwayat beserta seluruh pesannya secara permanen.
- `GET /v1/sessions/{session_id}/export.md`: Mengunduh transkrip percakapan sesi dalam format dokumen Markdown (.md) bertanggal.
- `GET /v1/share/{session_id}`: Menghasilkan snapshot publik dari sesi obrolan (read-only) untuk dibagikan ke mahasiswa atau dosen lain tanpa memerlukan login.

---

## 4. Katalog Berkas Resmi Directus (Dual-Option Access)

Menyediakan akses langsung ke 26 berkas formulir dan pedoman resmi Program Studi Informatika UNTAN:

- **Daftar Seluruh Berkas Resmi:**
  - `GET /v1/dokumen`: Mengembalikan daftar JSON 26 dokumen resmi lengkap dengan slug, judul, format master (PDF/DOCX), ukuran berkas, tanggal terbit, dan tautan unduhan.
- **Ekspor Naskah Teks Markdown:**
  - `GET /v1/dokumen/{doc_slug}/export.md`: Mengunduh atau membaca teks Markdown hasil ekstraksi PyMuPDF4LLM & Mammoth.
- **Unduh Berkas Master Fisik (Raw):**
  - `GET /v1/dokumen/{doc_slug}/raw`: Mengunduh langsung file master fisik biner asli (`application/pdf` atau `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) yang berstempel dan bertanda tangan basah resmi.

---

## 5. Eksplorasi Metadata Dokumen Vault

- `GET /v1/vault/documents`: Menampilkan seluruh daftar dokumen Markdown vault yang terpetakan dalam `vault/manifest.json` (104 dokumen) beserta pohon heading H1-H3.
- `GET /v1/vault/document?path={path}`: Mengambil isi naskah dokumen vault spesifik untuk ditampilkan di *Document Drawer*.

---

## 6. Otentikasi Google OAuth 2.0

- `GET /v1/auth/google/login`: Menghasilkan URL pengalihan (*redirect URL*) ke halaman persetujuan akun Google SSO UNTAN.
- `GET /v1/auth/google/callback`: Menerima kode otorisasi dari Google, memvalidasi email, dan mengalihkan pengguna kembali ke frontend dengan token sesi.
- `POST /v1/auth/google/verify`: Memverifikasi Google ID Token langsung dari Single Page Application (SPA).

---

## 7. Endpoint Kompatibilitas OpenAI

Digunakan untuk evaluasi otomatis (`eval/run_eval.py`), integrasi dengan antarmuka Open-WebUI, atau pemanggilan oleh bot pihak ketiga secara stateless.

- **Endpoint:** `POST /v1/chat/completions`
- **Akses:** Terbuka (Tanpa wajib login)
- **Request Body (OpenAI Standard):**
  ```json
  {
    "model": "luco",
    "messages": [
      {"role": "user", "content": "Berapa SKS syarat seminar proposal skripsi?"}
    ]
  }
  ```
- **Response (200 OK):** Format respons standar `chat.completion` OpenAI dilengkapi metadata `luco` dan `usage`.

---

## 8. Pemantauan & Analisis Audit (Monitoring)

Seluruh endpoint monitoring dilindungi oleh role administrator (`ADMIN_EMAILS` di `.env`). Pengguna wajib memiliki token JWT yang email-nya terdaftar sebagai administrator.

### A. Ringkasan Statistik Audit (`GET /v1/monitoring/summary`)
Mengambil metrik agregat performa sistem, konsumsi token, biaya, latensi, dan statistik per model.

- **Query Parameters:**
  - `start_time` *(opsional)*: Filter waktu mulai format ISO 8601 (misal `2026-11-01T00:00:00Z`).
  - `end_time` *(opsional)*: Filter waktu selesai format ISO 8601.
  - `model` *(opsional)*: Filter parsial nama model (misal `gemini`, `deepseek`).
- **Response (200 OK):**
  ```json
  {
    "total_requests": 142,
    "total_users": 18,
    "total_sessions": 35,
    "total_prompt_tokens": 85400,
    "total_completion_tokens": 28600,
    "total_tokens": 114000,
    "total_cost_usd": 0.0215,
    "total_cost_idr": 348.30,
    "avg_latency_s": 1.84,
    "total_rejected": 14,
    "rejection_rate_percent": 9.86,
    "models": [
      {
        "model": "antigravity-gemini-3-flash",
        "requests": 128,
        "tokens": 104200,
        "prompt_tokens": 78200,
        "completion_tokens": 26000,
        "cost_usd": 0.0195,
        "cost_idr": 315.90,
        "avg_latency_s": 1.72,
        "errors": 10
      }
    ]
  }
  ```

---

### B. Daftar Log Audit Tabular (`GET /v1/monitoring/logs`)
Mengambil catatan riwayat audit interaksi lengkap dengan rincian telemetri mikrofonis, token bertingkat, dan jejak eksekusi tool.

- **Query Parameters:**
  - `limit` *(default: 500, min: 1, max: 1000)*: Jumlah baris data per halaman.
  - `offset` *(default: 0)*: Posisi pergeseran baris data.
  - `model` *(opsional)*: Filter nama model.
  - `start_time` *(opsional)*: Filter waktu mulai ISO 8601.
  - `end_time` *(opsional)*: Filter waktu selesai ISO 8601.
- **Response (200 OK):**
  ```json
  {
    "total": 142,
    "offset": 0,
    "limit": 500,
    "logs": [
      {
        "id": "e4a3b2c1-0000-1111-2222-333344445555",
        "created_at": "2026-11-15T18:24:10+07:00",
        "user_id": "e4b6c310-9c2e-4b2a-88cb-527e02df0821",
        "user_email": "mahasiswa@untan.ac.id",
        "session_id": "7fa1bc82-0129-4562-b9cf-9876543210ab",
        "message_id": "66666666-7777-8888-9999-000000000000",
        "endpoint": "/v1/chat",
        "model": "antigravity-gemini-3-flash",
        "question": "Berapa SKS minimal untuk mengambil Kerja Praktik?",
        "answer": "Syarat minimal untuk mengambil Kerja Praktik (KP) di Prodi Informatika UNTAN adalah...",
        "user_prompt_tokens": 12,
        "system_prompt_tokens": 340,
        "context_tokens": 620,
        "prompt_tokens": 972,
        "completion_tokens": 85,
        "total_tokens": 1057,
        "estimated_cost_usd": 0.000131,
        "estimated_cost_idr": 2.12,
        "latency_s": 1.45,
        "steps": 1,
        "tool_calls": [
          {
            "tool": "telusuri_direktori_prodi",
            "args": {"query": "syarat SKS kerja praktik"},
            "duration_ms": 42.15,
            "files_accessed": ["kp-ta/panduan-kp.md"],
            "lines_accessed": "1 kandidat berkas relevan",
            "output": "..."
          }
        ],
        "system_prompt": "Identitas & Keamanan Sistem...",
        "user_prompt": "Berapa SKS minimal untuk mengambil Kerja Praktik?",
        "timing_breakdown": {
          "t_req_in": 1794558250.12,
          "router_latency_ms": 12.4,
          "tools_total_ms": 42.15,
          "tool_calls_breakdown": [
            {
              "tool": "telusuri_direktori_prodi",
              "duration_ms": 42.15,
              "files_accessed": ["kp-ta/panduan-kp.md"]
            }
          ],
          "llm_final_generation_ms": 1395.45,
          "total_latency_ms": 1450.0,
          "total_latency_s": 1.45
        },
        "feedback": "like",
        "rejected": false,
        "reason": null
      }
    ]
  }
  ```

---

### C. Ekspor Data Audit CSV (`GET /v1/monitoring/export`)
Mengunduh rekaman audit dalam format CSV untuk analisis spreadsheet atau evaluasi paper ilmiah. Mendukung parameter filter `model`, `start_time`, dan `end_time`.

- **Endpoint:** `GET /v1/monitoring/export?model=gemini`
- **Akses:** Memerlukan JWT Admin
- **Response (200 OK):** Berkas `text/csv` bertajuk `attachment; filename="luco_audit_dataset.csv"`.

---

## 9. Header Respons Rate Limiting (RFC 6585)

Setiap request yang menyentuh endpoint AI menyertakan header kuota transparan:
```http
X-RateLimit-Limit-Requests: 20
X-RateLimit-Remaining-Requests: 18
X-RateLimit-Limit-Tokens: 40000
X-RateLimit-Remaining-Tokens: 38400
```

Jika kuota terlampaui, server mengembalikan status **`429 Too Many Requests`**:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{
  "detail": "Batas laju permintaan terlampaui (20 req/menit). Coba lagi dalam 45 detik."
}
```

