# Panduan Deployment & Operasional

Dokumen ini memandu proses instalasi, deployment kontainer Docker, konfigurasi environment, serta panduan operasional produksi untuk sistem Luco.

---

## 1. Prasyarat Lingkungan

- **Sistem Operasi:** Linux (Ubuntu 22.04/24.04 LTS direkomendasikan), macOS, atau Windows via WSL2.
- **Package Manager:** [Pixi](https://pixi.sh/) (Manajer dependensi berbasis Conda yang cepat dan reproduktif).
- **Container Engine:** Docker Engine (v24.0+) & Docker Compose v2.

---

## 2. Instalasi Lingkungan Pengembangan Lokal

### Langkah 1: Kloning Repositori & Pasang Dependensi
```bash
git clone https://github.com/luco-untan/luco-untan.git
cd luco-untan

# Memasang seluruh dependensi Python, C-extension, dan toolchain terisolasi
pixi install
```

### Langkah 2: Konfigurasi File Environment
Salin template konfigurasi dan sesuaikan nilainya:
```bash
cp .env.example .env
cp ov.conf.example ov.conf
```

Pastikan variabel penting telah diisi di [.env](file:///home/luco/luco-untan/.env):
```ini
LLM_API_BASE=http://localhost:3000/v1
LLM_API_KEY=dummy-key
LLM_MODEL=gemini-3.8-flash-high
LUCO_BACKEND=local
DATABASE_URL=postgresql://luco:lucopass123@localhost:5432/lucodb
JWT_SECRET=rahasia-jwt-acak-minimal-32-karakter
```

### Langkah 3: Menjalankan Sub-Services Dependensi
Jalankan 4 sub-services inti (PostgreSQL 16, OpenViking :1933, IndoBERT Embedder :8001, dan Antigravity LLM Proxy :3000):
```bash
pixi run up:deps
```

### Langkah 4: Inisialisasi Data Vault
```bash
# Bangun tabel lookup dari frontmatter 33 dosen
pixi run build-lookup

# Bangun manifest pohon heading H1-H3 104 dokumen vault
pixi run build-manifest

# Validasi tidak ada link internal yang rusak (0 tautan rusak)
pixi run check-links
```

### Langkah 5: Menjalankan Server API atau CLI REPL
- Menjalankan REST API server di `http://localhost:8000`:
  ```bash
  pixi run serve
  ```
- Menjalankan pengujian interaktif langsung di terminal:
  ```bash
  pixi run chat
  ```

---

## 3. Integrasi & Spike OpenViking

Jika ingin beralih dari mode pencarian lokal (`LUCO_BACKEND=local`) ke retriever semantik OpenViking (`LUCO_BACKEND=viking`):

1. **Ingest Vault ke OpenViking:**
   ```bash
   pixi run ingest
   ```
2. **Uji Validasi (Spike):**
   ```bash
   pixi run spike
   ```
   *Spike dinyatakan lolos jika: health OK, struktur folder vault terbaca di root ls, dan find berhasil menemukan dokumen yang relevan.*
3. **Ubah Backend:**
   Set `LUCO_BACKEND=viking` di `.env`, lalu restart server API.

---

## 4. Deployment Penuh dengan Docker Compose

Untuk deployment terpadu dalam satu perintah (termasuk aplikasi Luco, basis data, proxy, dan OpenViking):

```bash
# Membangun image aplikasi dan menjalankan seluruh layanan
docker compose up -d --build
```

### Arsitektur Jaringan Kontainer
Di dalam jaringan Docker Compose (`docker-compose.yml`), seluruh kontainer berkomunikasi menggunakan nama layanannya:
- `luco-app` $\rightarrow$ `postgres:5432` (PostgreSQL)
- `luco-app` $\rightarrow$ `openviking:1933` (Retriever)
- `luco-app` $\rightarrow$ `antigravity-proxy:3000` (LLM Gateway)

### Perintah Manajemen Layanan & Benchmark
| Tugas | Perintah Pixi | Perintah Docker Langsung |
| :--- | :--- | :--- |
| Start Seluruh Stack | `pixi run up` | `docker compose up -d` |
| Stop Seluruh Stack | `pixi run down` | `docker compose down` |
| Start Sub-Services Saja | `pixi run up:deps` | `docker compose -f dependencies/docker-compose.yml up -d` |
| Lihat Log Aplikasi | - | `docker compose logs -f luco-app` |
| Lihat Log Proxy | - | `docker compose logs -f antigravity-proxy` |
| Evaluasi Baseline vs RAG | `pixi run eval -- --judge` | `python eval/run_eval.py --judge` |
| Benchmark 3 Mode Inferensi | `pixi run benchmark-modes` | `python scripts/benchmark_modes.py` |
| Benchmark Embedding IndoBERT | `pixi run benchmark-bert` | `docker exec -i luco-indobert python - < scripts/benchmark_embeddings.py` |
| Benchmark Context Stuffing | `pixi run benchmark-context` | `python scripts/benchmark_context_stuffing_vs_luco.py` |

---

## 5. Deployment Server Produksi / Proxmox VE

Untuk deployment di server kampus atau infrastruktur virtualisasi Proxmox VE:

1. **Gunakan Reverse Proxy (Nginx / Caddy):**
   Arahkan domain resmi (misal: `luco.untan.ac.id`) ke port `8000` dengan sertifikat SSL/TLS otomatis Let's Encrypt:
   ```nginx
   server {
       server_name luco.untan.ac.id;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
2. **Pencadangan Data Rutin (*Backup Strategy*):**
   - **Vault Markdown:** Disimpan dan di-commit ke repositori Git terpisah.
   - **PostgreSQL Data:** Backup volume `dependencies/postgres-data/` secara berkala via `pg_dump`:
     ```bash
     docker exec -t luco-postgres pg_dump -U luco lucodb > backup_lucodb_$(date +%F).sql
     ```
3. **Daftar Periksa Keamanan Produksi:**
   - [ ] Ubah default `JWT_SECRET` di `.env` dengan string acak kuat.
   - [ ] Ubah default kata sandi PostgreSQL (`POSTGRES_PASSWORD`).
   - [ ] Batasi akses port 3000 (dashboard proxy) dan port 5432 hanya untuk localhost/internal Docker.

---

## 6. Layanan Background Permanen (Systemd User Service)

Agar aplikasi backend (`luco-api`) dan frontend (`luco-web`) selalu aktif di background bahkan saat sesi SSH terputus, sistem telah dikonfigurasi menggunakan **Systemd User Services**:

- **Backend API (`:8000`)**: `~/.config/systemd/user/luco-api.service`
- **Frontend Vite (`:5173`)**: `~/.config/systemd/user/luco-web.service`

### Perintah Manajemen Systemd:
```bash
# Cek status kedua layanan
systemctl --user status luco-api luco-web

# Restart layanan (misal setelah pull kode terbaru)
systemctl --user restart luco-api luco-web

# Melihat live logs sistem
journalctl --user -u luco-api -u luco-web -f

# Opsional: Memastikan layanan otomatis start saat boot sebelum login
sudo loginctl enable-linger luco
```

