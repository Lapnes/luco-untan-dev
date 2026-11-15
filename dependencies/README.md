# Dependencies & Sub-Services Luco

Folder ini mengelola sub-layanan eksternal pendukung sistem Luco menggunakan containerization Docker.

## Daftar Layanan

1. **`antigravity-proxy` (`dependencies/antigravity-proxy`)**
   - **Fungsi:** Gateway / proxy OpenAI-compatible untuk model Gemini 3.8 (Antigravity).
   - **Port:** `3000` (`http://localhost:3000/v1`)
   - **Sumber upstream:** `https://github.com/frieser/antigravity-proxy.git` (Git Submodule)
   - **Data & Auth:** Disimpan di `dependencies/antigravity-proxy/data/` (diabaikan oleh git demi keamanan).

2. **`openviking`**
   - **Fungsi:** Engine retrieval dokumen dan vektor database.
   - **Port:** `1933` (`http://localhost:1933`)
   - **Image:** `ghcr.io/volcengine/openviking:main`
   - **Config:** Mount konfigurasi dari `../ov.conf` dan data dari `../.data/openviking`.

3. **`postgres`**
   - **Fungsi:** Database relasional PostgreSQL 16 (skema multi-session, full-text search FTS, dan audit log request/token/biaya).
   - **Port:** `5432` (`postgresql://luco:lucopass123@localhost:5432/lucodb`)
   - **Image:** `postgres:16-alpine`
   - **Data:** Disimpan di `./postgres-data` (diabaikan oleh git).

---

## Cara Menjalankan

### Melalui Pixi (Direkomendasikan)
Dari root project:
- Nyalakan semua dependensi: `pixi run up:deps`
- Nyalakan hanya OpenViking: `pixi run up:viking`
- Nyalakan hanya Antigravity Proxy: `pixi run up:proxy`
- Matikan semua dependensi: `pixi run down:deps`

### Melalui Docker Compose Langsung
```bash
# Menjalankan seluruh dependencies di background
docker compose -f dependencies/docker-compose.yml up -d

# Memeriksa log proxy
docker compose -f dependencies/docker-compose.yml logs -f antigravity-proxy
```

---

## Menghubungkan Akun Google ke `antigravity-proxy`

1. Pastikan container `antigravity-proxy` sudah berjalan.
2. Buka antarmuka web / dashboard di browser: `http://localhost:3000`.
3. Login menggunakan akun Google yang memiliki akses Antigravity.
4. Pastikan akun Google sudah pernah membuat API Key di [Google AI Studio](https://aistudio.google.com) agar Google Cloud `project_id` otomatis terbuat.
5. Konfigurasikan `.env` aplikasi utama:
   ```env
   LLM_API_BASE=http://localhost:3000/v1
   LLM_API_KEY=dummy-key
   LLM_MODEL=gemini-3.8-flash-high
   ```

