"""
Bagian 2 Dokumen Laporan:
- BAB III: PERANCANGAN SISTEM & ARSITEKTUR
- BAB IV: IMPLEMENTASI SISTEM
"""

import os
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from scripts.build_full_report import (
    COLOR_NAVY, COLOR_STEEL, COLOR_CHARCOAL, COLOR_MUTED,
    add_heading_1, add_heading_2, add_heading_3, add_p, add_bullet,
    add_callout, add_code_block, format_styled_table
)

def add_chapter_3(doc):
    add_heading_1(doc, "BAB III: PERANCANGAN SISTEM & ARSITEKTUR", page_break=True)
    
    add_heading_2(doc, "3.1. Arsitektur Menyeluruh Sistem Luco")
    add_p(doc, "Sistem Luco dirancang menggunakan arsitektur berlapis (layered architecture) yang memisahkan tanggung jawab antara antarmuka pengguna, lapisan keamanan dan perutean kueri, penalaran agen cerdas, serta penelusuran basis pengetahuan:")
    
    # Diagram Blok Arsitektur
    add_code_block(doc,
                   "+-------------------------------------------------------------------------+\n"
                   "|                     ANTARMUKA PENGGUNA (FRONTEND SPA)                   |\n"
                   "|       React 18 + Vite 6 + Tailwind CSS + Lucide Icons (Port 5173/8000)  |\n"
                   "+-------------------------------------------------------------------------+\n"
                   "                                    |  HTTP REST / SSE Stream\n"
                   "                                    v\n"
                   "+-------------------------------------------------------------------------+\n"
                   "|               LAPISAN GATEWAY & KEAMANAN (FASTAPI :8000)               |\n"
                   "|  - Sliding-Window Token Bucket Rate Limiter (RPM & TPM Isolation)        |\n"
                   "|  - Upfront Deterministic Router (Tier 1 Heuristic Regex & Tier 2 LLM)  |\n"
                   "+-------------------------------------------------------------------------+\n"
                   "            | (Kueri Sapaan / Luar Domain)         | (Kueri In-Scope Prodi)\n"
                   "            v                                      v\n"
                   "+-----------------------+         +---------------------------------------+\n"
                   "|  Bypass Respon Instan |         |     LLAMAINDEX FUNCTION AGENT         |\n"
                   "|  (0 ms Latensi, Rp 0) |         |     (Multi-step ReAct Tool Calling)   |\n"
                   "+-----------------------+         +---------------------------------------+\n"
                   "                                                   | Memanggil Tools\n"
                   "                   +-------------------------------+-------------------------------+\n"
                   "                   |                               |                               |\n"
                   "                   v                               v                               v\n"
                   "       +-----------------------+       +-----------------------+       +-----------------------+\n"
                   "       |  cari_profil_dosen    |       | telusuri_direktori    |       |  baca_dokumen_lengkap |\n"
                   "       |  (lookup.json)        |       | (OpenViking :1933)    |       |  (Safe Reader Vault)  |\n"
                   "       |  Zero-Hallucination   |       | + IndoBERT-p1 :8001   |       |  Max 12.000 Karakter  |\n"
                   "       +-----------------------+       +-----------------------+       +-----------------------+\n"
                   "                   |                               |                               |\n"
                   "                   +-------------------------------+-------------------------------+\n"
                   "                                                   |\n"
                   "                                                   v\n"
                   "+-------------------------------------------------------------------------+\n"
                   "|                LAPISAN VERIFIKASI SITASI & PERSISTENSI DATA             |\n"
                   "|  - CitationsVerifier (Validasi Tautan Sumber via Negative Lookbehind)   |\n"
                   "|  - PostgreSQL 16 Alpine (:5432) — Sesi, Riwayat Pesan, dan Audit Log   |\n"
                   "+-------------------------------------------------------------------------+")

    add_p(doc, "Bagan Alir Alur Kerja Inferensi Sistem:", bold_prefix="Penjelasan Alur Inferensi: ")
    add_bullet(doc, "Pengguna mengirimkan pesan melalui antarmuka web obrolan.", bold_prefix="1. Request Ingestion: ")
    add_bullet(doc, "FastAPI memeriksa kuota request pengguna pada sliding window rate limiter untuk mencegah abuse.", bold_prefix="2. Rate Limit Verification: ")
    add_bullet(doc, "Upfront Router mengevaluasi kueri. Jika kueri adalah sapaan umum atau pertanyaan di luar cakupan akademik (misalnya pertanyaan resep, tugas mata kuliah luar, atau politik), sistem mengembalikan respons penolakan sopan secara instan (latensi 0 ms, 0 token LLM).", bold_prefix="3. Upfront Routing: ")
    add_bullet(doc, "Jika kueri berada dalam lingkup akademik Informatika UNTAN, kueri dialirkan ke LlamaIndex FunctionAgent.", bold_prefix="4. Agent Invocation: ")
    add_bullet(doc, "Agen mengevaluasi informasi yang dibutuhkan dan memanggil fungsi spesifik: lookup.json untuk profil dosen dan OpenViking + IndoBERT untuk regulasi atau prosedur dokumen.", bold_prefix="5. Tool Execution Loop: ")
    add_bullet(doc, "Jawaban akhir diverifikasi oleh CitationsVerifier untuk memastikan setiap tautan rujukan benar-benar berasal dari dokumen yang dibuka pada giliran percakapan tersebut.", bold_prefix="6. Citation Validation: ")
    add_bullet(doc, "Jawaban dikirimkan ke frontend secara responsif dan dicatat ke basis data PostgreSQL untuk pemantauan sesi dan audit token.", bold_prefix="7. Response & Persistence: ")

    add_heading_2(doc, "3.2. Perancangan Basis Pengetahuan (Knowledge Vault)")
    add_p(doc, "Basis pengetahuan Luco dirancang dengan struktur berkas teks terbuka Markdown (.md) yang terorganisasi rapi di dalam direktori vault/. Format ini dipilih karena bersifat human-readable, mudah dikurasi, kompatibel dengan ekosistem Obsidian, dan mendukung pengindeksan metadata secara konsisten.")
    
    add_p(doc, "Struktur 7 Kategori Direktori Vault:", bold_prefix="Organisasi Direktori: ")
    add_bullet(doc, "Struktur kurikulum 140 SKS, Capaian Pembelajaran Lulusan (CPL), distribusi mata kuliah per semester, konversi nilai, dan prasyarat kelulusan.", bold_prefix="1. akademik/: ")
    add_bullet(doc, "Profil 33 dosen Informatika UNTAN, NIP 18 digit, alamat surel resmi, bidang keahlian (KBK), dan rekam jejak riset.", bold_prefix="2. dosen/: ")
    add_bullet(doc, "Laboratorium Rekayasa Perangkat Lunak, Sistem Cerdas & Robotika, serta Jaringan & Komputasi Awan beserta fasilitas dan peralatan.", bold_prefix="3. fasilitas-lab/: ")
    add_bullet(doc, "Himpunan Mahasiswa Informatika (HMIF), kegiatan organisasi, prestasi kompetisi, beasiswa, dan jejaring alumni (tracer study).", bold_prefix="4. kemahasiswaan/: ")
    add_bullet(doc, "Pedoman Kerja Praktik (KP), Seminar Proposal (Sempro), Sidang Tugas Akhir/Skripsi, serta alur penggunaan sistem SPOTA.", bold_prefix="5. kp-ta/: ")
    add_bullet(doc, "Visi, misi, tujuan, sejarah pendirian prodi, sertifikat akreditasi BAN-PT/LAM INFOKOM, dan struktur organisasi jurusan.", bold_prefix="6. profil/: ")
    add_bullet(doc, "26 berkas formulir dan pedoman resmi terpublikasi hasil ekstraksi repositori kampus Directus API.", bold_prefix="7. dokumen/: ")

    add_p(doc, "Setiap berkas Markdown dilengkapi metadata YAML Frontmatter terstandarisasi:")
    add_code_block(doc,
                   "---\n"
                   "judul: \"Pedoman Penulisan Skripsi Informatika UNTAN\"\n"
                   "kategori: \"kp-ta\"\n"
                   "slug: \"pedoman-skripsi-2022\"\n"
                   "sumber: \"SK Dekan FT UNTAN No. 124/UN22.1/AK/2022\"\n"
                   "terakhir_diperbarui: \"2026-06-04\"\n"
                   "berkas_asli: \"data/dokumen_raw/12_Pedoman_Penulisan_SKRIPSI_2022.pdf\"\n"
                   "url_asli: \"https://api.ifuntanhub.dev/assets/40608678-752d-4e9e-88b9-53e34360e200.pdf\"\n"
                   "---")

    add_heading_2(doc, "3.3. Perancangan Pipeline Ekstraksi 26 Dokumen Resmi (Directus API)")
    add_p(doc, "Untuk menjamin kelengkapan dan keabsahan dokumen regulasi yang menjadi rujukan mahasiswa, dirancang pipeline otomatis pengunduhan dan ekstraksi 26 berkas resmi dari portal Directus API prodi (https://api.ifuntanhub.dev/items/berkas):")
    
    add_bullet(doc, "Script scripts/fetch_and_convert_dokumen.py mengunduh 26 berkas fisik master asli (14 file PDF dan 12 file DOCX) dan menyimpannya ke data/dokumen_raw/.", bold_prefix="1. Pengunduhan Master Fisik: ")
    add_bullet(doc, "Untuk berkas PDF multi-halaman (seperti Pedoman Akademik 288 halaman, SOP KP, dan Pedoman Skripsi), digunakan modul PyMuPDF4LLM untuk mengekstrak teks, hierarki heading Markdown, dan struktur tabel numerik secara presisi.", bold_prefix="2. Ekstraksi PDF via PyMuPDF4LLM: ")
    add_bullet(doc, "Untuk berkas formulir administrasi Microsoft Word (.docx) seperti Form KP-IF-00 hingga IF-08, digunakan library Mammoth untuk mengekstrak teks terformat bersih tanpa tag XML Microsoft Office yang mengotori konteks prompt.", bold_prefix="3. Ekstraksi Word via Mammoth: ")
    add_bullet(doc, "Antarmuka chat dan drawer dokumen menyediakan akses ganda: mahasiswa dapat membaca teks naskah Markdown langsung di browser, atau mengunduh berkas biner fisik master asli bertanda tangan/berstempel melalui endpoint API /v1/dokumen/{slug}/raw.", bold_prefix="4. Paradigma Dual-Option Access: ")

    add_heading_2(doc, "3.4. Perancangan Upfront Deterministic Router (2-Tier Classification)")
    add_p(doc, "Upfront Router dirancang di src/luco/router.py untuk mencegah pemborosan komputasi LLM dan mencegah model berhalusinasi di luar ranah akademik. Router beroperasi dalam dua lapis (2-tier):")
    add_bullet(doc, "Mencocokkan pola regex untuk sapaan umum (halo, hai, pagi, siang, assalamualaikum) yang langsung dibalas template ramah Luco dalam 0 ms. Kueri saran/kemitraan langsung diarahkan ke alamat email sekretariat jurusan. Kueri yang memuat kata kunci prodi (PRODI_KEYWORDS) langsung diloloskan ke agen tanpa klasifikasi tambahan.", bold_prefix="Tier 1 — Heuristik & Regex Instan (0 ms): ")
    add_bullet(doc, "Jika kueri tidak dapat diputuskan oleh heuristik, prompt klasifikasi teroptimasi memandu model LLM ringan untuk mengelompokkan pesan ke dalam 4 kategori: IN_SCOPE, OUT_OF_SCOPE, CONTACT_REDIRECT, atau AMBIGUOUS_CLARIFICATION.", bold_prefix="Tier 2 — Semantic LLM Classifier: ")

    add_heading_2(doc, "3.5. Perancangan Komponen Agen & Alat Bantu (Tools)")
    add_p(doc, "Agen LlamaIndex di src/luco/agent.py dikonfigurasi sebagai FunctionAgent otonom yang dibekali 4 alat bantu khusus pada src/luco/tools.py:")
    
    tbl_tools = doc.add_table(rows=5, cols=3)
    col_w = [Inches(1.8), Inches(2.2), Inches(3.0)]
    alignments = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY]
    
    h_tools = ["Nama Tool", "Target Sumber Data", "Fungsi & Mekanisme Kerja"]
    for i, h in enumerate(h_tools):
        tbl_tools.rows[0].cells[i].paragraphs[0].text = h
        
    data_tools = [
        ("cari_profil_dosen", "vault/lookup.json", "Pencarian deterministik profil 33 dosen (nama lengkap, NIP 18 digit, email resmi, KBK). Menghilangkan 100% halusinasi angka."),
        ("telusuri_direktori_prodi", "OpenViking DB :1933 + IndoBERT-p1 :8001", "Pencarian kemiripan vektor semantik (kosinus) dan kata kunci BM25 untuk menemukan berkas panduan dan regulasi prodi yang relevan."),
        ("baca_dokumen_lengkap", "Berkas Markdown vault/", "Membaca teks naskah dokumen Markdown secara utuh dengan batas aman MAX_READ_CHARS = 12000 untuk mencegah context window overflow."),
        ("list_docs", "Tree Direktori vault/", "Menampilkan daftar berkas dan kategori panduan yang tersedia di vault ketika mahasiswa membutuhkan eksplorasi umum.")
    ]
    for r_idx, row_data in enumerate(data_tools, start=1):
        for c_idx, text in enumerate(row_data):
            tbl_tools.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl_tools, col_widths=col_w, alignments=alignments)

    add_heading_2(doc, "3.6. Perancangan Mesin Verifikasi Sitasi & Anti-Halusinasi")
    add_p(doc, "Untuk menjamin keterikatan data (groundedness), diimplementasikan komponen CitationsVerifier di src/luco/citations.py:")
    add_bullet(doc, "Setiap giliran pesan, kelas Recorder mencatat berkas dokumen apa saja yang dibaca oleh tool agen.", bold_prefix="1. Session Read Tracking: ")
    add_bullet(doc, r"Jawaban akhir agen dipindai menggunakan ekspresi reguler dengan negative lookbehind: (?<!!)\[([^\]]+)\]\(([^)\s]+)\) untuk mengekstrak seluruh hyperlink sitasi tanpa terkeliru dengan tag gambar markdown ![alt](url).", bold_prefix="2. Negative Lookbehind Regex: ")
    add_bullet(doc, "Setiap tautan yang diekstrak dicocokkan dengan daftar berkas yang benar-benar dibaca. Jika agen menyebutkan dokumen yang tidak pernah dibuka pada sesi tersebut, tautan ditandai sebagai unverified dan tidak dimunculkan sebagai chip rujukan resmi.", bold_prefix="3. Grounding Verification: ")

    add_heading_2(doc, "3.7. Perancangan Keamanan, Pertahanan Prompt Injection, & Rate Limiting")
    add_bullet(doc, "System prompt di src/luco/prompts.py menegaskan bahwa identitas Luco bersifat permanen, menolak pembongkaran system prompt/API key, menolak pembuatan tugas joki skripsi, dan menolak pengubahan persona (serangan DAN/jailbreak).", bold_prefix="1. Imutabilitas Peran Sistem: ")
    add_bullet(doc, "Fungsi pembaca berkas safe_rel() secara tegas memvalidasi path relatif dan melempar eksepsi ValueError jika ditemukan karakter traversal (../) yang mencoba keluar dari folder vault/.", bold_prefix="2. Directory Traversal Defense: ")
    add_bullet(doc, "Menggunakan algoritma sliding window token bucket yang membatasi RPM (Requests per Minute) dan TPM (Tokens per Minute) secara terisolasi per alamat IP/pengguna. Lonjakan request dari satu pengguna tidak akan mengorbankan pengguna lain.", bold_prefix="3. Sliding-Window Rate Limiter: ")

    add_heading_2(doc, "3.8. Perancangan Antarmuka Pengguna (UI/UX) & Drawer Riwayat")
    add_p(doc, "Antarmuka pengguna dibangun menggunakan React dan Tailwind CSS dengan pendekatan desain spasial yang ringan (weightless spatial design):")
    add_bullet(doc, "Drawer dokumen (DocumentDrawer.tsx) dilengkapi tumpukan navigasi (history stack) dengan tombol Previous (◀) dan Next (▶), indikator halaman berkas (misal: 1/3), serta pintasan keyboard (Alt + ←, Alt + →, Backspace) untuk menelusuri rujukan antar-dokumen dengan lancar.", bold_prefix="Document Drawer Navigasi Riwayat: ")
    add_bullet(doc, "Seluruh dokumen dan kutipan resmi yang memuat blok kode format internal (seperti ```text, ```format, atau ```mermaid) wajib dibungkus dengan 4-backtick (````) pada saat di-render agar teks dokumen tidak terpotong menjadi blok-blok terpisah di tampilan browser.", bold_prefix="Format Dokumen Anti-Putus (4-Backticks): ")

    add_heading_2(doc, "3.9. Perancangan Skema Basis Data Sesi (Entity Relationship Diagram)")
    add_p(doc, "Persistensi data sesi obrolan, riwayat pesan, sitasi yang terverifikasi, dan log audit token disimpan pada basis data relasional PostgreSQL 16 Alpine. Skema relasi antartabel digambarkan pada diagram ERD berikut:")

    erd_path = "docs/ERD_v1.png"
    if os.path.exists(erd_path):
        p_erd = doc.add_paragraph()
        p_erd.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_erd.paragraph_format.space_before = Pt(8)
        p_erd.paragraph_format.space_after = Pt(4)
        p_erd.add_run().add_picture(erd_path, width=Inches(5.5))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_c = p_cap.add_run("Gambar 3.2: Entity Relationship Diagram (ERD) Basis Data Sistem Luco")
        r_c.font.name = "Times New Roman"
        r_c.font.size = Pt(10)
        r_c.font.bold = True
        r_c.font.color.rgb = COLOR_NAVY

def add_chapter_4(doc):
    add_heading_1(doc, "BAB IV: IMPLEMENTASI SISTEM", page_break=True)
    
    add_heading_2(doc, "4.1. Lingkungan Implementasi & Stack Teknologi")
    add_p(doc, "Sistem Luco diimplementasikan pada lingkungan sistem operasi Linux menggunakan virtualisasi container Docker dan manajer paket modern Pixi v0.41.4. Rincian komponen teknologi tercantum pada tabel berikut:")
    
    tbl_stack = doc.add_table(rows=9, cols=3)
    col_w = [Inches(1.8), Inches(2.2), Inches(3.0)]
    alignments = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY]
    
    h_stack = ["Lapisan Arsitektur", "Komponen Teknologi", "Peran & Fungsi dalam Sistem Luco"]
    for i, h in enumerate(h_stack):
        tbl_stack.rows[0].cells[i].paragraphs[0].text = h
        
    data_stack = [
        ("Lingkungan & Paket", "Pixi v0.41.4 (Conda + Cargo)", "Manajemen lingkungan virtual Python 3.11/3.13 dan Node.js 20 secara reproducible lintas sistem operasi."),
        ("Backend Web Server", "FastAPI v0.115 + Uvicorn", "Penyedia endpoint REST API berkecepatan tinggi, validasi skema Pydantic v2, dan SSE streaming."),
        ("Framework Penalaran", "LlamaIndex Core v0.12", "Implementasi FunctionAgent, FunctionTool, dan orkestrasi pemanggilan ReAct multi-step tools."),
        ("Database Vektor", "OpenViking Docker (:1933)", "Penyimpanan dan penelusuran dokumen hierarkis berbasis hybrid dense vector + leksikal BM25."),
        ("Mikroservis Embedding", "IndoBERT-Base-p1 Docker (:8001)", "Model transformer 124,5M parameter, 768 dimensi vektor kalimat, inferensi rata-rata 66,58 ms di CPU."),
        ("Database Relasional", "PostgreSQL 16 Alpine (:5432)", "Persistensi data sesi UUIDv4, riwayat obrolan multi-turn, jejak audit token, dan rating feedback."),
        ("Gateway LLM Proxy", "Antigravity Proxy (:3000)", "Reverse proxy protokol OpenAI-compatible dengan failover cerdas ke Google Gemini 2.5 Flash."),
        ("Frontend Web SPA", "React 18 + Vite 6 + Tailwind", "Antarmuka obrolan responsif, drawer dokumen riwayat penjelajahan, dan visualisasi status live.")
    ]
    for r_idx, row_data in enumerate(data_stack, start=1):
        for c_idx, text in enumerate(row_data):
            tbl_stack.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl_stack, col_widths=col_w, alignments=alignments)

    add_heading_2(doc, "4.2. Implementasi Backend & Agen Cerdas (src/luco/)")
    add_p(doc, "Modul backend dibangun dengan prinsip arsitektur modular di direktori src/luco/:")
    add_bullet(doc, "src/luco/agent.py: Menginisialisasi FunctionAgent LlamaIndex, membatasi riwayat memori percakapan pada 6 pesan terakhir (recent_history = history[-6:]), dan mengimplementasikan mekanisme ResilientTransport untuk menangani kegagalan unmarshal chunk SSE.", bold_prefix="1. Modul Agen & Transport: ")
    add_bullet(doc, "src/luco/router.py: Mengimplementasikan logika pemilahan pesan dua tingkat (Tier 1 heuristik regex dan Tier 2 LLM classifier).", bold_prefix="2. Modul Perutean Kueri: ")
    add_bullet(doc, "src/luco/backends.py: Menyediakan abstraksi antarmuka seragam (find, read, ls) untuk VikingBackend dan LocalBackend sebagai fail-safe.", bold_prefix="3. Modul Abstraksi Backend: ")
    add_bullet(doc, "src/luco/lookup.py: Memuat data 33 profil dosen ke memori hash table dan menormalisasi sapaan gelar (Dr., Prof., Ir., S.Kom., M.Cs.) untuk pencarian 100% presisi.", bold_prefix="4. Modul Lookup Deterministik: ")
    add_bullet(doc, "src/luco/citations.py: Memeriksa dan memvalidasi keabsahan sitasi dokumen menggunakan ekspresi reguler negative lookbehind.", bold_prefix="5. Modul Verifikasi Sitasi: ")
    add_bullet(doc, "src/luco/monitoring.py: Menghitung konsumsi token dan estimasi biaya operasional dalam USD dan IDR secara real-time.", bold_prefix="6. Modul Audit & Monitoring: ")

    add_heading_2(doc, "4.3. Implementasi Mikroservis Embedding IndoBERT")
    add_p(doc, "Mikroservis embedding berjalan di dalam kontainer Docker terisolasi luco-indobert pada port 8001:")
    add_bullet(doc, "Menggunakan bobot model transformer indobenchmark/indobert-base-p1 seberat 498 MB dari Hugging Face Hub.", bold_prefix="• ")
    add_bullet(doc, "Menyediakan endpoint POST /embed yang menerima daftar string teks dan mengembalikan matriks vektor normalisasi L2 berdimensi 768.", bold_prefix="• ")
    add_bullet(doc, "Waktu inferensi CPU rata-rata tercatat 66,58 ms per batch teks, membuktikan kelayakan operasional tanpa memerlukan kartu grafis (GPU) mahal.", bold_prefix="• ")

    add_heading_2(doc, "4.4. Implementasi Penyimpanan Sesi & Basis Data PostgreSQL 16")
    add_p(doc, "Skema basis data diinisialisasi melalui src/luco/schema.sql dengan tiga tabel utama:")
    add_bullet(doc, "Menyimpan session_id (tipe UUIDv4), user_id, status aktif, dan stempel waktu pembuatan sesi.", bold_prefix="1. Tabel sessions: ")
    add_bullet(doc, "Menyimpan seluruh giliran pesan (user dan assistant), teks jawaban, sitasi yang terverifikasi, serta riwayat pemanggilan tool (trajectory).", bold_prefix="2. Tabel messages: ")
    add_bullet(doc, "Mencatat penggunaan token input, token output, total latensi inferensi, dan estimasi biaya operasional per request.", bold_prefix="3. Tabel audit_logs: ")

    add_heading_2(doc, "4.5. Implementasi Antarmuka Web SPA")
    add_p(doc, "Frontend diimplementasikan menggunakan React v18, Vite v6, TypeScript, dan Tailwind CSS:")
    add_bullet(doc, "Memungkinkan pengguna beralih antara 3 mode inferensi: IndoBERT + OpenViking (ikon Layers), OpenViking Cepat (ikon Zap), dan Direct LLM (ikon MessageSquare).", bold_prefix="Mode Selector Dinamis: ")
    add_bullet(doc, "Komponen DocumentDrawer.tsx menampilkan naskah Markdown rujukan secara interaktif, dilengkapi tombol Previous & Next untuk riwayat penelusuran, tombol salin teks naskah, serta tombol ekspor berkas.", bold_prefix="Document Drawer Interaktif: ")
    add_bullet(doc, "Menyajikan katalog 26 formulir dan berkas regulasi resmi dengan pilihan pratinjau teks naskah atau unduh langsung berkas biner master asli.", bold_prefix="Katalog Berkas Resmi: ")

    add_heading_2(doc, "4.6. Standar Format Dokumen Markdown Anti-Putus (4-Backticks)")
    add_p(doc, "Untuk mengatasi anomali visual di antarmuka obrolan di mana naskah dokumen yang memuat blok kode internal (seperti ```format, ```text, atau ```mermaid) terpecah menjadi boks-boks terpotong di browser, sistem prompt agen dan script ekstraksi mewajibkan pembungkus 4-backtick (````) pada awal dan akhir naskah:")
    
    add_code_block(doc,
                   "````markdown\n"
                   "# Form Permohonan Kerja Praktik (KP-IF-01)\n"
                   "Berikut adalah format isian formulir resmi:\n"
                   "```text\n"
                   "Nama Mahasiswa : [Nama Lengkap]\n"
                   "NIM            : [D1041XXXXX]\n"
                   "Instansi KP    : [Nama Perusahaan / Dinas]\n"
                   "```\n"
                   "Silakan isi formulir di atas dan serahkan ke sekretariat jurusan.\n"
                   "````")
    add_p(doc, "Penerapan standar 4-backtick ini berhasil menghilangkan 100% bug tampilan naskah terputus di antarmuka obrolan pengguna.")

print("Part 2 ready.")
