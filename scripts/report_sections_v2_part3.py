"""
Bagian 3 Laporan Tugas Besar AI 2026 (Sistematika Resmi 9 Poin):
- 8. Etika dan Keterbatasan: Potensi Bias, Privasi, Risiko Kesalahan, serta Penggunaan Generative AI
- 9. Kesimpulan dan Saran Pengembangan
- DAFTAR PUSTAKA
- LAMPIRAN (Lampiran 1, 2, 3)
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from scripts.build_full_report import (
    COLOR_NAVY, COLOR_STEEL, COLOR_CHARCOAL, COLOR_MUTED,
    add_heading_1, add_heading_2, add_heading_3, add_p, add_bullet,
    add_callout, add_code_block, format_styled_table
)

def add_section_8(doc):
    add_heading_1(doc, "8. ETIKA DAN KETERBATASAN", page_break=True)
    
    add_heading_2(doc, "8.1. Potensi Bias Algoritmik & Budaya Bahasa")
    add_p(doc, "Penerapan model kecerdasan buatan berbasis Large Language Models (LLM) pada lingkungan institusi perguruan tinggi memiliki tantangan inheren terkait bias algoritmik dan representasi bahasa:")
    add_bullet(doc, "Model LLM komersial global (seperti keluarga GPT dan Gemini) dilatih pada dominasi korpus bahasa Inggris dan teks barat. Ketika memproses terminologi khas perguruan tinggi Indonesia (seperti akronim KP, Sempro, SPOTA, Yudisium, KBK, dan Matrikulasi), model sering kali mengalami bias pemahaman semantik atau salah menginterpretasikan singkatan resmi tersebut.", bold_prefix="1. Bias Korpus Bahasa: ")
    add_bullet(doc, "Untuk memitigasi bias budaya dan bahasa tersebut, Luco mengadopsi model representasi vektor transformer bahasa Indonesia indobenchmark/indobert-base-p1 yang dilatih secara khusus pada korpus Indo4B (~3,6 miliar kata ragam formal dan percakapan Indonesia). Langkah ini memastikan akronim akademik lokal diakui secara presisi dalam ruang vektor semantik.", bold_prefix="2. Mitigasi via Dense Embedding Lokal: ")
    add_bullet(doc, "Prompt instruksi agen (src/luco/prompts.py) dirancang dengan prinsip netralitas institusional, mencegah keluaran teks yang memihak, menghakimi, atau mendiskriminasi berdasarkan latar belakang gender, agama, ras, maupun status akademik mahasiswa.", bold_prefix="3. Netralitas Komunikasi Institusional: ")

    add_heading_2(doc, "8.2. Privasi Data & Perlindungan Informasi Sivitas Akademika")
    add_p(doc, "Kepatuhan terhadap regulasi privasi data (mengacu pada prinsip UU No. 27 Tahun 2022 tentang Perlindungan Data Pribadi) diterapkan secara ketat dalam rancang bangun sistem Luco:")
    add_bullet(doc, "Sistem Luco sengaja TIDAK dihubungkan secara langsung ke basis data transkrip nilai individual mahasiswa pada SIAKAD UNTAN. Hal ini bertujuan melindungi hak privasi mahasiswa dari potensi kebocoran data akademik pribadi atau akses tanpa hak oleh pihak lain melalui antarmuka obrolan terbuka.", bold_prefix="1. Isolasi Data Nilai Sensitif SIAKAD: ")
    add_bullet(doc, "Informasi kontak dosen yang disajikan sistem dibatasi secara ketat pada data profil resmi universitas yang bersifat publik (Nomor Induk Pegawai 18 digit, alamat surel institusi berdomain @untan.ac.id, dan bidang keahlian). Sistem secara eksplisit menolak menyebarkan nomor telepon pribadi, alamat rumah, atau data perbankan dosen.", bold_prefix="2. Sanitasi Data Kontak Dosen: ")
    add_bullet(doc, "Setiap percakapan diidentifikasi menggunakan kunci acak sesi UUIDv4. Data riwayat obrolan dan log audit token yang tersimpan di PostgreSQL tidak memuat alamat fisik pengguna dan hanya digunakan untuk keperluan perbaikan performa sistem.", bold_prefix="3. Anonimisasi Sesi Pengguna: ")

    add_heading_2(doc, "8.3. Risiko Kesalahan & Strategi Halusinasi Nol (Zero-Hallucination)")
    add_p(doc, "Dalam konteks administrasi akademik, kesalahan informasi faktual dapat menimbulkan dampak kerugian fatal bagi mahasiswa—seperti kegagalan mendaftar seminar proposal akibat salah informasi batas minimal SKS, atau kesalahan mengirimkan berkas akibat salah format formulir. Oleh karena itu, Luco menerapkan tiga strategi pertahanan anti-halusinasi berlapis:")
    add_bullet(doc, "Data-data administratif kritis yang tidak boleh meleset satu digit pun (seperti NIP 18 digit dosen dan nama pejabat prodi) tidak dipercayakan pada penarikan probabilistik LLM, melainkan dikunci dalam berkas hash JSON deterministik vault/lookup.json melalui fungsi cari_profil_dosen.", bold_prefix="1. Deterministic Lookup Table: ")
    add_bullet(doc, "Instruksi sistem mewajibkan agen untuk bersikap jujur dan menolak spekulasi. Jika suatu informasi tidak tercantum pada 104 dokumen resmi di dalam vault, Luco diinstruksikan untuk menyatakan tidak tahu dan mengarahkan mahasiswa ke kontak resmi sekretariat jurusan.", bold_prefix="2. Honest Rejection Fallback: ")
    add_bullet(doc, "Seluruh tautan dokumen yang dikeluarkan agen diverifikasi secara programatik oleh CitationsVerifier. Jika model mencoba mengarang tautan berkas yang tidak pernah dibaca, tautan tersebut ditolak dan tidak dimunculkan sebagai chip referensi.", bold_prefix="3. Automated Citation Grounding: ")

    add_heading_2(doc, "8.4. Penggunaan Generative AI Secara Bertanggung Jawab (Responsible AI & Anti-Joki)")
    add_p(doc, "Penerapan kecerdasan buatan generatif dalam dunia pendidikan harus menjunjung tinggi integritas akademik dan etika pembelajaran:")
    add_bullet(doc, "Asisten Luco secara tegas memblokir permintaan joki akademik, seperti pembuatan naskah skripsi utuh, penulisan kode tugas akhir secara curang, atau pengerjaan soal ujian mata kuliah. Jika diminta melakukan hal tersebut, agen memberikan penolakan sopan dan mengarahkan mahasiswa untuk berkonsultasi langsung dengan Dosen Pembimbing Akademik (PA).", bold_prefix="1. Pencegahan Joki Akademik: ")
    add_bullet(doc, "Sistem menyediakan transparansi penuh di mana mahasiswa dapat menelusuri naskah Markdown rujukan dan mengunduh berkas biner master asli bertanda tangan/berstempel resmi dari portal Directus kampus.", bold_prefix="2. Transparansi & Akuntabilitas Sumber: ")
    add_bullet(doc, "Model LLM dalam sistem Luco difungsikan secara ketat sebagai perangkum informasi terikat fakta (grounded retrieval synthesizer), bukan sebagai pembuat fakta fiktif baru (creative writer).", bold_prefix="3. Batasan Fungsional AI: ")

    add_heading_2(doc, "8.5. Keterbatasan Teknis Sistem")
    add_p(doc, "Meskipun telah membuktikan keandalan tinggi pada pengujian empiris, sistem Luco memiliki beberapa keterbatasan teknis yang perlu diperhatikan:")
    add_bullet(doc, "Penambahan SK Dekan baru, revisi kalender akademik, atau perubahan kurikulum saat ini masih memerlukan eksekusi pipeline ekstraksi dan pengindeksan manual (pixi run ingest) oleh administrator repositori.", bold_prefix="1. Pembaruan Dokumen Masih Semi-Otomatis: ")
    add_bullet(doc, "Sistem saat ini baru mendukung masukan teks melalui web dan CLI, belum memiliki antarmuka multimodal audio (speech-to-text / text-to-speech) untuk melayani pengguna tunanetra secara penuh.", bold_prefix="2. Ketiadaan Antarmuka Suara: ")
    add_bullet(doc, "Pada pertanyaan penalaran multi-dokumen yang sangat kompleks, latensi respon P95 masih dapat mencapai 22 detik ketika koneksi jaringan proxy sedang mengalami antrean beban puncak.", bold_prefix="3. Fluktuasi Latensi Kueri Multi-File: ")

def add_section_9(doc):
    add_heading_1(doc, "9. KESIMPULAN DAN SARAN PENGEMBANGAN", page_break=True)
    
    add_heading_2(doc, "9.1. Kesimpulan")
    add_p(doc, "Berdasarkan keseluruhan tahapan perancangan arsitektur, implementasi perangkat lunak, dan evaluasi empiris kuantitatif yang telah diselesaikan pada tugas besar ini, dapat diambil kesimpulan utama sebagai berikut:")
    add_bullet(doc, "Sistem asisten cerdas Luco berhasil dibangun menggunakan arsitektur Hybrid Agentic RAG yang menggabungkan penalaran multi-step LlamaIndex FunctionAgent, basis data vektor hierarkis OpenViking, mikroservis representasi kalimat IndoBERT-Base-p1 (768 dimensi), pencarian deterministik data presisi lookup.json, serta gerbang penyaring kueri upfront router 2-tier.", bold_prefix="1. ")
    add_bullet(doc, "Pengujian empiris membuktikan bahwa model indobenchmark/indobert-base-p1 unggul secara mutlak atas indolem/indobert-base-uncased dengan Top-1 Accuracy 80,0% vs 40,0%, Top-3 Recall 100,0% vs 60,0%, dan margin separasi semantik rata-rata +0,2657 vs +0,0373, serta terbukti kebal dari fenomena representation collapse yang menimpa korpus berita formal IndoLEM.", bold_prefix="2. ")
    add_bullet(doc, "Mekanisme pencarian deterministik lookup.json terbukti sukses mewujudkan target zero-hallucination (akurasi 100%) pada data administratif kritis (NIP 18 digit dosen, surel resmi, dan pembagian KBK), memecahkan kelemahan fatal model LLM publik generik.", bold_prefix="3. ")
    add_bullet(doc, "Pada pengujian percakapan panjang multi-turn (6 giliran obrolan), arsitektur Luco berhasil menghemat 97,76% token kumulatif (44,6x lebih hemat) dan 96,66% biaya komputasi dibandingkan metode brute-force context stuffing, sekaligus membuktikan keunggulan dalam mengatasi fenomena Lost-in-the-Middle.", bold_prefix="4. ")
    add_bullet(doc, "Seluruh suite pengujian otomatis (78 pengujian Pytest pada 13 modul sistem) berhasil lulus 100% dalam waktu 5,03 detik, sementara implementasi format pembungkus 4-backtick (````) berhasil mengatasi anomali keterputusan naskah Markdown di browser pengguna.", bold_prefix="5. ")
    add_bullet(doc, "Dengan estimasi biaya operasional hanya Rp 3,37 per interaksi percakapan, sistem Luco terbukti sangat ekonomis dan layak dioperasikan secara berkelanjutan di lingkungan Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura.", bold_prefix="6. ")

    add_heading_2(doc, "9.2. Saran Pengembangan Lanjutan (Future Work)")
    add_p(doc, "Untuk meningkatkan kapabilitas dan jangkauan layanan sistem Luco pada fase pengembangan pasca-tugas besar, direkomendasikan beberapa arah inovasi lanjutan:")
    add_bullet(doc, "Mengadopsi basis data vektor terdistribusi berskala enterprise (seperti Qdrant atau Milvus terkluster) untuk menampung repositori puluhan ribu naskah skripsi dan laporan kerja praktik alumni Informatika UNTAN secara lengkap.", bold_prefix="1. Migrasi ke Basis Data Vektor Terdistribusi: ")
    add_bullet(doc, "Mengintegrasikan model Speech-to-Text bahasa Indonesia (seperti OpenAI Whisper fine-tuned Indo) dan model Text-to-Speech natural untuk memfasilitasi asisten suara interaktif ramah disabilitas netra di lobi gedung perkuliahan.", bold_prefix="2. Pengembangan Antarmuka Suara Interaktif (Voice Assistant): ")
    add_bullet(doc, "Membangun basis data graf (Neo4j) yang memetakan keterkaitan antara topik draft usulan tugas akhir mahasiswa dengan keahlian riset dan riwayat publikasi dosen secara otomatis.", bold_prefix="3. Pembangunan Knowledge Graph Kepakaran Dosen: ")
    add_bullet(doc, "Mengintegrasikan otentikasi resmi kampus (OAuth2/SAML UNTAN) dengan proteksi data bertingkat agar mahasiswa dapat mengecek kemajuan akademik secara terpersonalisasi dengan aman.", bold_prefix="4. Integrasi Single Sign-On (SSO) Terpusat: ")

def add_references_v2(doc):
    add_heading_1(doc, "DAFTAR PUSTAKA", page_break=True)
    
    refs = [
        "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. arXiv preprint arXiv:1810.04805.",
        "Koto, F., Rahimi, A., Lau, J. H., & Baldwin, T. (2020). IndoLEM and IndoBERT: A Benchmark Dataset and Pre-trained Language Model for Indonesian NLP. Proceedings of the 28th International Conference on Computational Linguistics (COLING 2020), 757–770.",
        "Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W. T., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Advances in Neural Information Processing Systems (NeurIPS 2020), 33, 9459–9474.",
        "Liu, J. (2023). LlamaIndex: Data Framework for LLM Applications. GitHub Repository: https://github.com/run-llama/llama_index.",
        "Program Studi S-1 Informatika Universitas Tanjungpura. (2022). Buku Panduan Akademik dan Kurikulum Program Studi Informatika Fakultas Teknik Universitas Tanjungpura 2022–2026. Pontianak: FT UNTAN.",
        "Program Studi S-1 Informatika Universitas Tanjungpura. (2022). Standar Operasional Prosedur (SOP) Kerja Praktik dan Tugas Akhir Mahasiswa. Pontianak: FT UNTAN.",
        "Republik Indonesia. (2022). Undang-Undang Republik Indonesia Nomor 27 Tahun 2022 tentang Perlindungan Data Pribadi. Lembaran Negara Republik Indonesia Tahun 2022 Nomor 196.",
        "Wilie, B., Vincentio, K., Winata, G. I., Cahyawijaya, S., Li, X., Lim, Z. Y., Soleman, S., Mahendra, R., Pascual, P., Zhang, C., & Purwarianti, A. (2020). IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding. Proceedings of the 1st Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics (AACL/IJCNLP 2020), 843–860."
    ]
    for idx, ref in enumerate(refs, start=1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        r_num = p.add_run(f"[{idx}] ")
        r_num.font.name = "Times New Roman"
        r_num.font.bold = True
        r_text = p.add_run(ref)
        r_text.font.name = "Times New Roman"
        r_text.font.size = Pt(10.5)

def add_appendices_v2(doc):
    add_heading_1(doc, "LAMPIRAN", page_break=True)
    
    add_heading_2(doc, "Lampiran 1: Rekapitulasi Eksekusi Pytest Lengkap (78 Skenario Uji)")
    add_p(doc, "Log eksekusi otomatis pengujian unit dan integrasi Pytest tersimpan pada berkas docs/laporan/raw/pytest_report.txt. Seluruh 78 skenario terbukti lulus 100% pada platform Linux Python 3.13:")
    add_code_block(doc,
                   "collected 78 items\n"
                   "tests/test_agent.py::test_ask_in_scope PASSED\n"
                   "tests/test_agent.py::test_ask_out_of_scope_fast_reject PASSED\n"
                   "tests/test_agent.py::test_agent_fallback_on_llm_error PASSED\n"
                   "tests/test_agent.py::test_agent_clarification_mode PASSED\n"
                   "tests/test_agent.py::test_antislop_filter PASSED\n"
                   "tests/test_agent.py::test_anti_prompt_injection PASSED\n"
                   "tests/test_agent.py::test_four_backticks_formatting PASSED\n"
                   "tests/test_api_contract.py::test_health_endpoint PASSED\n"
                   "tests/test_api_contract.py::test_chat_completions_contract PASSED\n"
                   "tests/test_api_contract.py::test_dokumen_katalog_endpoint PASSED\n"
                   "tests/test_api_contract.py::test_dokumen_raw_download PASSED\n"
                   "tests/test_api_contract.py::test_dokumen_export_markdown PASSED\n"
                   "tests/test_api_contract.py::test_feedback_endpoint PASSED\n"
                   "tests/test_auth.py::test_password_hashing PASSED\n"
                   "tests/test_auth.py::test_jwt_creation_and_verify PASSED\n"
                   "tests/test_backends.py::test_viking_backend_find PASSED\n"
                   "tests/test_backends.py::test_local_backend_equivalence PASSED\n"
                   "tests/test_lookup.py::test_profil_dosen_by_name PASSED\n"
                   "tests/test_lookup.py::test_profil_dosen_nip_exact_18_digits PASSED\n"
                   "tests/test_monitoring.py::test_token_counting PASSED\n"
                   "tests/test_monitoring.py::test_cost_estimation PASSED\n"
                   "tests/test_ratelimit.py::test_sliding_window_rpm PASSED\n"
                   "tests/test_ratelimit.py::test_sliding_window_tpm PASSED\n"
                   "tests/test_router.py::test_heuristic_check_greetings PASSED\n"
                   "tests/test_router.py::test_semantic_routing_in_scope PASSED\n"
                   "tests/test_sessions_and_db.py::test_session_lifecycle PASSED\n"
                   "tests/test_viking_live.py::test_openviking_connection PASSED\n"
                   "[... 78 passed in 5.03s ...]")

    add_heading_2(doc, "Lampiran 2: Katalog 26 Berkas Resmi Directus (vault/dokumen/)")
    add_p(doc, "Daftar 26 berkas formulir dan pedoman resmi Program Studi S-1 Informatika UNTAN yang tersedia dalam format ganda (naskah Markdown interaktif dan berkas master biner asli berstempel):")
    
    tbl_dok = doc.add_table(rows=27, cols=4)
    col_w = [Inches(0.5), Inches(3.2), Inches(1.3), Inches(1.8)]
    alignments = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT]
    
    h_dok = ["No", "Nama Berkas Dokumen Resmi", "Format Asli", "Kategori & Keterangan"]
    for i, h in enumerate(h_dok):
        tbl_dok.rows[0].cells[i].paragraphs[0].text = h
        
    katalog = [
        ("1", "01-sop-kerja-praktek.md", "PDF", "SOP Kerja Praktik Mahasiswa"),
        ("2", "02-panduan-penulisan-proposal-kerja-praktek.md", "DOCX", "Panduan Proposal Kerja Praktik"),
        ("3", "03-panduan-penulisan-laporan-kerja-praktek.md", "DOCX", "Panduan Laporan Kerja Praktik"),
        ("4", "04-formulir-kerja-praktek-if-01.md", "DOCX", "Formulir Pendaftaran KP (IF-01)"),
        ("5", "05-formulir-kerja-praktek-if-00.md", "DOCX", "Form Surat Pengantar Instansi (IF-00)"),
        ("6", "06-formulir-kerja-praktek-if-05.md", "DOCX", "Lembar Asistensi Bimbingan KP (IF-05)"),
        ("7", "07-pedoman-akademik-untan-20232024.md", "PDF (288 Hal)", "Buku Pedoman Akademik Universitas"),
        ("8", "08-formulir-kerja-praktek-if-06.md", "DOCX", "Formulir Revisi Laporan KP (IF-06)"),
        ("9", "09-formulir-kerja-praktek-if-07.md", "DOCX", "Form Penilaian Seminar KP (IF-07)"),
        ("10", "10-formulir-kerja-praktek-if-08.md", "DOCX", "Form Penilaian Pembimbing Lapangan"),
        ("11", "11-pedoman-penulisan-proposal-skripsi-2022.md", "PDF", "Pedoman Penulisan Proposal Skripsi"),
        ("12", "12-pedoman-penulisan-skripsi-2022.md", "PDF", "Pedoman Penulisan Naskah Skripsi"),
        ("13", "13-tamplate-proposal-skripsi.md", "PDF / DOCX", "Template Resmi Proposal Skripsi"),
        ("14", "14-tamplate-skripsi.md", "PDF / DOCX", "Template Resmi Naskah Skripsi"),
        ("15", "15-formulir-pengajuan-draft-proposal-ta.md", "DOCX", "Formulir Pengajuan Draft Proposal TA"),
        ("16", "16-format-draft-usulan-topik-ta.md", "DOCX", "Format Draft Usulan Topik Skripsi"),
        ("17", "17-prosedur-pengajuan-draft-proposal-skripsi.md", "DOCX", "SOP Pengajuan Draft Proposal Skripsi"),
        ("18", "18-prosedur-pengajuan-draft-proposal-skripsi.md", "DOCX", "Alur Pengajuan Draft via SPOTA"),
        ("19", "19-prosedur-pengesahan-skripsi-dan-wisuda.md", "PDF", "Prosedur Pengesahan & Daftar Wisuda"),
        ("20", "20-kalender-akademik-20252026.md", "PDF", "Kalender Akademik UNTAN 2025/2026"),
        ("21", "21-kalender-akademik-ta-20262027.md", "PDF", "Kalender Akademik UNTAN 2026/2027"),
        ("22", "22-akreditasi-informatika-tahun-2017-2022.md", "PDF", "Sertifikat Akreditasi BAN-PT 2017"),
        ("23", "23-akreditasi-informatika-tahun-2013-2018.md", "PDF", "Sertifikat Akreditasi BAN-PT 2013"),
        ("24", "24-akreditasi-informatika-tahun-2006-2011.md", "PDF", "Sertifikat Akreditasi BAN-PT 2006"),
        ("25", "25-akreditasi-informatika-tahun-2022-2027.md", "PDF", "Sertifikat Akreditasi LAM INFOKOM (B)"),
        ("26", "26-sertifikat-keanggotaan-aptikom-2027.md", "PDF", "Sertifikat Anggota Resmi APTIKOM")
    ]
    for r_idx, row_data in enumerate(katalog, start=1):
        for c_idx, text in enumerate(row_data):
            tbl_dok.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl_dok, col_widths=col_w, alignments=alignments)

    add_heading_2(doc, "Lampiran 3: Panduan Eksekusi Sistem & Replikasi Lingkungan")
    add_p(doc, "Repositori proyek dilengkapi automasi task berbasis Pixi. Perintah-perintah operasional utama meliputi:")
    add_code_block(doc,
                   "# 1. Pemasangan dependensi lingkungan lintas sistem\n"
                   "pixi install\n\n"
                   "# 2. Menjalankan seluruh stack layanan (Proxy + OpenViking + PostgreSQL + Luco)\n"
                   "pixi run up\n\n"
                   "# 3. Ekstraksi dan pengindeksan dokumen resmi ke database vektor\n"
                   "pixi run ingest\n\n"
                   "# 4. Eksekusi 78 automated test suite Pytest\n"
                   "pixi run test\n\n"
                   "# 5. Menjalankan benchmark komparasi 3 mode inferensi\n"
                   "pixi run benchmark-modes\n\n"
                   "# 6. Menjalankan benchmark komparasi multi-turn vs context stuffing\n"
                   "pixi run benchmark-context\n\n"
                   "# 7. Menjalankan server backend API produksi pada port 8000\n"
                   "pixi run serve\n\n"
                   "# 8. Menjalankan antarmuka obrolan CLI REPL interaktif\n"
                   "pixi run chat")

print("Part 3 V2 ready.")
