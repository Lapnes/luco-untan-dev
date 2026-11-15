"""
Bagian 1 Laporan Tugas Besar AI 2026 (Sistematika Resmi 9 Poin):
- Lembar Konsultasi & Ringkasan Eksekutif
- Kata Pengantar & Daftar Isi
- 1. Judul Proyek dan Identitas Anggota Kelompok
- 2. Pendahuluan: Latar Belakang, Rumusan Masalah, Tujuan, dan Manfaat
- 3. Landasan Teori Singkat: Konsep dan Metode AI yang Digunakan
- 4. Data: Sumber Data, Deskripsi, dan Tahapan Preprocessing
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

def add_front_matter_v2(doc):
    # 1. Lembar Konsultasi
    add_heading_1(doc, "LEMBAR KONSULTASI & KESIAPAN TUGAS BESAR", page_break=True)
    add_p(doc, "Mata Kuliah: Kecerdasan Buatan (AI) | Program Studi S-1 Informatika Universitas Tanjungpura", bold_prefix="Identitas Verifikasi: ")
    add_p(doc, "Lembar ini merangkum formulir evaluasi kesiapan kelompok, topik riset, metode AI yang diterapkan, dataset acuan, prototipe fungsional, dan matriks pengujian yang telah disetujui dalam sesi konsultasi tugas besar.")

    tbl = doc.add_table(rows=9, cols=3)
    col_w = [Inches(1.5), Inches(2.3), Inches(3.2)]
    alignments = [WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY]
    
    headers = ["Aspek Verifikasi", "Pertanyaan / Parameter Evaluasi", "Uraian Implementasi Kelompok Luco"]
    for i, h in enumerate(headers):
        tbl.rows[0].cells[i].paragraphs[0].text = h
        
    data = [
        ("Permasalahan", 
         "Masalah apa yang ingin diselesaikan? Mengapa relevan menggunakan AI?",
         "Informasi akademik Prodi Informatika UNTAN (alur KP, syarat TA/skripsi, kurikulum 140 SKS, dan profil 33 dosen) tersebar di berbagai dokumen terpisah. Mahasiswa kesulitan mencari regulasi valid. LLM publik generik tidak mengetahui konteks lokal dan rentan halusinasi fatal (mengarang NIP 18 digit dosen dan aturan SKS). Pendekatan naive RAG membebani context window dengan teks tidak relevan. Oleh karena itu, dibangun Hybrid Agentic RAG dengan verifikasi sitasi dan lookup deterministik."),
        
        ("Tujuan",
         "Apa yang ingin dihasilkan oleh sistem?",
         "Membangun chatbot asisten cerdas (Luco) berbasis web dan REST API yang mampu menjawab pertanyaan seputar Informatika UNTAN dengan menyertakan tautan sumber berkas vault, menyatakan 'tidak tahu' jika informasi tidak tercantum di dokumen resmi, menolak kueri di luar lingkup akademik via Upfront Router, dan mengarahkan pengguna ke kontak resmi sekretariat jurusan."),
        
        ("Metode AI",
         "Mengapa memilih metode AI tersebut?",
         "Memilih arsitektur Hybrid Agentic RAG menggunakan LlamaIndex FunctionAgent yang dipadukan dengan database vektor hierarkis OpenViking dan model dense embedding bahasa Indonesia IndoBERT (768 dimensi). Pendekatan ini memungkinkan pembaruan regulasi kampus tanpa perlu fine-tuning ulang model, serta memberikan kapabilitas multi-step reasoning untuk memvalidasi isi dokumen sebelum menjawab."),
        
        ("Dataset & Sumber Data",
         "Data apa yang digunakan dan dari mana sumbernya?",
         "Arsip dokumen resmi Prodi Informatika UNTAN, mencakup 26 berkas formulir dan pedoman resmi (14 berkas PDF dan 12 berkas DOCX) yang diekstrak langsung dari repositori Directus API kampus, 104 naskah Markdown terstruktur pada Obsidian Knowledge Vault, serta database profil 33 dosen (NIP, email, kelompok keahlian) yang diverifikasi via crawling OpenAlex."),
         
        ("Ketersediaan & Kualitas",
         "Apakah dataset sudah diperoleh, dapat dibuka, dan boleh digunakan?",
         "Seluruh dokumen bersifat publik untuk keperluan akademik internal kampus. Teks PDF dan DOCX berhasil diekstrak 100% menggunakan pipeline PyMuPDF4LLM dan Mammoth, menghasilkan naskah Markdown rapi dengan struktur heading H1-H3 dan tabel utuh."),
         
        ("Input-Output",
         "Apa masukan pengguna dan keluaran sistem?",
         "Input: Kueri teks percakapan pengguna melalui antarmuka web SPA. Output: Jawaban komprehensif bergaya komunikatif asisten Luco dengan kutipan chip dokumen resmi, tautan naskah Markdown interaktif, dan tombol unduh berkas master fisik asli berstempel."),
         
        ("Platform & Stack",
         "Bahasa pemrograman, framework, dan lingkungan eksekusi?",
         "Backend berbasis Python 3.11/3.13, FastAPI, Uvicorn, LlamaIndex Core v0.12, dan OpenViking SDK. Frontend berbasis React v18, TypeScript, Vite v6, Tailwind CSS, dan Lucide Icons. Layanan terorkestrasi dalam multi-container Docker Compose (Proxy, OpenViking, IndoBERT, PostgreSQL, dan Luco Backend)."),
         
        ("Metodologi Evaluasi",
         "Bagaimana membuktikan sistem bekerja dengan baik?",
         "Evaluasi empiris multi-tingkat: (1) Pytest automated test suite 78 skenario pada 13 modul (100% lulus); (2) Benchmark dense embedding 3 model transformer IndoBERT (Top-1, Top-3, dan margin separasi); (3) Benchmark komparasi 3 mode inferensi (IndoBERT+Viking vs Fast vs Direct LLM); (4) Evaluasi multi-turn vs brute-force Context Stuffing; serta (5) Uji ketahanan terhadap adversarial prompt injection.")
    ]
    for r_idx, row_data in enumerate(data, start=1):
        for c_idx, text in enumerate(row_data):
            tbl.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl, col_widths=col_w, alignments=alignments)

    # 2. Ringkasan Eksekutif
    add_heading_1(doc, "RINGKASAN EKSEKUTIF", page_break=True)
    add_p(doc, 
          "Perkembangan model bahasa besar (Large Language Models / LLM) menawarkan potensi revolusioner dalam otomasi layanan informasi akademik di perguruan tinggi. Namun, penerapan LLM komersial generik secara langsung pada domain tertutup (closed-domain) perguruan tinggi menghadapi kendala fundamental berupa halusinasi faktual (fact hallucination)—terutama pada data administratif kritis seperti Nomor Induk Pegawai (NIP 18 digit dosen) dan prasyarat SKS kelulusan—serta tingginya biaya inferensi pada percakapan panjang.",
          bold_prefix="Latar Belakang & Urgensi: ")
          
    add_p(doc,
          "Laporan ini mendokumentasikan perancangan, implementasi, dan pengujian menyeluruh Luco, sebuah sistem asisten informasi akademik cerdas untuk Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura (UNTAN). Luco dibangun di atas arsitektur Hybrid Agentic Retrieval-Augmented Generation (RAG) yang mengintegrasikan penalaran agen cerdas LlamaIndex FunctionAgent, basis data vektor hierarkis OpenViking, mikroservis model representasi vektor bahasa Indonesia IndoBERT (indobenchmark/indobert-base-p1 berdimensi 768), mesin pencari deterministik lookup.json, serta gerbang penyaring kueri upfront router 2-tier.",
          bold_prefix="Solusi Arsitektur: ")
          
    add_p(doc,
          "Pengujian empiris menyeluruh membuktikan keunggulan sistem: (1) Automated test suite berbasis Pytest meluluskan 100% dari 78 skenario pengujian pada 13 modul sistem dalam waktu 5,03 detik; (2) Evaluasi embedding membuktikan model IndoBenchmark p1 unggul secara mutlak dengan Top-1 Accuracy 80,0% dan Top-3 Recall 100,0% dengan margin separasi rata-rata +0,2657, mengungguli model IndoLEM yang mengalami fenomena representation collapse; (3) Pencarian deterministik menghasilkan akurasi 100% (zero hallucination) pada data NIP dosen dan regulasi formal; (4) Pada skenario percakapan panjang multi-turn (6 giliran interaksi), arsitektur Luco berhasil menghemat 97,76% token (44,6x lebih hemat) dan 96,66% biaya komputasi dibandingkan metode brute-force context stuffing; serta (5) Upfront router terbukti 100% konsisten menolak kueri di luar cakupan akademik dengan latensi 0 ms tanpa memicu pemanggilan LLM berbayar.",
          bold_prefix="Temuan Kunci: ")

    add_callout(doc, 
                "Sistem Luco berhasil membuktikan bahwa kombinasi Hybrid Agentic RAG dengan pencarian data deterministik dan dense embedding lokal bahasa Indonesia mampu meniadakan halusinasi faktual pada sistem informasi perguruan tinggi dengan efisiensi biaya operasional yang sangat ekonomis (Rp 3,37 per percakapan).",
                bold_prefix="Pernyataan Kontribusi: ")
                
    add_p(doc, "Hybrid Agentic RAG, Large Language Models, IndoBERT, OpenViking, Knowledge Vault, Upfront Semantic Router, Zero-Hallucination, Informatika UNTAN.", bold_prefix="Kata Kunci: ")

    # English Abstract
    add_heading_2(doc, "EXECUTIVE SUMMARY (ENGLISH)")
    add_p(doc,
          "The deployment of Large Language Models (LLMs) in closed-domain academic environments faces major challenges regarding factual hallucinations, particularly when dealing with critical administrative data such as 18-digit employee identification numbers (NIP) and formal curriculum prerequisites. This paper presents the design, implementation, and empirical evaluation of Luco, an intelligent academic information assistant for the Undergraduate Informatics Study Program at Universitas Tanjungpura (UNTAN). Luco implements a Hybrid Agentic Retrieval-Augmented Generation (RAG) architecture powered by LlamaIndex FunctionAgent, OpenViking hierarchical vector database, Indonesian transformer dense embeddings (IndoBERT-base-p1, 768 dimensions), a deterministic lookup mechanism (lookup.json), and a 2-tier upfront semantic guardrail router.",
          bold_prefix="Abstract: ")
          
    add_p(doc,
          "Comprehensive empirical evaluations reveal that: (1) The automated test suite achieves a 100% pass rate across 78 test cases covering 13 core modules in 5.03 seconds; (2) The IndoBERT-base-p1 embedding achieves 80.0% Top-1 accuracy and 100.0% Top-3 recall with a distinct separation margin of +0.2657, substantially preventing representation collapse observed in alternative models; (3) The deterministic lookup guarantees zero hallucination (100% accuracy) on sensitive administrative queries; (4) In realistic multi-turn conversation benchmarks, Luco achieves a 97.76% reduction in cumulative token usage and a 96.66% cost reduction compared to brute-force context stuffing; and (5) The upfront router reliably filters out-of-scope queries with 0 ms tool latency. The proposed system demonstrates high accuracy, strict security compliance, and exceptional economic viability for institutional academic deployment.",
          bold_prefix="Results & Impact: ")
          
    add_p(doc, "Hybrid Agentic RAG, Large Language Models, IndoBERT, Vector Database, Prompt Engineering, Academic Chatbot, Universitas Tanjungpura.", bold_prefix="Keywords: ")

    # 3. Kata Pengantar
    add_heading_1(doc, "KATA PENGANTAR", page_break=True)
    add_p(doc, "Puji dan syukur kami panjatkan ke hadirat Tuhan Yang Maha Esa karena atas berkat, rahmat, dan petunjuk-Nya, kami dapat menyelesaikan Laporan Tugas Besar Pengganti Ujian Akhir Semester (UAS) untuk Mata Kuliah Kecerdasan Buatan (AI) Tahun Akademik 2025/2026 yang berjudul:")
    
    p_judul = doc.add_paragraph()
    p_judul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_judul.paragraph_format.space_before = Pt(6)
    p_judul.paragraph_format.space_after = Pt(8)
    r = p_judul.add_run("“Luco: Chatbot Asisten Informasi Program Studi Informatika UNTAN Berbasis Hybrid Agentic RAG dan Agentic Search Menggunakan LlamaIndex”")
    r.font.name = "Times New Roman"
    r.font.bold = True
    r.font.color.rgb = COLOR_NAVY
    
    add_p(doc, "Laporan ini disusun secara sistematis mengacu pada format panduan resmi laporan tugas besar mata kuliah Kecerdasan Buatan (F. Sistematika Laporan), mendokumentasikan tahapan analisis masalah, perancangan arsitektur, implementasi sistem cerdas, pengujian empiris kuantitatif, analisis etika dan privasi, serta rekomendasi pengembangan masa depan.")
    add_p(doc, "Dalam proses penyusunan tugas besar ini, kami menerima banyak bimbingan, arahan, dan dukungan dari berbagai pihak. Oleh karena itu, kami ingin menyampaikan ucapan terima kasih yang tulus dan sebesar-besarnya kepada:")
    
    add_bullet(doc, "Dosen Pengampu Mata Kuliah Kecerdasan Buatan Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura atas dedikasi, transfer wawasan ilmiah, serta masukan konstruktif selama sesi konsultasi tugas besar.", bold_prefix="1. ")
    add_bullet(doc, "Koordinator dan Seluruh Dosen Program Studi S-1 Informatika Universitas Tanjungpura atas keterbukaan informasi, publikasi dokumen regulasi resmi, serta dukungan terhadap inovasi digital di lingkungan jurusan.", bold_prefix="2. ")
    add_bullet(doc, "Balin Niswah, alumni Informatika UNTAN yang telah memprakarsai topik riset awal asisten informasi akademik prodi pada naskah skripsinya.", bold_prefix="3. ")
    add_bullet(doc, "Edwin Hermili, rekan mahasiswa pengembang yang telah berkolaborasi dalam pembangunan fondasi awal prototipe sistem asisten produksi.", bold_prefix="4. ")
    add_bullet(doc, "Orang tua dan keluarga tercinta atas doa, restu, dan dukungan moril maupun materil yang senantiasa menyertai langkah kami.", bold_prefix="5. ")
    add_bullet(doc, "Rekan-rekan mahasiswa angkatan 2024 dan civitas akademika Himpunan Mahasiswa Informatika (HMIF) FT UNTAN atas ruang diskusi dan persahabatan yang suportif.", bold_prefix="6. ")
    
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sign.paragraph_format.space_before = Pt(14)
    p_sign.paragraph_format.line_spacing = 1.15
    r_s = p_sign.add_run("Pontianak, 16 November 2026\n\n\nTim Penulis (Kelompok Luco)\nRagil Amirzaky · Andrean Stephanus · Adjie Prasetya")
    r_s.font.name = "Times New Roman"
    r_s.font.bold = True
    r_s.font.color.rgb = COLOR_CHARCOAL

    # 4. Daftar Isi
    add_heading_1(doc, "DAFTAR ISI", page_break=True)
    toc_items = [
        ("LEMBAR KONSULTASI & KESIAPAN TUGAS BESAR", "ii"),
        ("RINGKASAN EKSEKUTIF", "iv"),
        ("EXECUTIVE SUMMARY (ENGLISH)", "v"),
        ("KATA PENGANTAR", "vi"),
        ("DAFTAR ISI", "vii"),
        ("1. JUDUL PROYEK DAN IDENTITAS ANGGOTA KELOMPOK", "1"),
        ("   1.1. Judul Proyek & Tema Sistem", "1"),
        ("   1.2. Identitas Anggota Kelompok & Pembagian Tugas", "1"),
        ("   1.3. Kronologi & Rekam Jejak Pengembangan", "2"),
        ("2. PENDAHULUAN", "4"),
        ("   2.1. Latar Belakang Masalah", "4"),
        ("   2.2. Rumusan Masalah", "5"),
        ("   2.3. Tujuan Penelitian & Pengembangan", "5"),
        ("   2.4. Manfaat Sistem", "6"),
        ("   2.5. Batasan Masalah & Ruang Lingkup", "7"),
        ("3. LANDASAN TEORI SINGKAT", "8"),
        ("   3.1. Large Language Models (LLM) & Halusinasi Faktual", "8"),
        ("   3.2. Paradigma Retrieval-Augmented Generation (RAG)", "9"),
        ("   3.3. Hybrid Agentic RAG & Function Calling Loop", "9"),
        ("   3.4. Model Transformer Bahasa Indonesia (IndoBERT)", "10"),
        ("   3.5. Formulasi Matematis Mean Pooling & Cosine Similarity", "11"),
        ("   3.6. Basis Data Vektor Hierarkis (OpenViking)", "12"),
        ("   3.7. Upfront Semantic Routing & Guardrail AI", "12"),
        ("   3.8. Evaluasi Groundedness & LLM-as-a-Judge", "13"),
        ("4. DATA: SUMBER, DESKRIPSI, DAN PREPROCESSING", "14"),
        ("   4.1. Sumber Data (Data Sources)", "14"),
        ("   4.2. Deskripsi Dataset & Taksonomi Pengetahuan", "15"),
        ("   4.3. Tahapan Preprocessing Data", "16"),
        ("5. PERANCANGAN SISTEM", "19"),
        ("   5.1. Diagram Alir & Arsitektur Menyeluruh Sistem", "19"),
        ("   5.2. Spesifikasi Masukan (Input)", "20"),
        ("   5.3. Proses Kecerdasan Buatan (AI Reasoning Pipeline)", "21"),
        ("   5.4. Spesifikasi Keluaran (Output) & Dual-Option Access", "23"),
        ("   5.5. Perancangan Skema Basis Data Sesi (ERD)", "24"),
        ("6. IMPLEMENTASI", "25"),
        ("   6.1. Perangkat Lunak & Stack Teknologi", "25"),
        ("   6.2. Tahapan Rekayasa & Implementasi Kode (src/luco/)", "26"),
        ("   6.3. Panduan Menjalankan Prototipe Sistem", "28"),
        ("7. PENGUJIAN DAN EVALUASI", "30"),
        ("   7.1. Pengujian Unit & Integrasi Otomatis (Pytest 78/78 Passed)", "30"),
        ("   7.2. Evaluasi Komparasi Model Dense Embedding IndoBERT", "32"),
        ("   7.3. Benchmark Komparasi 3 Mode Inferensi Sistem Luco", "34"),
        ("   7.4. Evaluasi Komparasi Multi-Turn: Context Stuffing vs Luco", "37"),
        ("   7.5. Pengujian Keamanan, Prompt Injection, & Imutabilitas", "40"),
        ("   7.6. Pengujian Integritas Tautan & Verifikasi Sitasi", "41"),
        ("   7.7. Analisis Efisiensi Komputasi, Token, & Biaya Operasional", "42"),
        ("8. ETIKA DAN KETERBATASAN", "44"),
        ("   8.1. Potensi Bias Algoritmik & Budaya Bahasa", "44"),
        ("   8.2. Privasi Data & Perlindungan Informasi Sivitas Akademika", "44"),
        ("   8.3. Risiko Kesalahan & Strategi Halusinasi Nol", "45"),
        ("   8.4. Penggunaan Generative AI Secara Bertanggung Jawab", "46"),
        ("   8.5. Keterbatasan Teknis Sistem", "47"),
        ("9. KESIMPULAN DAN SARAN PENGEMBANGAN", "48"),
        ("   9.1. Kesimpulan", "48"),
        ("   9.2. Saran Pengembangan Lanjutan (Future Work)", "49"),
        ("DAFTAR PUSTAKA", "51"),
        ("LAMPIRAN", "53"),
        ("   Lampiran 1: Rekapitulasi Eksekusi Pytest Lengkap (78 Skenario)", "53"),
        ("   Lampiran 2: Katalog Lengkap 26 Berkas Resmi Directus", "56"),
        ("   Lampiran 3: Panduan Eksekusi Sistem & Replikasi Lingkungan", "58")
    ]
    tbl = doc.add_table(rows=len(toc_items), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_w = [Inches(5.7), Inches(1.0)]
    for idx, (title, page) in enumerate(toc_items):
        c0 = tbl.rows[idx].cells[0]
        c1 = tbl.rows[idx].cells[1]
        c0.width = col_w[0]
        c1.width = col_w[1]
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2.5)
        p0.paragraph_format.space_before = Pt(1)
        r0 = p0.add_run(title)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(10)
        if title[0].isdigit() or title.startswith("LEMBAR") or title.startswith("DAFTAR") or title.startswith("RINGKASAN") or title.startswith("KATA"):
            r0.font.bold = True
            r0.font.color.rgb = COLOR_NAVY
            
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1.paragraph_format.space_after = Pt(2.5)
        p1.paragraph_format.space_before = Pt(1)
        r1 = p1.add_run(page)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10)
        if title[0].isdigit() or title.startswith("LEMBAR") or title.startswith("DAFTAR") or title.startswith("RINGKASAN"):
            r1.font.bold = True

def add_section_1(doc):
    add_heading_1(doc, "1. JUDUL PROYEK DAN IDENTITAS ANGGOTA KELOMPOK", page_break=True)
    
    add_heading_2(doc, "1.1. Judul Proyek & Tema Sistem")
    add_p(doc, "Judul Resmi Tugas Besar:", bold_prefix="Judul Proyek: ")
    add_callout(doc, 
                "“Luco: Chatbot Asisten Informasi Program Studi Informatika UNTAN Berbasis Hybrid Agentic RAG dan Agentic Search Menggunakan LlamaIndex”\n"
                "(Rancang Bangun Asisten Informasi Akademik Berbasis Hybrid Agentic Retrieval-Augmented Generation pada Program Studi S-1 Informatika Universitas Tanjungpura)",
                bold_prefix="Judul Lengkap: ")
    add_p(doc, "Sistem Luco dirancang sebagai asisten virtual cerdas yang menyajikan informasi akademik, panduan administratif, regulasi kurikulum, serta direktori dosen dan laboratorium secara presisi, terpercaya, dan bebas dari halusinasi data.")

    add_heading_2(doc, "1.2. Identitas Anggota Kelompok & Pembagian Tugas")
    add_p(doc, "Tugas besar ini dikerjakan secara kolaboratif oleh kelompok mahasiswa Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura Angkatan 2024 yang beranggotakan 3 orang:")
    
    tbl_members = doc.add_table(rows=4, cols=4)
    col_w = [Inches(1.8), Inches(1.3), Inches(2.3), Inches(1.6)]
    alignments = [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT]
    
    h_members = ["Nama Mahasiswa", "NIM", "Peran & Tanggung Jawab Utama", "Fokus Modul Sistem"]
    for i, h in enumerate(h_members):
        tbl_members.rows[0].cells[i].paragraphs[0].text = h
        
    data_members = [
        ("Ragil Amirzaky", "D1041241069", 
         "Lead Developer & Cloud/Systems Architect (Merancang arsitektur agen LlamaIndex, backend FastAPI, docker container, dan router 2-tier).",
         "src/luco/agent.py, router.py, backends.py, tools.py"),
        ("Andrean Stephanus", "D1041241027", 
         "Co-Developer & Evaluation Engineer (Merancang pipeline benchmark, evaluasi embedding IndoBERT, dan pengujian multi-turn).",
         "eval/, scripts/benchmark_*, test_llm_resilience.py"),
        ("Adjie Prasetya", "D1041241038", 
         "Co-Developer & Knowledge Vault Curation (Kurasi basis pengetahuan vault, ekstraksi dokumen Directus, dan validasi lookup dosen).",
         "vault/, scripts/fetch_and_convert_*, lookup.json")
    ]
    for r_idx, row_data in enumerate(data_members, start=1):
        for c_idx, text in enumerate(row_data):
            tbl_members.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl_members, col_widths=col_w, alignments=alignments)

    add_heading_2(doc, "1.3. Kronologi & Rekam Jejak Pengembangan")
    add_p(doc, "Pengembangan asisten cerdas Luco berakar dari riset topik skripsi Balin Niswah (alumni S1 Informatika UNTAN) yang mengeksplorasi chatbot informasi prodi berbasis model bahasa. Selanjutnya, Ragil Amirzaky bersama Andrean Stephanus dan Edwin Hermili membangun fondasi sistem production-ready pertama yang mengintegrasikan kemampuan agentic dan semi-GraphRAG yang dirancang sebagai prototipe asisten dosen.")
    add_p(doc, "Dalam rangka pelaksanaan Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan (AI) Tahun Akademik 2025/2026, tim pengembang yang beranggotakan Ragil Amirzaky, Andrean Stephanus, dan Adjie Prasetya secara komprehensif merombak modul RAG tersebut menjadi Hybrid Agentic RAG dengan mengintegrasikan basis data vektor hierarkis OpenViking, model transformer bahasa Indonesia IndoBERT (768 dimensi), pencarian deterministik data presisi lookup.json, serta gerbang penyaring kueri upfront router 2-tier.")

def add_section_2(doc):
    add_heading_1(doc, "2. PENDAHULUAN", page_break=True)
    
    add_heading_2(doc, "2.1. Latar Belakang Masalah")
    add_p(doc, "Penyampaian informasi akademik, regulasi kurikulum, dan prosedur administratif di lingkungan Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura (UNTAN) saat ini tersebar di berbagai dokumen panduan terpisah, seperti Surat Keputusan (SK) Dekan, pedoman Kerja Praktik (KP), panduan Tugas Akhir/Skripsi (TA), modul kurikulum 140 SKS, serta format formulir administratif di portal repositori Directus kampus. Mahasiswa kerap mengalami kebingungan dalam mencari informasi mutakhir terkait prasyarat SKS, tanggal tenggat sempro, pembagian kelompok keahlian (KBK) dosen, hingga alur sistem informasi seperti SPOTA.")
    add_p(doc, "Penggunaan model kecerdasan buatan komersial generik (generative AI) secara langsung untuk menjawab pertanyaan akademik memiliki kelemahan mendasar:")
    add_bullet(doc, "Model bahasa besar (LLM) cenderung mengarang angka-angka administratif kritis, seperti nomor induk pegawai (NIP 18 digit dosen), alamat surel institusi, atau nomor pasal regulasi akademik.", bold_prefix="1. Halusinasi Faktual (Fact Hallucination): ")
    add_bullet(doc, "Model LLM publik tidak memiliki akses terhadap arsip dokumen panduan internal kampus yang bersifat spesifik (proprietary/closed-domain).", bold_prefix="2. Ketiadaan Konteks Institusional Lokal: ")
    add_bullet(doc, "Model-model embedding umum (sering kali berbasis korpus multibahasa atau bahasa asing) kesulitan menangkap makna semantik dari akronim dan terminologi lokal kampus seperti KP, Sempro, Yudisium, SPOTA, KBK, dan SIAKAD.", bold_prefix="3. Degradasi Pemahaman Semantik Lokal: ")
    add_p(doc, "Untuk mengatasi masalah tersebut, dibangun sistem asisten virtual cerdas bernama Luco (luco-untan) yang mengintegrasikan arsitektur Hybrid Agentic Retrieval-Augmented Generation (RAG) dengan model representasi vektor bahasa Indonesia IndoBERT, dipadukan dengan pencarian data deterministik terstruktur dan gerbang penyaring kueri (upfront router).")

    add_heading_2(doc, "2.2. Rumusan Masalah")
    add_p(doc, "Berdasarkan latar belakang masalah yang telah diuraikan, rumusan masalah dalam penelitian ini adalah:")
    add_bullet(doc, "Bagaimana merancang arsitektur chatbot AI yang mampu memberikan informasi akademik Prodi Informatika UNTAN dengan tingkat halusinasi nol persen pada data kritis (NIP dosen dan prasyarat formal)?", bold_prefix="1. ")
    add_bullet(doc, "Bagaimana efektivitas model dense embedding Bahasa Indonesia indobenchmark/indobert-base-p1 dibandingkan model alternatif seperti indolem/indobert-base-uncased dalam memisahkan teks regulasi kampus dari dokumen pengganggu (distractor)?", bold_prefix="2. ")
    add_bullet(doc, "Bagaimana komparasi kinerja (latensi, konsumsi token, biaya, dan akurasi jawaban) antara mode Agentic RAG, One-shot Fast Retrieval, dan Direct LLM?", bold_prefix="3. ")
    add_bullet(doc, "Bagaimana mengamankan sistem asisten akademik dari serangan manipulasi prompt (prompt injection / jailbreak) serta menjaga kepatuhan batas etika akademik?", bold_prefix="4. ")

    add_heading_2(doc, "2.3. Tujuan Penelitian & Pengembangan")
    add_p(doc, "Tujuan yang hendak dicapai dalam perancangan dan implementasi sistem ini meliputi:")
    add_bullet(doc, "Membangun sistem chatbot asisten informasi akademik berbasis web yang responsif, terintegrasi dengan basis dokumen resmi Prodi Informatika UNTAN.", bold_prefix="1. ")
    add_bullet(doc, "Mengintegrasikan model representasi vektor bahasa Indonesia berkinerja tinggi (IndoBERT 768-dim) dengan database vektor OpenViking dan pencarian data deterministik (lookup.json).", bold_prefix="2. ")
    add_bullet(doc, "Mengimplementasikan gerbang filter kueri (Upfront Router) 2-tier yang efisien (latensi 0 ms pada kueri sapaan dan non-akademik).", bold_prefix="3. ")
    add_bullet(doc, "Menyediakan sistem ekstraksi dokumen resmi (26 berkas formulir & panduan) dengan akses ganda (dual-option: naskah Markdown interaktif vs unduh berkas master fisik asli).", bold_prefix="4. ")
    add_bullet(doc, "Menguji dan membuktikan keandalan sistem melalui automated test suite, evaluasi LLM-as-a-judge, dan benchmark keamanan adversarial.", bold_prefix="5. ")

    add_heading_2(doc, "2.4. Manfaat Sistem")
    add_bullet(doc, "Mempercepat perolehan informasi resmi terkait alur KP, pengajuan draft proposal skripsi, jadwal akademik, dan kontak dosen tanpa harus datang ke ruang sekretariat untuk hal-hal administratif dasar.", bold_prefix="Bagi Mahasiswa: ")
    add_bullet(doc, "Mengurangi beban kerja repetitif staf tata usaha dan dosen dalam menjawab pertanyaan regulasi yang sama berulang kali.", bold_prefix="Bagi Pengelola Program Studi: ")
    add_bullet(doc, "Memberikan kontribusi rancang bangun sistem Hybrid Agentic RAG berbahasa Indonesia yang tangguh, hemat biaya, dan terverifikasi secara empiris.", bold_prefix="Bagi Pengembangan Akademik: ")

    add_heading_2(doc, "2.5. Batasan Masalah & Ruang Lingkup")
    add_p(doc, "Agar fokus penelitian dan implementasi tetap terarah sesuai alokasi waktu Tugas Besar Pengganti UAS Kecerdasan Buatan 2026, ditetapkan batasan masalah sebagai berikut:")
    add_bullet(doc, "Informasi terbatas pada kurikulum, dosen, laboratorium, regulasi KP/TA, kalender akademik, dan 26 dokumen resmi Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura.", bold_prefix="Lingkup Pengetahuan: ")
    add_p(doc, "Sesuai kesepakatan rancangan awal, beberapa modul berikut sengaja tidak dikerjakan pada fase ini dan dialokasikan sebagai pengembangan lanjutan (scope-out):", bold_prefix="Lingkup Teknis di Luar Batasan Tugas Besar (Scope-Out): ")
    add_bullet(doc, "Integrasi basis data vektor terdistribusi enterprise multi-node (seperti Qdrant/Milvus cluster).", bold_prefix="1. ")
    add_bullet(doc, "Implementasi antarmuka pengenalan dan sintesis suara (speech-to-speech) menggunakan Whisper/TTS.", bold_prefix="2. ")
    add_bullet(doc, "Integrasi Single Sign-On (SSO) akun universitas dan otorisasi bertingkat (RBAC/JWT kompleks tingkat universitas).", bold_prefix="3. ")
    add_bullet(doc, "Graf pengetahuan (Knowledge Graph) relasi topik skripsi mahasiswa dengan pakar dosen.", bold_prefix="4. ")

def add_section_3(doc):
    add_heading_1(doc, "3. LANDASAN TEORI SINGKAT", page_break=True)
    
    add_heading_2(doc, "3.1. Large Language Models (LLM) & Halusinasi Faktual")
    add_p(doc, "Model Bahasa Besar (Large Language Models) seperti OpenAI GPT-4 dan Google Gemini dilatih pada korpus data teks raksasa menggunakan mekanisme self-attention transformer. Meskipun memiliki kapabilitas penalaran linguistik yang tinggi, LLM bersifat probabilistik (next-token prediction). Ketika dihadapkan pada pertanyaan faktual tertutup (closed-domain), LLM rentan menghasilkan halusinasi (hallucination), yaitu keluaran teks yang terdengar meyakinkan namun secara faktual salah atau fiktif.")

    add_heading_2(doc, "3.2. Paradigma Retrieval-Augmented Generation (RAG)")
    add_p(doc, "Retrieval-Augmented Generation (RAG) diperkenalkan oleh Lewis et al. (2020) untuk mengatasi kelemahan halusinasi LLM. Alur dasar RAG memisahkan proses menjadi dua tahap:")
    add_bullet(doc, "Mengambil potongan teks dokumen relevan dari basis pengetahuan eksternal berdasarkan kemiripan kueri.", bold_prefix="1. Retrieval: ")
    add_bullet(doc, "Menyuntikkan potongan teks tersebut ke dalam prompt LLM sebagai konteks referensi, sehingga model menghasilkan jawaban yang terikat pada data (grounded).", bold_prefix="2. Augmentation & Generation: ")

    add_heading_2(doc, "3.3. Hybrid Agentic RAG & Function Calling Loop")
    add_p(doc, "RAG konvensional bersifat linear (naive RAG) di mana penelusuran dokumen hanya dilakukan 1 kali. Pada Agentic RAG, model LLM berperan sebagai agen penalaran (reasoning agent) yang dilengkapi dengan alat bantu (tools). Agen menggunakan teknik ReAct (Reasoning + Acting) atau Function Calling Loop untuk:")
    add_bullet(doc, "Mengevaluasi apakah dokumen yang diambil sudah cukup menjawab pertanyaan.", bold_prefix="• ")
    add_bullet(doc, "Melakukan penelusuran lanjutan jika informasi belum lengkap.", bold_prefix="• ")
    add_bullet(doc, "Mengakses sumber data deterministik jika diperlukan data pasti (seperti nomor telepon atau NIP).", bold_prefix="• ")

    add_heading_2(doc, "3.4. Model Transformer Bahasa Indonesia (IndoBERT)")
    add_p(doc, "Representasi dokumen dalam ruang vektor membutuhkan model bahasa terenkode (encoder-only transformer). Model BERT (Devlin et al., 2018) menghasilkan vektor kontekstual untuk setiap token. Dua keluarga model BERT bahasa Indonesia terkemuka:")
    add_bullet(doc, "Dilatih menggunakan korpus Indo4B (~3,6 miliar kata) yang mencakup berita, ensiklopedia, media sosial, dan forum internet.", bold_prefix="1. IndoBenchmark IndoBERT (Wilie et al., 2020): ")
    add_bullet(doc, "Dilatih menggunakan korpus berita formal (Kompas, Tempo, Tempo Interaktif) dan Wikipedia Bahasa Indonesia (~220 juta kata).", bold_prefix="2. IndoLEM IndoBERT (Koto et al., 2020): ")

    add_heading_2(doc, "3.5. Formulasi Matematis Mean Pooling & Cosine Similarity")
    add_p(doc, "Proses ekstraksi representasi kalimat tunggal (sentence embedding) dilakukan menggunakan teknik Mean Pooling yang dirumuskan secara matematis sebagai:")
    
    add_code_block(doc, 
                   "Formulasi Matematis Ekstraksi Vektor dan Normalisasi L2:\n"
                   "  v = [ sum_{i=1}^L (h_i * m_i) ] / [ sum_{i=1}^L m_i ]\n"
                   "  v_norm = v / ||v||_2\n\n"
                   "Operasi Kemiripan Kosinus (Cosine Similarity):\n"
                   "  Sim(q, d) = q_norm . d_norm = sum_{j=1}^{768} (q_j * d_j)")
                   
    add_p(doc, "Di mana h_i adalah vektor hidden state token ke-i pada layer terakhir transformer (768 dimensi), m_i adalah attention mask, dan Sim(q, d) menghasilkan nilai kemiripan dalam rentang [-1, 1].")

    add_heading_2(doc, "3.6. Basis Data Vektor Hierarkis (OpenViking)")
    add_p(doc, "OpenViking adalah platform basis data vektor ringan berbasis Docker yang mengombinasikan penyimpanan berkas lokal terindeks dengan pencarian semantik vektor dan pencarian leksikal BM25 (hybrid search). Dokumen diindeks berdasarkan hierarki direktori (resources), memungkinkan pemilahan domain pengetahuan secara terisolasi (misalnya: folder akademik/, dosen/, kp-ta/, dan dokumen/).")

    add_heading_2(doc, "3.7. Upfront Semantic Routing & Guardrail AI")
    add_p(doc, "Untuk meningkatkan efisiensi dan keamanan, sistem RAG modern tidak mengalirkan setiap input pengguna langsung ke model agen. Gerbang penyaring (Upfront Router) memisahkan kueri pengguna menjadi beberapa jalur:")
    add_bullet(doc, "Sapaan atau penolakan kueri terlarang diproses dengan latensi 0 ms tanpa memanggil API LLM.", bold_prefix="• Heuristik Langsung: ")
    add_bullet(doc, "Kueri dievaluasi apakah berada dalam domain institusi (in-scope), di luar domain (out-of-scope), atau membutuhkan penanganan kontak khusus (contact redirect).", bold_prefix="• Klasifikasi Semantik: ")

    add_heading_2(doc, "3.8. Evaluasi Groundedness & LLM-as-a-Judge")
    add_p(doc, "Evaluasi kebenaran sistem RAG diukur menggunakan metrik:")
    add_bullet(doc, "Seberapa sering dokumen target masuk ke dalam k hasil teratas.", bold_prefix="1. Top-k Retrieval Accuracy & Recall: ")
    add_bullet(doc, "Selisih nilai kemiripan antara dokumen target relevan dengan dokumen pengganggu (distractor) terdekat: Delta = S_GroundTruth - max(S_Distractors).", bold_prefix="2. Separation Margin (Delta): ")
    add_bullet(doc, "Penggunaan model bahasa canggih pihak ketiga yang dipandu oleh rubrik penilaian ketat (skala 1–5) untuk mengukur ketepatan faktual dan ketiadaan halusinasi secara objektif.", bold_prefix="3. LLM-as-a-Judge: ")

def add_section_4(doc):
    add_heading_1(doc, "4. DATA: SUMBER, DESKRIPSI, DAN PREPROCESSING", page_break=True)
    
    add_heading_2(doc, "4.1. Sumber Data (Data Sources)")
    add_p(doc, "Basis pengetahuan sistem Luco bersumber dari arsip dokumen resmi Program Studi S-1 Informatika Fakultas Teknik Universitas Tanjungpura yang dihimpun dari tiga kanal primer:")
    add_bullet(doc, "Sebanyak 26 berkas formulir dan pedoman resmi diunduh langsung dari repositori Directus API prodi (https://api.ifuntanhub.dev/items/berkas) dalam format biner asli master (14 berkas PDF dan 12 berkas DOCX).", bold_prefix="1. Repositori Berkas Resmi Directus API: ")
    add_bullet(doc, "Sebanyak 104 naskah panduan akademik terstruktur disimpan di direktori vault/ dengan metadata frontmatter YAML terstandarisasi.", bold_prefix="2. Obsidian Knowledge Vault: ")
    add_bullet(doc, "Profil 33 dosen Informatika UNTAN disusun melalui pencarian data direktori prodi dan diperkaya dengan rekam jejak riset serta publikasi internasional melalui pipeline crawling OpenAlex API.", bold_prefix="3. Direktori Dosen & Crawler OpenAlex: ")

    add_heading_2(doc, "4.2. Deskripsi Dataset & Taksonomi Pengetahuan")
    add_p(doc, "Pengetahuan akademik Luco diklasifikasikan ke dalam 7 kategori taksonomi terstruktur di dalam vault/:")
    
    tbl_tax = doc.add_table(rows=8, cols=4)
    col_w = [Inches(1.5), Inches(0.8), Inches(3.2), Inches(1.5)]
    alignments = [WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT]
    
    h_tax = ["Kategori Folder", "Berkas", "Cakupan Materi & Informasi Akademik", "Format Utama"]
    for i, h in enumerate(h_tax):
        tbl_tax.rows[0].cells[i].paragraphs[0].text = h
        
    data_tax = [
        ("akademik/", "6 berkas", "Kurikulum 140 SKS, Capaian Pembelajaran Lulusan (CPL), distribusi semester, konversi nilai, dan prasyarat.", "Markdown (.md)"),
        ("dosen/", "34 berkas", "Profil 33 dosen, NIP 18 digit, email institusi, Kelompok Bidang Keahlian (KBK), dan rekam jejak publikasi.", "Markdown + lookup.json"),
        ("fasilitas-lab/", "3 berkas", "Laboratorium RPL, Sistem Cerdas & Robotika, Jaringan & Komputasi Awan, serta sarana praktikum.", "Markdown (.md)"),
        ("kemahasiswaan/", "8 berkas", "Himpunan Mahasiswa Informatika (HMIF), kegiatan organisasi, prestasi kompetisi, beasiswa, dan tracer study.", "Markdown (.md)"),
        ("kp-ta/", "6 berkas", "Pedoman Kerja Praktik (KP), Seminar Proposal (Sempro), Sidang Skripsi, dan alur penggunaan sistem SPOTA.", "Markdown (.md)"),
        ("profil/", "9 berkas", "Visi, misi, tujuan, sejarah pendirian prodi, sertifikat akreditasi BAN-PT/LAM INFOKOM, struktur organisasi.", "Markdown (.md)"),
        ("dokumen/", "26 berkas", "Koleksi formulir resmi IF-00 s.d. IF-08, SOP KP, pedoman skripsi, dan kalender akademik kampus.", "Markdown + Master Raw")
    ]
    for r_idx, row_data in enumerate(data_tax, start=1):
        for c_idx, text in enumerate(row_data):
            tbl_tax.rows[r_idx].cells[c_idx].paragraphs[0].text = text
    format_styled_table(tbl_tax, col_widths=col_w, alignments=alignments)

    add_heading_2(doc, "4.3. Tahapan Preprocessing Data")
    add_p(doc, "Data mentah dari berkas master biner diolah melalui pipeline preprocessing bertingkat agar dapat dibaca dan dipahami secara optimal oleh model AI:")
    
    add_code_block(doc,
                   "PIPELINE PREPROCESSING DOKUMEN SISTEM LUCO:\n"
                   "[Directus API / Berkas Master] --> [data/dokumen_raw/ (14 PDF & 12 DOCX)]\n"
                   "                                         |\n"
                   "           +-----------------------------+-----------------------------+\n"
                   "           | (Berkas PDF Multi-halaman)                                | (Berkas Formulir DOCX)\n"
                   "           v                                                           v\n"
                   "   [PyMuPDF4LLM Parser]                                        [Mammoth Word Parser]\n"
                   "           | Ekstraksi Heading, Teks & Tabel                           | Ekstraksi Format Bersih\n"
                   "           +-----------------------------+-----------------------------+\n"
                   "                                         |\n"
                   "                                         v\n"
                   "                     [Pembersihan Artefak XML & Normalisasi]\n"
                   "                                         |\n"
                   "                                         v\n"
                   "               [Penyimpanan Naskah Markdown Terstruktur: vault/dokumen/]\n"
                   "                                         |\n"
                   "           +-----------------------------+-----------------------------+\n"
                   "           |                                                           |\n"
                   "           v                                                           v\n"
                   "   [scripts/build_manifest.py]                                 [scripts/build_lookup.py]\n"
                   "   Ekstraksi Pohon Heading H1-H3                              Ekstraksi Hash Table 33 Dosen\n"
                   "   Output: vault/manifest.json                                 Output: vault/lookup.json\n"
                   "           |                                                           |\n"
                   "           v                                                           v\n"
                   "   [scripts/ingest.py]                                         [Pencarian Deterministik]\n"
                   "   Chunking Semantik & Mean Pooling IndoBERT                   NIP 18 Digit & Surel Resmi\n"
                   "   Indeksasi Database Vektor OpenViking :1933                  Akurasi 100% Zero-Hallucination")

    add_p(doc, "Rincian Langkah Preprocessing:", bold_prefix="Penjelasan Rinci Tahapan: ")
    add_bullet(doc, "Berkas PDF diekstrak menggunakan PyMuPDF4LLM untuk mempertahankan hierarki heading dan tabel numerik secara presisi tanpa kehilangan format baris.", bold_prefix="1. Ekstraksi PDF Terformat: ")
    add_bullet(doc, "Berkas DOCX diekstrak menggunakan Mammoth untuk menghasilkan format teks Markdown yang bebas dari tag XML Microsoft Word pengotor konteks token.", bold_prefix="2. Ekstraksi Word Bersih: ")
    add_bullet(doc, "Script scripts/build_manifest.py memindai seluruh 104 berkas vault dan memetakan posisi baris seluruh heading H1, H2, dan H3 ke vault/manifest.json sehingga agen dapat membaca outline dokumen sebelum membaca teks penuh.", bold_prefix="3. Generasi Heading Tree Manifest: ")
    add_bullet(doc, "Script scripts/build_lookup.py mengekstrak NIP 18 digit, surel resmi, dan pembagian KBK dari profil 33 dosen ke dalam berkas hash JSON vault/lookup.json, meniadakan halusinasi angka secara mutlak.", bold_prefix="4. Generasi Hash Table Deterministik: ")
    add_bullet(doc, "Naskah di-chunking berdasarkan batasan semantik heading dan diproses oleh model indobenchmark/indobert-base-p1 pada port 8001 untuk menghasilkan matriks vektor 768 dimensi yang disimpan di OpenViking port 1933.", bold_prefix="5. Vektorisasi & Indeksasi: ")

print("Part 1 V2 ready.")
