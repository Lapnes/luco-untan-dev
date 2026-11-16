# AGENTS.md — Luco (luco-untan)

Chatbot asisten informasi Prodi Informatika UNTAN. Tugas Besar pengganti UAS Kecerdasan Buatan 2026 (kelompok 3 orang).
Hybrid agentic RAG: **LlamaIndex** (agent) + **OpenViking** (retrieval, Docker) + **lookup.json** (data tepat seperti NIP).
Bahasa dokumen/komentar: Indonesia. Nama kode/identifier: Inggris/Indonesia campur sudah lazim di repo ini.

## Perintah (pixi)
- `pixi install` — pasang env
- `pixi run test` — tes unit (tanpa jaringan/LLM)
- `pixi run build-lookup` — vault → `vault/lookup.json` (JANGAN edit lookup.json manual)
- `pixi run build-manifest` — generate `vault/manifest.json` tree heading
- `pixi run check-links` — cek tautan relatif di vault
- `pixi run up` — jalankan seluruh stack (OpenViking + antigravity-proxy + luco-app via Docker Compose)
- `pixi run up:deps` — jalankan sub-services dependensi saja (OpenViking & antigravity-proxy)
- `pixi run ingest` — masukkan vault ke OpenViking; `pixi run spike` — verifikasi hasil; `pixi run check-chunks` — statistik chunk & vektor OpenViking
- `pixi run serve` — API di :8000 (`POST /v1/chat/completions`, `GET /health`); `pixi run chat` — REPL
- `pixi run eval -- --judge` — evaluasi tolok ukur vs baseline tanpa RAG
- `pixi run benchmark-modes` — benchmark 3 mode inferensi (IndoBERT+Viking vs Fast vs Direct LLM)
- `pixi run benchmark-bert` — benchmark komparasi varian embedding IndoBERT
- `pixi run benchmark-context` — benchmark multi-turn Context Stuffing vs Luco Hybrid RAG

## Struktur
- `dependencies/` — sub-services eksternal (`docker-compose.yml`, `antigravity-proxy`, PostgreSQL, OpenViking)
- `vault/` sumber kebenaran pengetahuan (Markdown + frontmatter YAML; repo Git terpisah disarankan)
- `src/luco/` — `backends.py`, `tools.py`, `agent.py`, `router.py`, `auth.py`, `db.py`, `monitoring.py`, `prompts.py`, `citations.py`, `trajectory.py`, `api.py`
- `scripts/` — build_lookup, check_links, ingest, spike, crawl_openalex
- `eval/` — `questions.jsonl`, `run_eval.py`, `reports/`
- `crawl-output/` — staging hasil crawl OpenAlex; BUKAN vault

## Aturan
- Jangan commit `.env`, `ov.conf`, API key, atau `logs/`.
- Data dosen/publikasi yang `diverifikasi: true` tidak boleh ditimpa otomatis. Crawler hanya menulis ke `crawl-output/`.
- Agent hanya boleh menjawab dari hasil tool; sitasi harus dari field `sumber`/tautan dokumen (dicek `citations.py`).
- Backend dipilih lewat `LUCO_BACKEND` (`viking` atau `local`). Jaga antarmuka `find/read/ls` tetap sama di kedua backend.
- Setiap perubahan logika: tambah/ubah tes di `tests/`. Perubahan prompt: jalankan `pixi run eval` dan bandingkan.
- Kode yang menyentuh API OpenViking SDK dan LlamaIndex agent BELUM DIVERIFIKASI end-to-end (dibuat tanpa akses jaringan). Verifikasi dulu dengan spike sebelum menambah fitur.
- Pembuatan/output dokumen Markdown lengkap yang memuat blok kode internal (seperti ```format, ```text, atau ```mermaid) WAJIB dibungkus dengan 4 backticks (````) pada awal dan akhir agar tidak terpotong atau putus di UI.

## Yang sengaja tidak dikerjakan (di luar lingkup UAS)
JWT/RBAC, rate limiter, Qdrant, knowledge graph, MCP/skills, Whisper — tulis sebagai pengembangan lanjutan di laporan.

<!-- antislop:start -->
## antislop
For UI, copy, people, mobile layout, or code comments work, read these installed skill files directly (use these paths even if a same-named global skill exists):
- Core filter, always on: `antislop`: `.agents/skills/antislop/SKILL.md`
- UI / visual: `antislop-ui`: `.agents/skills/antislop-ui/SKILL.md`
- Copy & text: `antislop-copywriting`: `.agents/skills/antislop-copywriting/SKILL.md`
- People: `antislop-human`: `.agents/skills/antislop-human/SKILL.md`
- Mobile / responsive: `antislop-layoutmobile`: `.agents/skills/antislop-layoutmobile/SKILL.md`
- Code comments: `antislop-code`: `.agents/skills/antislop-code/SKILL.md`
Before starting, follow the core's "Two Usage Modes" section in strict order: explicit session instruction first, then global preference, then ask. A session instruction always wins. For a resolved mode, say `antislop active: <mode> (session override).` or `antislop active: <mode> (global preference).` once before presenting findings or making edits, using the actual mode and source. Acknowledging the user's request without naming the source does not replace this notice.
Only an explicit choice of antislop during or after selects a session mode. A request to review, audit, or avoid file edits does not select a mode; read the global preference in that case. Another skill's mode does not select antislop's mode.
If the mode is unresolved, ask during/after and end the response; wait for the answer before any UI review, planning, or concept. For read-only tasks, put the active-mode notice only at the start of the final answer, never in progress messages. For editing tasks, announce before the first edit and omit it from the final answer.
To update antislop later: `npx antislop-ai --update`, or run `npx antislop-ai` and pick Overwrite them.
<!-- antislop:end -->
