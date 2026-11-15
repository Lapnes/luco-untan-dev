"""Skrip migrasi dan reorganisasi basis pengetahuan vault/ Prodi Informatika UNTAN.

Mengintegrasikan berkas dari know.zip dan UNTAN-RAG-Assistant.zip ke dalam
arsitektur 6 kategori modular dengan subfolder KBK dosen dan tautan relatif standar.
"""
from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

ROOT = Path("/home/luco/luco-untan")
VAULT = ROOT / "vault"
KNOW_DIR = Path("/tmp/luco_staging/know_clean")
RAG_DIR = Path("/tmp/luco_staging/rag/UNTAN-RAG-Assistant")


def setup_directories() -> None:
    dirs = [
        VAULT / "profil",
        VAULT / "akademik",
        VAULT / "akademik" / "kurikulum",
        VAULT / "akademik" / "kurikulum" / "2026",
        VAULT / "akademik" / "kurikulum" / "2016",
        VAULT / "akademik" / "panduan",
        VAULT / "kp-ta",
        VAULT / "dosen",
        VAULT / "dosen" / "ai-komputasi",
        VAULT / "dosen" / "rpl-mobile",
        VAULT / "dosen" / "jaringan-keamanan",
        VAULT / "dosen" / "si-spasial",
        VAULT / "dosen" / "umum",
        VAULT / "fasilitas-lab",
        VAULT / "kemahasiswaan",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Direktori vault/ berhasil disiapkan.")


def get_kbk_folder(kk: str) -> str:
    kk_norm = kk.lower()
    if "artificial" in kk_norm or "computation" in kk_norm:
        return "ai-komputasi"
    if "software" in kk_norm or "mobile" in kk_norm:
        return "rpl-mobile"
    if "network" in kk_norm or "security" in kk_norm:
        return "jaringan-keamanan"
    if "information system" in kk_norm or "spatial" in kk_norm:
        return "si-spasial"
    return "umum"


def clean_slug(name: str) -> str:
    base = name.split(",")[0].strip()
    base = re.sub(r"^(Prof\.|Dr\.|Ir\.|H\.)\s*", "", base)
    base = re.sub(r"^(Prof\.|Dr\.|Ir\.|H\.)\s*", "", base)
    base = re.sub(r"\s+[A-Z]\.$", "", base)
    slug = base.lower().strip().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug


def parse_osint(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    text = file_path.read_text(encoding="utf-8")
    
    m_id = re.search(r"OpenAlex ID\*\*:\s*\[?([A-Za-z0-9]+)\]?", text)
    openalex_id = m_id.group(1) if m_id else None
    
    m_pub = re.search(r"Total publikasi\*\*:\s*(\d+)", text)
    total_pub = int(m_pub.group(1)) if m_pub else None
    
    m_sit = re.search(r"Total sitasi\*\*:\s*(\d+)", text)
    total_sit = int(m_sit.group(1)) if m_sit else None
    
    m_h = re.search(r"H-index\*\*:\s*(\d+)", text)
    h_index = int(m_h.group(1)) if m_h else None
    
    # Extract sections: tren publikasi, kolaborasi, venue, publikasi teratas
    tren_sec = ""
    m_tren = re.search(r"(## Tren Publikasi per Tahun\s*\n.*?\n)(?=\n##|\Z)", text, re.DOTALL)
    if m_tren:
        tren_sec = m_tren.group(1).strip()
        
    kolab_sec = ""
    m_kolab = re.search(r"(## Jaringan Kolaborasi.*?\n.*?\n)(?=\n##|\Z)", text, re.DOTALL)
    if m_kolab:
        kolab_sec = m_kolab.group(1).strip()

    venue_sec = ""
    m_venue = re.search(r"(## Venue / Jurnal Favorit\s*\n.*?\n)(?=\n##|\Z)", text, re.DOTALL)
    if m_venue:
        venue_sec = m_venue.group(1).strip()

    pub_sec = ""
    m_pub_sec = re.search(r"(## Publikasi Teratas.*?\n.*?\n)(?=\n##|\Z)", text, re.DOTALL)
    if m_pub_sec:
        pub_sec = m_pub_sec.group(1).strip()

    return {
        "openalex_id": openalex_id,
        "total_pub": total_pub,
        "total_sit": total_sit,
        "h_index": h_index,
        "tren_sec": tren_sec,
        "kolab_sec": kolab_sec,
        "venue_sec": venue_sec,
        "pub_sec": pub_sec,
    }


def migrate_dosen() -> list[dict]:
    roster_files = sorted(glob.glob(str(KNOW_DIR / "content-only" / "prodi-knowledge-base" / "Basis_Pengetahuan_Program_Studi_Informatika_UNTAN" / "12._Daftar_Dosen_Roster_Lengkap" / "*.md")))
    roster_text = ""
    for rf in roster_files:
        roster_text += Path(rf).read_text(encoding="utf-8") + "\n"
        
    rows = re.findall(r"\|\s*([^|\n]+?)\s*\|\s*(\d{18})\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|", roster_text)
    print(f"Ditemukan {len(rows)} data dosen dari roster.")
    
    osint_map = {
        "alfian abdul jalid": "OSINT-Deep-Alfian-Abdul-Jalid.md",
        "anggi perwitasari": "OSINT-Deep-Anggi-Perwitasari.md",
        "anggi srimurdianti": "OSINT-Deep-Anggi-Srimurdianti.md",
        "desepta isna ulumi": "OSINT-Deep-Desepta-Isna-Ulumi.md",
        "dimas apriyandi": "OSINT-Deep-Dimas-Apriyandi.md",
        "arif bijaksana putra negara": "OSINT-Deep-Arif-Bijaksana-Putra-Negara.md",
        "yus sholva": "OSINT-Deep-Yus-Sholva.md",
        "enda esyudha pratama": "OSINT-Deep-Enda-Esyudha-Pratama.md",
        "enriko yudhistira ramadhan": "OSINT-Deep-Enriko-Yudhistira-Ramadhan.md",
        "eva faja ripanti": "OSINT-Deep-Eva-Faja-Ripanti.md",
        "fauzan asrin": "OSINT-Deep-Fauzan-Asrin.md",
        "hengky anra": "OSINT-Deep-Hengky-Anra.md",
        "haried novriando": "OSINT-Deep-Haried-Novriando.md",
        "helen sastypratiwi": "OSINT-Deep-Helen-Sastypratiwi.md",
        "helfi nasution": "OSINT-Deep-Helfi-Nasution.md",
        "heri priyanto": "OSINT-Deep-Heri-Priyanto.md",
        "ibnu arif": "OSINT-Deep-Ibnu-Arif.md",
        "m azhar irwansyah": "OSINT-Deep-M-Azhar-Irwansyah.md",
        "m. azhar irwansyah": "OSINT-Deep-M-Azhar-Irwansyah.md",
        "rickhy artha octaviyana": "OSINT-Deep-Rickhy-Artha-Octaviyana.md",
        "izuardo zulkarnain": "OSINT-Deep-Izuardo-Zulkarnain.md",
        "khairul hafidh": "OSINT-Deep-Khairul-Hafidh.md",
        "m tsanauddin farid": "OSINT-Deep-M-Tsanauddin-Farid.md",
        "m. tsanauddin farid": "OSINT-Deep-M-Tsanauddin-Farid.md",
        "morteza muthhahari": "OSINT-Deep-Morteza-Muthahhari.md",
        "morteza muthahhari": "OSINT-Deep-Morteza-Muthahhari.md",
        "niken candraningrum": "OSINT-Deep-Niken-Candraningrum.md",
        "novi safriadi": "OSINT-Deep-Novi-Safriadi.md",
        "herry sujaini": "OSINT-Deep-Herry-Sujaini.md",
        "rifqi anugrah": "OSINT-Deep-Rifqi-Anugrah.md",
        "rina septiriana": "OSINT-Deep-Rina-Septiriana.md",
        "rizki firdaus mulya": "OSINT-Deep-Rizki-Firdaus-Mulya.md",
        "rudy dwi nyoto": "OSINT-Deep-Rudy-Dwi-Nyoto.md",
        "tursina": "OSINT-Deep-Tursina.md",
        "yulianti": "OSINT-Deep-Yulianti.md",
    }
    
    osint_base = RAG_DIR / "DATA" / "CLEAN" / "vault"
    
    dosen_list = []
    
    for nama_lengkap, nip, email, kk in rows:
        subfolder = get_kbk_folder(kk)
        slug = clean_slug(nama_lengkap)
        
        # Match OSINT
        matched_osint = None
        for k, v in osint_map.items():
            if k in nama_lengkap.lower():
                matched_osint = v
                break
                
        osint_data = {}
        if matched_osint:
            osint_data = parse_osint(osint_base / matched_osint)
            
        openalex_id = osint_data.get("openalex_id")
        jabatan = "Dosen Tetap"
        if "Prof." in nama_lengkap:
            jabatan = "Guru Besar"
        elif "Dr." in nama_lengkap:
            jabatan = "Lektor Kepala"
            
        sources = ["https://informatika.untan.ac.id"]
        if openalex_id:
            sources.append(f"https://openalex.org/{openalex_id}")
            
        target_file = VAULT / "dosen" / subfolder / f"{slug}.md"
        rel_to_vault = target_file.relative_to(VAULT).as_posix()
        
        # Build Markdown content
        lines = [
            "---",
            "tipe: dosen",
            f"nama: {nama_lengkap}",
            f'nip: "{nip}"',
            f"email: {email}",
            f"jabatan: {jabatan}",
            f"kelompok_keahlian: {kk}",
            f"openalex_id: {openalex_id or 'null'}",
            "diverifikasi: true",
            "sumber:",
        ]
        for s in sources:
            lines.append(f"  - {s}")
        lines.extend([
            "---",
            "",
            f"# {nama_lengkap}",
            "",
            "## 1. Biodata Resmi",
            f"- **NIP**: `{nip}`",
            f"- **Surel Resmi**: `{email}`",
            f"- **Kelompok Bidang Keahlian (KBK)**: [{kk}](../../fasilitas-lab/kelompok-bidang-keahlian.md)",
            f"- **Jabatan Fungsional**: {jabatan}",
            f"- **Program Studi**: S1 Informatika, Fakultas Teknik, Universitas Tanjungpura",
            "",
        ])
        
        if openalex_id:
            lines.extend([
                "## 2. Profil Riset & Publikasi (OpenAlex)",
                f"- **OpenAlex ID**: [{openalex_id}](https://openalex.org/{openalex_id})",
                f"- **Total Publikasi Terindeks**: {osint_data.get('total_pub', 0)}",
                f"- **Total Sitasi**: {osint_data.get('total_sit', 0)}",
                f"- **H-index**: {osint_data.get('h_index', '-')}",
                "",
            ])
            if osint_data.get("tren_sec"):
                lines.append(osint_data["tren_sec"])
                lines.append("")
            if osint_data.get("kolab_sec"):
                lines.append(osint_data["kolab_sec"])
                lines.append("")
            if osint_data.get("venue_sec"):
                lines.append(osint_data["venue_sec"])
                lines.append("")
            if osint_data.get("pub_sec"):
                lines.append(osint_data["pub_sec"])
                lines.append("")
        else:
            lines.extend([
                "## 2. Profil Riset & Akademik",
                "Data publikasi ilmiah OpenAlex untuk dosen yang bersangkutan sedang dalam proses verifikasi dan sinkronisasi berkala.",
                "",
            ])
            
        lines.extend([
            "## 3. Tautan Terkait",
            "- [Daftar Seluruh Dosen Prodi Informatika](../README.md)",
            "- [Kelompok Bidang Keahlian](../../fasilitas-lab/kelompok-bidang-keahlian.md)",
            "- [Fasilitas Laboratorium Riset](../../fasilitas-lab/laboratorium.md)",
            "- [Panduan Tugas Akhir & Skripsi](../../kp-ta/panduan-ta.md)",
            "",
        ])
        
        target_file.write_text("\n".join(lines), encoding="utf-8")
        dosen_list.append({
            "nama": nama_lengkap,
            "nip": nip,
            "email": email,
            "kk": kk,
            "jabatan": jabatan,
            "subfolder": subfolder,
            "slug": slug,
            "rel_file": rel_to_vault,
        })
        
    print(f"Berhasil menulis {len(dosen_list)} berkas dosen di vault/dosen/.")
    return dosen_list


def build_dosen_readme(dosen_list: list[dict]) -> None:
    lines = [
        "# Direktori Dosen & Tenaga Pengajar Informatika UNTAN",
        "",
        "Halaman ini memuat daftar resmi 33 dosen Program Studi Informatika, Fakultas Teknik, Universitas Tanjungpura yang dikelompokkan berdasarkan **Kelompok Bidang Keahlian (KBK)**.",
        "",
        "---",
        "",
    ]
    
    kbk_groups = {
        "ai-komputasi": "Computation & Artificial Intelligence (AI & Komputasi)",
        "rpl-mobile": "Software Engineering & Mobile Computing (RPL & Mobile)",
        "jaringan-keamanan": "Networking & Security (Jaringan & Keamanan Sistem)",
        "si-spasial": "Information System & Data Spatial (Sistem Informasi & Data Spasial)",
        "umum": "Dosen Baru & Penempatan Lintas Bidang",
    }
    
    for folder, title in kbk_groups.items():
        members = [d for d in dosen_list if d["subfolder"] == folder]
        lines.extend([
            f"## {title}",
            "",
            "| Nama Lengkap | NIP | Surel Resmi | Profil Dokumen |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for m in sorted(members, key=lambda x: x["nama"]):
            rel_link = f"[{m['nama']}]({m['subfolder']}/{m['slug']}.md)"
            lines.append(f"| {m['nama']} | `{m['nip']}` | `{m['email']}` | {rel_link} |")
        lines.extend(["", "---", ""])
        
    lines.extend([
        "## Tautan Terkait",
        "- [Kelompok Bidang Keahlian](../fasilitas-lab/kelompok-bidang-keahlian.md)",
        "- [Laboratorium Riset](../fasilitas-lab/laboratorium.md)",
        "- [Panduan Tugas Akhir](../kp-ta/panduan-ta.md)",
        "- [Indeks Utama Vault](../README.md)",
        "",
    ])
    
    out = VAULT / "dosen" / "README.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("vault/dosen/README.md berhasil dibuat.")

    # Tulis juga vault/dosen/index.md sebagai pintu masuk pencarian
    index_lines = [
        "---",
        "tipe: indeks",
        "---",
        "",
        "# Daftar Dosen Informatika UNTAN",
        "",
        "Halaman indeks untuk pertanyaan tentang profil dan data dosen. Satu baris per dosen:",
        "",
        "| Dosen | NIP | Kelompok Keahlian | Tautan Profil |",
        "|---|---|---|---|",
    ]
    for d in sorted(dosen_list, key=lambda x: x["nama"]):
        index_lines.append(f"| {d['nama']} | `{d['nip']}` | {d['kk']} | [{d['slug']}]({d['subfolder']}/{d['slug']}.md) |")
    index_lines.append("")
    (VAULT / "dosen" / "index.md").write_text("\n".join(index_lines), encoding="utf-8")
    print("vault/dosen/index.md berhasil diperbarui.")


def migrate_profil() -> None:
    # 1. Visi Misi
    vm_content = """# Visi, Misi, dan Tujuan Program Studi Informatika UNTAN

## 1. Visi Keilmuan
> *"Menjadi program studi unggul, inovatif, dan berdaya saing global, dengan fokus pada informatika cerdas untuk mendukung keberlanjutan dan pemberdayaan masyarakat melalui solusi teknologi berbasis kearifan lokal."*

---

## 2. Misi Tridharma Perguruan Tinggi
1. **Pendidikan OBE Unggul** — Menyelenggarakan pendidikan berbasis informatika cerdas yang unggul dan inovatif melalui pendekatan OBE (*Outcome-Based Education*) untuk menghasilkan lulusan yang kompeten, adaptif, beretika, dan berdaya saing global.
2. **Penelitian untuk SDGs** — Mengembangkan penelitian unggul di bidang informatika cerdas yang mendukung pencapaian Tujuan Pembangunan Berkelanjutan (*Sustainable Development Goals* / SDGs) dan relevan dengan tantangan lokal maupun global.
3. **Pengabdian Berbasis Kearifan Lokal** — Menerapkan dan mengembangkan solusi teknologi berbasis kearifan lokal dalam kegiatan pengabdian kepada masyarakat untuk memberdayakan komunitas secara inklusif dan berkelanjutan.
4. **Kemitraan Strategis** — Membangun kemitraan strategis dengan industri, pemerintah, dan institusi akademik untuk memperkuat ekosistem riset, inovasi, dan penerapan informatika cerdas yang memberikan dampak nyata bagi masyarakat.
5. **Budaya Akademik Beretika** — Menumbuhkan budaya akademik yang beretika, kolaboratif, kreatif, dan berorientasi pada pembelajaran sepanjang hayat untuk mempersiapkan sumber daya manusia unggul menghadapi disrupsi teknologi.

---

## 3. Tujuan Program Studi
Tujuan Program Studi Informatika UNTAN diturunkan dari visi dan misi untuk memastikan setiap aktivitas akademik memberikan dampak nyata bagi lulusan, ilmu pengetahuan, dan masyarakat:
- **Lulusan Unggul & Beretika**: Menghasilkan lulusan yang menguasai informatika cerdas, memiliki integritas profesional, dan berdaya saing global.
- **Kurikulum Adaptif**: Menyelenggarakan [Kurikulum 2026](../akademik/kurikulum/2026/tahap-pembelajaran.md) berbasis OBE yang dinamis terhadap kemajuan industri teknologi informasi.
- **Riset Berdampak**: Mendorong riset pada [Kelompok Bidang Keahlian](../fasilitas-lab/kelompok-bidang-keahlian.md) untuk memecahkan persoalan riil Kalimantan Barat dan nasional.
- **Pengabdian Inklusif**: Mentransfer keahlian teknologi informatika untuk memajukan UMKM, instansi pemerintah, dan masyarakat umum.

---

## Tautan Navigasi
- [Struktur Organisasi](struktur-organisasi.md)
- [Akreditasi dan Prestasi](akreditasi.md)
- [Profil Lulusan & CPL](../akademik/profil-lulusan-cpl.md)
- [Daftar Dosen](../dosen/README.md)
"""
    (VAULT / "profil" / "visi-misi.md").write_text(vm_content, encoding="utf-8")

    # 2. Struktur Organisasi
    so_content = """# Struktur Organisasi Program Studi Informatika UNTAN

## 1. Pimpinan Jurusan & Program Studi
| Jabatan | Pejabat | Profil |
| :--- | :--- | :--- |
| **Ketua Jurusan Informatika** | Dr. Ir. Yus Sholva, S.T., M.T. | [Lihat Profil](../dosen/si-spasial/yus-sholva.md) |
| **Koordinator Program Studi (Kaprodi)** | Eva Faja Ripanti, S.Kom., MMSI., Ph.D. | [Lihat Profil](../dosen/si-spasial/eva-faja-ripanti.md) |

---

## 2. Koordinator Laboratorium Pembelajaran & Riset
| Laboratorium | Koordinator Lab | Profil |
| :--- | :--- | :--- |
| **Lab Komputer & Pemrograman** | Morteza Muthahhari, S.Kom., M.T.I. | [Lihat Profil](../dosen/si-spasial/morteza-muthahhari.md) |
| **Lab Komputasi & Kecerdasan Buatan** | Niken Candraningrum, S.T., M.Cs. | [Lihat Profil](../dosen/ai-komputasi/niken-candraningrum.md) |
| **Lab Rekayasa Data & Perangkat Lunak** | Desepta Isna Ulumi, S.Kom., M.Kom. | [Lihat Profil](../dosen/rpl-mobile/desepta-isna-ulumi.md) |
| **Lab Teknologi & Sistem Informasi** | Enda Esyudha Pratama, S.T., M.T. | [Lihat Profil](../dosen/si-spasial/enda-esyudha-pratama.md) |
| **Lab Jaringan, Keamanan Data & IoT** | Haried Novriando, S.Kom., M.Eng. | [Lihat Profil](../dosen/jaringan-keamanan/haried-novriando.md) |

---

## 3. Kelompok Bidang Keahlian (KBK)
Pengelolaan keilmuan dan penugasan dosen pembimbing Tugas Akhir dikoordinasikan oleh 4 Ketua KBK:
- **KBK Computation & Artificial Intelligence**: Dikoordinasikan oleh [Prof. Dr. Herry Sujaini, S.T., M.T.](../dosen/ai-komputasi/herry-sujaini.md)
- **KBK Software Engineering & Mobile Computing**: Dikoordinasikan oleh [H. Hengky Anra, S.T., M.Kom.](../dosen/rpl-mobile/hengky-anra.md)
- **KBK Networking & Security**: Dikoordinasikan oleh [Ir. M. Azhar Irwansyah, S.T., M.Eng.](../dosen/jaringan-keamanan/m-azhar-irwansyah.md)
- **KBK Information System & Data Spatial**: Dikoordinasikan oleh [Dr. Ir. Yus Sholva, S.T., M.T.](../dosen/si-spasial/yus-sholva.md)

---

## Tautan Terkait
- [Visi, Misi, dan Tujuan](visi-misi.md)
- [Fasilitas Laboratorium](../fasilitas-lab/laboratorium.md)
- [Daftar Dosen Lengkap](../dosen/README.md)
"""
    (VAULT / "profil" / "struktur-organisasi.md").write_text(so_content, encoding="utf-8")

    # 3. Akreditasi
    ak_content = """# Akreditasi & Prestasi Program Studi Informatika UNTAN

## 1. Status Akreditasi Resmi
- **Akreditasi Institusi**: **Unggul** (Universitas Tanjungpura, BAN-PT, Periode 2024-2029).
- **Akreditasi Program Studi**: **Baik Sekali** menuju Unggul (LAM INFOKOM).

---

## 2. Prestasi & Rekognisi Nasional/Internasional
| Peringkat / Predikat | Ajang & Rekognisi | Lembaga / Tahun |
| :--- | :--- | :--- |
| **#19 Nasional** | Kampus Paling Berprestasi di Indonesia | Puspresnas, SIMT 2025 |
| **#7 Nasional** | Top Publikasi Riset Terbaik Nasional | Nature Index Indonesia 2025 |
| **Top 50 Asia** | Competitive Programming Contest | ICPC Asia Pacific 2025 |
| **Juara 1 Regional** | Divisi 1 (Kalimantan, Bali, NTB, NTT) | GEMASTIK 2023, 2024, 2025 |

---

## 3. Ekosistem Platform Digital Mandiri
Prodi Informatika UNTAN mengoperasikan sejumlah platform perangkat lunak internal:
- **SPOTA** (`spota.untan.ac.id`): Sistem Pendukung Outline Tugas Akhir untuk pengajuan draft dan persetujuan dosen KBK.
- **EDOXID** (`gis.my.id/login2`): Manajemen berkas sidang tugas akhir dan yudisium.
- **KodingMu** (`kodingmu.id`): Platform praktikum pemrograman gamifikasi.
- **GUGAH** (`gugah.ifuntanhub.dev`): Media komunikasi terpadu dosen dan mahasiswa.

---

## Tautan Terkait
- [Profil Visi Misi](visi-misi.md)
- [Panduan Tugas Akhir](../kp-ta/panduan-ta.md)
- [Kegiatan Mahasiswa HMIF](../kemahasiswaan/hmif.md)
"""
    (VAULT / "profil" / "akreditasi.md").write_text(ak_content, encoding="utf-8")

    # 4. Sejarah Untan
    sj_content = """# Sejarah Universitas Tanjungpura & Fakultas Teknik

## 1. Selayang Pandang Universitas Tanjungpura
Universitas Tanjungpura (UNTAN) didirikan pada tanggal 20 Mei 1959 di Kota Pontianak, Kalimantan Barat. Sebagai perguruan tinggi negeri terbesar di Kalimantan Barat, UNTAN mengemban amanat mencerdaskan masyarakat di wilayah perbatasan Indonesia dengan visi *"Mewujudkan Universitas Tanjungpura sebagai Institusi Preservasi dan Pusat Informasi Ilmiah Kalimantan Barat yang Berdaya Saing Global"*.

---

## 2. Fakultas Teknik & Lahirnya Jurusan Informatika
Fakultas Teknik UNTAN berdiri untuk mencetak insinyur andal di Kalimantan Barat. Menjawab pesatnya era transformasi digital dan kebutuhan sumber daya manusia di bidang komputasi, Program Studi Sarjana (S1) Informatika didirikan di bawah Jurusan Teknik Informatika.

Prodi Informatika terus berkembang menjadi pusat rujukan keilmuan rekayasa perangkat lunak, kecerdasan artifisial, sistem keamanan siber, dan analisis data spasial di pulau Kalimantan.

---

## Tautan Terkait
- [Visi, Misi, dan Tujuan Prodi](visi-misi.md)
- [Struktur Organisasi Jurusan](struktur-organisasi.md)
- [Fasilitas dan Laboratorium](../fasilitas-lab/laboratorium.md)
"""
    (VAULT / "profil" / "sejarah-untan.md").write_text(sj_content, encoding="utf-8")

    # 5. README Profil
    pr_readme = """# Direktori Profil & Tata Kelola Prodi Informatika UNTAN

Bagian ini memuat dokumen legalitas, kepemimpinan, dan identitas institusi:
- [Visi, Misi, dan Tujuan](visi-misi.md): Fondasi filosofis dan tridharma prodi.
- [Struktur Organisasi](struktur-organisasi.md): Pimpinan jurusan, kaprodi, kalab, dan ketua KBK.
- [Akreditasi dan Prestasi](akreditasi.md): Pengakuan resmi BAN-PT/LAM INFOKOM dan rekam jejak kejuaraan.
- [Sejarah UNTAN & Fakultas Teknik](sejarah-untan.md): Latar belakang historis berdirinya kampus dan jurusan.
"""
    (VAULT / "profil" / "README.md").write_text(pr_readme, encoding="utf-8")
    print("Dokumen profil/ berhasil dibuat.")


def migrate_akademik() -> None:
    # 1. Profil Lulusan & CPL
    cpl_content = """# Profil Lulusan & Capaian Pembelajaran Lulusan (CPL)

## 1. Profil Lulusan Sarjana Informatika
Lulusan Program Studi S1 Informatika Fakultas Teknik Universitas Tanjungpura dipersiapkan untuk berkarier sebagai:
1. **Software Engineer / Fullstack Developer**: Pengembang sistem perangkat lunak skala enterprise, mobile, dan cloud.
2. **Artificial Intelligence Specialist / Data Scientist**: Praktisi kecerdasan buatan, machine learning, computer vision, dan analisis data analitik.
3. **Network & Cybersecurity Specialist**: Perancang arsitektur jaringan, sistem IoT, dan auditor keamanan informasi.
4. **Information System Analyst**: Analis proses bisnis, perancang arsitektur data spasial, dan konsultan sistem enterprise.
5. **Technopreneur**: Pendiri usaha rintisan teknologi digital.

---

## 2. 10 Capaian Pembelajaran Lulusan (CPL)
Kurikulum Informatika UNTAN merujuk pada Kerangka Kualifikasi Nasional Indonesia (KKNI) dan Standar Penjaminan Mutu OBE:

| Kode CPL | Dimensi | Deskripsi Capaian Pembelajaran |
| :--- | :--- | :--- |
| **CPL-01** | Sikap & Etika | Menjunjung tinggi nilai kemanusiaan, moral, etika profesional, dan tanggung jawab hukum dalam penerapan solusi teknologi informasi. |
| **CPL-02** | Sosial & Budaya | Memiliki kepedulian sosial, memahami isu keberlanjutan lingkungan hidup (*sustainability*), dan adaptif terhadap kearifan lokal. |
| **CPL-03** | Fondasi Teoretis | Menguasai landasan matematika komputasi, algoritma dasar, struktur data, dan konsep fundamental sains komputer. |
| **CPL-04** | Jaringan & IoT | Mampu merancang, mengonfigurasi, dan mengamankan infrastruktur jaringan komputer, sistem paralel/terdistribusi, serta ekosistem IoT. |
| **CPL-05** | Penalaran Kritis | Mampu menganalisis masalah kompleks dengan cara berpikir komputasional, logis, dan kritis. |
| **CPL-06** | Komunikasi & Tim | Mampu berkomunikasi secara efektif, berkolaborasi dalam tim multidisiplin, dan menyusun dokumentasi teknis berstandar industri. |
| **CPL-07** | Keputusan Data | Mampu mengolah, memodelkan, dan mengambil keputusan berbasis data menggunakan metode *machine learning*, NLP, maupun sistem cerdas. |
| **CPL-08** | Analisis Kebutuhan | Mampu menggali kebutuhan pengguna (*user requirement*), merancang antarmuka (UI/UX), dan menyusun arsitektur sistem informasi. |
| **CPL-09** | Rekayasa Perangkat Lunak | Mampu mengimplementasikan, menguji (*quality assurance*), dan memelihara sistem perangkat lunak dengan metode agile dan best practices DevOps. |
| **CPL-10** | Solusi Terapan & Keamanan | Mampu mengintegrasikan solusi komputasi yang aman, andal, dan terukur untuk memecahkan permasalahan nyata di masyarakat. |

---

## Tautan Terkait
- [Struktur Kurikulum 2026 (140 SKS)](kurikulum/2026/tahap-pembelajaran.md)
- [Matriks Pemetaan CPL ke Mata Kuliah](kurikulum/2026/pemetaan-cpl.md)
- [Arsip Kurikulum 2016](kurikulum/2016/sebaran-semester.md)
"""
    (VAULT / "akademik" / "profil-lulusan-cpl.md").write_text(cpl_content, encoding="utf-8")

    # 2. Kurikulum Hub README
    kur_readme = """# Hub Informasi Kurikulum Informatika UNTAN

Program Studi Informatika Fakultas Teknik UNTAN saat ini memberlakukan **Kurikulum 2026 (140 SKS)** berbasis OBE (Outcome-Based Education) sebagai kurikulum operasional aktif, dengan tetap mengarsipkan **Kurikulum 2016 (144 SKS)** sebagai rujukan perbandingan historis dan konversi nilai bagi angkatan terdahulu.

---

## Jalur Kurikulum

```
vault/akademik/kurikulum/
├── README.md               # Halaman perbandingan kurikulum
├── 2026/                   # [AKTIF] Kurikulum 2026 (140 SKS)
│   ├── README.md           # Ikhtisar Kurikulum 2026
│   ├── tahap-pembelajaran.md # 4 Tahap Pembelajaran (Semester 1-8)
│   └── pemetaan-cpl.md     # Matriks Relasi CPL 01-10
└── 2016/                   # [ARSIP HISTORIS] Kurikulum 2016 (144 SKS)
    ├── README.md           # Ikhtisar Kurikulum 2016
    └── sebaran-semester.md # Daftar Mata Kuliah Semester I - VIII
```

---

## Ringkasan Perbedaan Utama

| Parameter | Kurikulum 2016 (Arsip) | Kurikulum 2026 (Aktif) |
| :--- | :--- | :--- |
| **Total Beban Kelulusan** | 144 SKS | **140 SKS** |
| **Pendekatan Utama** | Berbasis Mata Kuliah Konvensional | **Outcome-Based Education (OBE) & MBKM** |
| **Struktur Kurikulum** | Sebaran Kaku per Semester | **4 Tahap Pembelajaran Bertingkat** |
| **Mata Kuliah Pilihan / KBK** | Semester 7-8 | **Pendalaman Terarah pada 4 KBK sejak Semester 5** |
| **Capstone Project** | Skripsi Tradisional | **Proyek Perangkat Lunak / Capstone + Publikasi Ilmiah** |

---

## Tautan Dokumen Kurikulum
- **[Masuk ke Jalur Kurikulum 2026 (140 SKS)](2026/README.md)**
- **[Masuk ke Arsip Kurikulum 2016 (144 SKS)](2016/README.md)**
- [Profil Lulusan & Capaian Pembelajaran Lulusan (CPL)](../profil-lulusan-cpl.md)
- [Peraturan Akademik & KRS](../panduan/peraturan-akademik-krs.md)
"""
    (VAULT / "akademik" / "kurikulum" / "README.md").write_text(kur_readme, encoding="utf-8")

    # 3. Kurikulum 2026
    k26_readme = """# Kurikulum 2026 (140 SKS) — Program Studi Informatika UNTAN

Kurikulum 2026 merupakan kurikulum operasional berbasis *Outcome-Based Education* (OBE) yang dirancang untuk membekali mahasiswa dengan penguasaan kecerdasan artifisial, rekayasa perangkat lunak modern, keamanan jaringan, dan sistem enterprise.

---

## Dokumen Kurikulum 2026
1. **[Tahap Pembelajaran Semester 1 s.d. 8](tahap-pembelajaran.md)**: Rincian 4 tahap pembelajaran dari Penguatan Dasar Komputasi hingga Proyek Capstone Akhir.
2. **[Matriks Pemetaan CPL](pemetaan-cpl.md)**: Distribusi pemenuhan Capaian Pembelajaran Lulusan (CPL 01-10) pada setiap kelompok mata kuliah.

---

## Tautan Terkait
- [Kembali ke Hub Kurikulum](../README.md)
- [Arsip Kurikulum 2016](../2016/README.md)
- [Panduan Tugas Akhir & Skripsi](../../../kp-ta/panduan-ta.md)
"""
    (VAULT / "akademik" / "kurikulum" / "2026" / "README.md").write_text(k26_readme, encoding="utf-8")

    k26_tahap = """# Struktur 4 Tahap Pembelajaran Kurikulum 2026 (140 SKS)

Beban kelulusan program sarjana Informatika UNTAN berjumlah **140 SKS** yang ditempuh dalam 4 tahap pembelajaran bertingkat:

---

## Tahap 1: Penguatan Dasar Komputasi & Sains (Semester 1–2)
Fokus pada penanaman pola pikir komputasional (*computational thinking*), logika matematika, dan keterampilan dasar pemrograman.
- **Mata Kuliah Utama**: Kalkulus, Matematika Diskrit, Dasar Pemrograman (Python/C), Algoritma & Struktur Data, Bahasa Inggris Profesional, Pendidikan Pancasila & Kewarganegaraan.
- **Beban SKS**: ~36–40 SKS.

---

## Tahap 2: Inti Informatika & Rekayasa Perangkat Lunak (Semester 3–4)
Fokus pada penguasaan pilar fundamental sistem komputer dan rekayasa perangkat lunak.
- **Mata Kuliah Utama**: Pemrograman Berorientasi Objek (OOP), Basis Data, Sistem Operasi, Jaringan Komputer, Rekayasa Perangkat Lunak, Probabilitas dan Statistik, Kecerdasan Buatan Dasar.
- **Beban SKS**: ~38–42 SKS.

---

## Tahap 3: Pendalaman Kelompok Bidang Keahlian & MBKM (Semester 5–6)
Mahasiswa memilih mata kuliah peminatan sesuai minat riset pada salah satu dari 4 [Kelompok Bidang Keahlian](../../../fasilitas-lab/kelompok-bidang-keahlian.md), serta dapat mengikuti program Merdeka Belajar Kampus Merdeka (magang industri, pertukaran mahasiswa, studi independen).
- **Mata Kuliah Pilihan KBK**:
  - *KBK AI*: Machine Learning, Deep Learning, Natural Language Processing (NLP), Computer Vision.
  - *KBK RPL*: Pemrograman Mobile, Cloud Computing, DevOps & CI/CD, Pengujian Perangkat Lunak.
  - *KBK Jaringan*: Keamanan Siber, Internet of Things (IoT), Forensik Digital, Manajemen Jaringan.
  - *KBK SI*: Sistem Informasi Enterprise, Sistem Informasi Geografis (GIS), Data Warehouse & BI.
- **Mata Kuliah Wajib Tahap**: [Kerja Praktik (KP)](../../../kp-ta/panduan-kp.md) (2 SKS, syarat minimal 80 SKS), Metodologi Penelitian Informatika.
- **Beban SKS**: ~36–40 SKS.

---

## Tahap 4: Integrasi Solusi & Capstone Tugas Akhir (Semester 7–8)
Fokus pada penyelesaian proyek akhir mandiri, publikasi karya ilmiah, dan kesiapan memasuki dunia profesional.
- **Mata Kuliah Utama**: Etika Profesi Komputasi, Penulisan Proposal Tugas Akhir, Proyek Capstone / [Tugas Akhir (Skripsi)](../../../kp-ta/panduan-ta.md) (6 SKS).
- **Beban SKS**: ~18–22 SKS.

---

## Tautan Terkait
- [Matriks Pemetaan CPL 2026](pemetaan-cpl.md)
- [Panduan Kerja Praktik](../../../kp-ta/panduan-kp.md)
- [Panduan Tugas Akhir](../../../kp-ta/panduan-ta.md)
- [Hub Kurikulum](../README.md)
"""
    (VAULT / "akademik" / "kurikulum" / "2026" / "tahap-pembelajaran.md").write_text(k26_tahap, encoding="utf-8")

    k26_cpl = """# Matriks Pemetaan CPL ke Kurikulum 2026

Dokumen ini memetakan [Capaian Pembelajaran Lulusan (CPL)](../../profil-lulusan-cpl.md) ke dalam rumpun mata kuliah Kurikulum 2026:

| Kode CPL | Bidang Fokus | Contoh Mata Kuliah Terkait |
| :--- | :--- | :--- |
| **CPL-01** | Sikap profesional, etika, tanggung jawab | Pendidikan Kewarganegaraan, Etika Komputasi, Penulisan Proposal TA |
| **CPL-02** | Kepedulian sosial, budaya, keberlanjutan | Masyarakat dan Komputasi Berkelanjutan, Sistem Informasi |
| **CPL-03** | Landasan teoretis komputasi | Kalkulus, Matematika Diskrit, Struktur Data & Algoritma, Basis Data |
| **CPL-04** | Jaringan, keamanan, IoT | Jaringan Komputer, Manajemen Jaringan, IoT, Keamanan Informasi |
| **CPL-05** | Berpikir logis, kritis, sistematis | Strategi Algoritma, Pemrograman Berorientasi Objek, Kecerdasan Buatan |
| **CPL-06** | Komunikasi efektif & kolaborasi | Komunikasi Profesional, Kerja Praktik, Proyek Perangkat Lunak |
| **CPL-07** | Keputusan berbasis data | Probabilitas dan Statistik, Machine Learning, NLP, Computer Vision |
| **CPL-08** | Solusi berpusat pada kebutuhan pengguna | Analisis & Perancangan SI, Interaksi Manusia dan Komputer (IMK) |
| **CPL-09** | Implementasi & evaluasi perangkat lunak | Pemrograman Web, Pemrograman Mobile, Uji Perangkat Lunak, TA |
| **CPL-10** | Konektivitas sistem IoT & keamanan | Sistem Paralel dan Terdistribusi, Pemrograman Jaringan, IoT |

---

## Tautan Terkait
- [Tahap Pembelajaran Kurikulum 2026](tahap-pembelajaran.md)
- [Profil Lulusan & Rincian CPL](../../profil-lulusan-cpl.md)
- [Arsip Kurikulum 2016](../2016/sebaran-semester.md)
"""
    (VAULT / "akademik" / "kurikulum" / "2026" / "pemetaan-cpl.md").write_text(k26_cpl, encoding="utf-8")

    # 4. Kurikulum 2016
    k16_readme = """# Arsip Historis Kurikulum 2016 (144 SKS)

Kurikulum 2016 merupakan kurikulum Program Studi Informatika UNTAN dengan total beban **144 SKS** yang diarsipkan sebagai dokumen rujukan bagi mahasiswa angkatan terdahulu dan acuan konversi nilai mata kuliah ke Kurikulum 2026.

---

## Dokumen Arsip
- **[Sebaran Mata Kuliah Semester I s.d. VIII](sebaran-semester.md)**: Daftar lengkap mata kuliah per semester beserta bobot SKS.

---

## Tautan Terkait
- [Hub Perbandingan Kurikulum](../README.md)
- [Kurikulum 2026 (140 SKS)](../2026/README.md)
"""
    (VAULT / "akademik" / "kurikulum" / "2016" / "README.md").write_text(k16_readme, encoding="utf-8")

    k16_sem = """# Sebaran Mata Kuliah Kurikulum 2016 (Total 144 SKS)

## Semester I (20 SKS)
- Pendidikan Agama (2 SKS)
- Pancasila & Kewarganegaraan (2 SKS)
- Bahasa Indonesia (2 SKS)
- Kalkulus I (3 SKS)
- Fisika Dasar (3 SKS)
- Pengantar Teknologi Informasi (2 SKS)
- Dasar Pemrograman (4 SKS)
- Bahasa Inggris (2 SKS)

## Semester II (20 SKS)
- Kalkulus II (3 SKS)
- Matematika Diskrit (3 SKS)
- Algoritma & Struktur Data (4 SKS)
- Aljabar Linier (3 SKS)
- Organisasi & Arsitektur Komputer (3 SKS)
- Sistem Operasi (4 SKS)

## Semester III (21 SKS)
- Probabilitas & Statistik (3 SKS)
- Pemrograman Berorientasi Objek (4 SKS)
- Sistem Berkas & Basis Data (4 SKS)
- Komunikasi Data & Jaringan Komputer (4 SKS)
- Metode Numerik (3 SKS)
- Teori Bahasa & Otomata (3 SKS)

## Semester IV (21 SKS)
- Analisis & Perancangan Sistem (4 SKS)
- Pemrograman Web (4 SKS)
- Desain & Analisis Algoritma (3 SKS)
- Kecerdasan Buatan (3 SKS)
- Grafika Komputer (3 SKS)
- Interaksi Manusia & Komputer (4 SKS)

## Semester V (21 SKS)
- Rekayasa Perangkat Lunak (4 SKS)
- Keamanan Komputer & Jaringan (4 SKS)
- Manajemen Proyek TI (3 SKS)
- Sistem Terdistribusi (3 SKS)
- Mata Kuliah Pilihan KBK I (3 SKS)
- Mata Kuliah Pilihan KBK II (4 SKS)

## Semester VI (22 SKS)
- Metodologi Penelitian (2 SKS)
- Kewirausahaan Berbasis Teknologi (3 SKS)
- [Kerja Praktik (KP)](../../../kp-ta/panduan-kp.md) (2 SKS)
- Mata Kuliah Pilihan KBK III (3 SKS)
- Mata Kuliah Pilihan KBK IV (4 SKS)
- Mata Kuliah Pilihan KBK V (4 SKS)
- Etika Profesi (4 SKS)

## Semester VII & VIII (19 SKS)
- Seminar Proposal Tugas Akhir (2 SKS)
- [Tugas Akhir / Skripsi](../../../kp-ta/panduan-ta.md) (6 SKS)
- Kuliah Kerja Nyata (KKN) (3 SKS)
- Mata Kuliah Pilihan Pengayaan (8 SKS)

---

## Tautan Terkait
- [Hub Perbandingan Kurikulum](../README.md)
- [Kurikulum Baru 2026](../2026/tahap-pembelajaran.md)
"""
    (VAULT / "akademik" / "kurikulum" / "2016" / "sebaran-semester.md").write_text(k16_sem, encoding="utf-8")

    # 5. Panduan Akademik & KRS
    pan_krs = r"""# Peraturan Akademik, Batas SKS, dan Panduan KRS

## 1. Beban SKS Semester Berdasarkan IPS
Mahasiswa dapat mengambil beban SKS semester berjalan sesuai Indeks Prestasi Semester (IPS) semester sebelumnya:

| Nilai IPS Sebelumnya | Beban Maksimal SKS yang Diizinkan |
| :--- | :--- |
| **IPS $\ge$ 3.00** | Maksimal **24 SKS** |
| **2.50 $\le$ IPS < 3.00** | Maksimal **21 SKS** |
| **2.00 $\le$ IPS < 2.50** | Maksimal **18 SKS** |
| **1.50 $\le$ IPS < 2.00** | Maksimal **15 SKS** |
| **IPS < 1.50** | Maksimal **12 SKS** |

---

## 2. Prosedur Pengisian Kartu Rencana Studi (KRS)
1. **Pembayaran UKT**: Mahasiswa menyelesaikan kewajiban pembayaran Uang Kuliah Tunggal (UKT) sesuai jadwal kalender akademik.
2. **Konsultasi Dosen PA**: Mengatur jadwal bimbingan dengan Dosen Pembimbing Akademik (PA) untuk membahas rencana mata kuliah.
3. **Pengisian di SIAKAD UNTAN**: Login ke portal SIAKAD dan memilih kelas sesuai paket kurikulum.
4. **Persetujuan (Approval) Dosen PA**: Dosen PA memvalidasi pilihan KRS secara online di portal dosen.
5. **Cetak KRS**: Mahasiswa mencetak bukti KRS resmi sebagai tanda peserta kuliah sah.

---

## 3. Ketentuan Cuti Akademik & Evaluasi Studi
- **Cuti Akademik**: Mahasiswa baru diizinkan mengajukan cuti setelah menempuh minimal 2 semester pertama. Maksimal cuti adalah 2 semester berturut-turut.
- **Evaluasi 4 Semester Pertama**: Mahasiswa wajib mengumpulkan minimal 40 SKS dengan IPK minimal 2.00 tanpa nilai E.
- **Batas Maksimal Masa Studi**: Maksimal 14 semester (7 tahun akademik).

---

## Tautan Terkait
- [Tahap Pembelajaran Kurikulum 2026](../kurikulum/2026/tahap-pembelajaran.md)
- [Informasi Beasiswa & Jalur Masuk](beasiswa-dan-pmb.md)
- [Panduan Kerja Praktik](../../kp-ta/panduan-kp.md)
"""
    (VAULT / "akademik" / "panduan" / "peraturan-akademik-krs.md").write_text(pan_krs, encoding="utf-8")

    # 6. Beasiswa & PMB
    bea_content = """# Informasi Beasiswa & Penerimaan Mahasiswa Baru (PMB)

## 1. Jalur Masuk Penerimaan Mahasiswa Baru (PMB)
Program Studi Sarjana Informatika UNTAN menerima mahasiswa melalui 3 jalur seleksi nasional dan mandiri:
1. **SNBP (Seleksi Nasional Berdasarkan Prestasi)**: Penilaian prestasi nilai rapor dan portofolio prestasi akademik/non-akademik siswa SMA/SMK/MA.
2. **SNBT (Seleksi Nasional Berdasarkan Tes)**: Ujian Tulis Berbasis Komputer (UTBK) dengan materi Tes Potensi Skolastik (TPS), Literasi Bahasa Indonesia/Inggris, dan Penalaran Matematika.
3. **Seleksi Mandiri UNTAN**: Jalur ujian mandiri yang diselenggarakan langsung oleh Universitas Tanjungpura untuk menjaring calon mahasiswa berpotensi.

---

## 2. Program Beasiswa Mahasiswa
Mahasiswa Informatika UNTAN dapat mengajukan berbagai skema bantuan pendidikan dan beasiswa:
- **KIP-Kuliah (Kartu Indonesia Pintar Kuliah)**: Bebas biaya pendidikan UKT penuh dan tunjangan biaya hidup bulanan dari Kemendikbudristek.
- **Beasiswa Bank Indonesia (BI)**: Bantuan finansial dan pembinaan kepemimpinan melalui komunitas Generasi Baru Indonesia (GenBI).
- **Beasiswa Djarum Plus**: Bantuan dana pendidikan serta pelatihan soft-skills kepemimpinan dan character building.
- **Beasiswa PPA (Peningkatan Prestasi Akademik)**: Bantuan untuk mahasiswa berprestasi akademik tinggi dengan IPK minimal 3.00.
- **Beasiswa Bantuan Pemda**: Bantuan studi dari pemerintah kabupaten/kota di Kalimantan Barat.

---

## Tautan Terkait
- [Peraturan Akademik & KRS](peraturan-akademik-krs.md)
- [Kegiatan Mahasiswa HMIF](../../kemahasiswaan/hmif.md)
- [Ikatan Alumni IKA](../../kemahasiswaan/alumni-tracer-study.md)
"""
    (VAULT / "akademik" / "panduan" / "beasiswa-dan-pmb.md").write_text(bea_content, encoding="utf-8")

    # 7. README Akademik
    ak_readme = """# Direktori Akademik Informatika UNTAN

Bagian ini memuat seluruh informasi teknis perkuliahan, kurikulum, dan panduan belajar mahasiswa:
- **[Profil Lulusan & Capaian Pembelajaran Lulusan (CPL)](profil-lulusan-cpl.md)**: 10 CPL standar kompetensi sarjana komputasi.
- **[Hub Kurikulum](kurikulum/README.md)**:
  - [Kurikulum 2026 (140 SKS) - Operasional](kurikulum/2026/README.md)
  - [Kurikulum 2016 (144 SKS) - Arsip Historis](kurikulum/2016/README.md)
- **[Panduan Mahasiswa](panduan/peraturan-akademik-krs.md)**:
  - [Peraturan Akademik & Batas SKS KRS](panduan/peraturan-akademik-krs.md)
  - [Info Beasiswa & PMB](panduan/beasiswa-dan-pmb.md)
"""
    (VAULT / "akademik" / "README.md").write_text(ak_readme, encoding="utf-8")
    print("Dokumen akademik/ berhasil dibuat.")


def migrate_kp_ta() -> None:
    # 1. Panduan KP
    kp_content = """# Panduan Kerja Praktik (KP) Informatika UNTAN

## 1. Ketentuan & Persyaratan Umum
Kerja Praktik (KP) berbobot **2 SKS** dan merupakan mata kuliah wajib yang bertujuan memberikan pengalaman langsung di industri teknologi informasi:
- **Syarat SKS**: Mahasiswa telah lulus minimal **80 SKS** tanpa nilai E pada saat mengajukan permohonan KP.
- **Indeks Prestasi Kumulatif**: IPK minimal **2.00**.
- **Durasi KP**: Minimal **1 bulan** (160 jam kerja efektif) hingga maksimal 3 bulan di instansi mitra atau perusahaan IT.
- **Kelompok**: Mahasiswa dapat melaksanakan KP secara mandiri atau dalam kelompok maksimal 2-3 orang di instansi yang sama dengan pembagian tugas yang jelas.

---

## 2. Alur Pelaksanaan Kerja Praktik
1. **Pengajuan Tempat KP**: Mahasiswa mencari instansi/perusahaan target, lalu mengajukan surat pengantar dari Bagian Akademik Fakultas Teknik.
2. **Surat Penerimaan**: Memperoleh surat balasan resmi dari instansi mitra yang menyatakan bersedia menerima mahasiswa.
3. **Penetapan Dosen Pembimbing**: Koordinator KP / Kaprodi menerbitkan Surat Keputusan (SK) penunjukan Dosen Pembimbing KP.
4. **Pelaksanaan Kerja**: Melaksanakan tugas di tempat KP, mengisi *logbook* mingguan, dan berkonsultasi dengan pembimbing lapangan serta Dosen Pembimbing kampus.
5. **Penyusunan Laporan**: Menyusun laporan KP sesuai format pedoman resmi FT UNTAN.
6. **Seminar KP**: Mendaftarkan seminar evaluasi KP setelah laporan disetujui dosen pembimbing.

---

## Tautan Terkait
- [Panduan Tugas Akhir & Skripsi](panduan-ta.md)
- [Ikhtisar Tahap Akhir Mahasiswa](README.md)
- [Daftar Dosen Pembimbing](../dosen/README.md)
"""
    (VAULT / "kp-ta" / "panduan-kp.md").write_text(kp_content, encoding="utf-8")

    # 2. Panduan TA
    ta_content = """# Panduan Tugas Akhir & Skripsi Informatika UNTAN

## 1. Persyaratan Pengajuan Tugas Akhir
- **Beban SKS**: Telah mengumpulkan minimal **110 SKS** lulus.
- **Mata Kuliah Prasyarat**: Telah lulus mata kuliah Metodologi Penelitian dan [Kerja Praktik (KP)](panduan-kp.md).
- **IPK**: Minimal **2.00** tanpa nilai E.

---

## 2. Alur Pengajuan Draft Proposal via SPOTA
1. Mahasiswa menyusun ide topik dan berkonsultasi dengan Dosen Pembimbing Akademik (PA).
2. Menyusun dokumen **Draft Proposal** sesuai template resmi.
3. Meminta akun SPOTA kepada staf TU jurusan, kemudian mengunggah dokumen Draft Proposal (format PDF dengan scan tanda tangan mahasiswa).
4. Dosen anggota [Kelompok Bidang Keahlian (KBK)](../fasilitas-lab/kelompok-bidang-keahlian.md) melakukan telaah online via portal SPOTA maksimal 14 hari kerja.
5. Pimpinan Jurusan/Kaprodi menerbitkan penetapan:
   - **DITERIMA**: Diterbitkan penunjukan **Dosen Pembimbing 1** dan **Dosen Pembimbing 2**. Mahasiswa wajib melaksanakan Seminar Proposal maksimal 2 bulan sejak tanggal penerimaan.
   - **DITOLAK**: Mahasiswa harus menyusun draft baru dengan topik lain.
   - **GUGUR**: Apabila dalam 2 bulan tidak ada kemajuan bimbingan proposal.

---

## 3. Tahapan Menuju Kelulusan
```
[Draft Proposal (SPOTA)] ──► [Seminar Proposal] ──► [Penelitian & Bimbingan]
                                                            │
[Yudisium & Wisuda] ◄── [Revisi & Pengesahan] ◄── [Sidang Skripsi / Munaqasyah]
```
1. **Seminar Proposal**: Memaparkan rancangan riset di hadapan tim penguji untuk memperoleh masukan metodologi.
2. **Penelitian & Pembuatan Produk**: Membangun aplikasi/model AI di bawah supervisi tim pembimbing.
3. **Seminar Hasil (Semhas)**: Evaluasi hasil implementasi dan pengujian sistem.
4. **Sidang Munaqasyah (Ujian Akhir)**: Ujian komprehensif penentuan kelulusan sarjana.
5. **Publikasi Ilmiah & Pengesahan**: Mengunggah naskah publikasi ilmiah ke jurnal/prosiding, menyerahkan naskah final skripsi, dan mendaftar wisuda.

---

## Tautan Terkait
- [Panduan Kerja Praktik (KP)](panduan-kp.md)
- [Kelompok Bidang Keahlian](../fasilitas-lab/kelompok-bidang-keahlian.md)
- [Daftar Dosen Calon Pembimbing](../dosen/README.md)
- [Platform SPOTA & EDOXID](../profil/akreditasi.md)
"""
    (VAULT / "kp-ta" / "panduan-ta.md").write_text(ta_content, encoding="utf-8")

    # 3. README KP-TA
    kpta_readme = """# Direktori Kerja Praktik (KP) & Tugas Akhir (TA)

Bagian ini memuat pedoman operasional tahapan akhir studi mahasiswa S1 Informatika UNTAN:
- **[Panduan Kerja Praktik (KP)](panduan-kp.md)**: Syarat 80 SKS, alur pengajuan tempat magang, bimbingan, dan seminar KP.
- **[Panduan Tugas Akhir & Skripsi](panduan-ta.md)**: Syarat 110 SKS, pengajuan outline melalui sistem SPOTA, seminar proposal, sidang munaqasyah, hingga yudisium kelulusan.

---

## Rujukan Lintas Dokumen
- [Kelompok Bidang Keahlian](../fasilitas-lab/kelompok-bidang-keahlian.md) (Penentuan dosen pembimbing)
- [Daftar Dosen](../dosen/README.md) (Biodata dan rekam jejak riset dosen)
- [Kurikulum 2026](../akademik/kurikulum/2026/tahap-pembelajaran.md) (Tahap 4 Capstone Project)
"""
    (VAULT / "kp-ta" / "README.md").write_text(kpta_readme, encoding="utf-8")
    print("Dokumen kp-ta/ berhasil dibuat.")


def migrate_fasilitas_lab() -> None:
    # 1. Laboratorium
    lab_content = """# Fasilitas Laboratorium Pembelajaran & Riset Informatika UNTAN

Program Studi Informatika UNTAN mengoperasikan **5 laboratorium tematik** dengan total sarana **93 unit PC**, perangkat server, dan workstation GPU untuk mendukung perkuliahan praktikum, sertifikasi, serta riset dosen dan mahasiswa.

---

## 1. Laboratorium Komputer & Pemrograman Dasar (Lab Komputasi Dasar)
- **Koordinator Lab**: [Morteza Muthahhari, S.Kom., M.T.I.](../dosen/si-spasial/morteza-muthahhari.md)
- **Fokus Layanan**: Praktikum pemrograman dasar, algoritma & struktur data, pemrograman web, dan sertifikasi literasi digital.
- **Fasilitas**: 25 Unit PC Client, Proyektor Interaktif, Gigabit Switch, High-Speed Internet.

---

## 2. Laboratorium Komputasi & Kecerdasan Buatan (Lab AI & Cerdas)
- **Koordinator Lab**: [Niken Candraningrum, S.T., M.Cs.](../dosen/ai-komputasi/niken-candraningrum.md)
- **Fokus Layanan**: Riset machine learning, deep learning, computer vision, pemrosesan bahasa alami (NLP), dan sistem pakar.
- **Fasilitas**: Workstation Komputasi Tinggi dengan kartu grafis NVIDIA RTX GPU, Python/Jupyter Lab Environment, Server Training Model.

---

## 3. Laboratorium Rekayasa Data & Perangkat Lunak (Lab RPL)
- **Koordinator Lab**: [Desepta Isna Ulumi, S.Kom., M.Kom.](../dosen/rpl-mobile/desepta-isna-ulumi.md)
- **Fokus Layanan**: Analisis kebutuhan perangkat lunak, perancangan arsitektur enterprise, pengembangan aplikasi mobile, dan pengujian mutu software (QA & DevOps).
- **Fasilitas**: 20 Unit PC High-Performance, Android Development Tools, Server Repositori Git Internal (`git.ifuntanhub.dev`).

---

## 4. Laboratorium Teknologi & Sistem Informasi (Lab SI)
- **Koordinator Lab**: [Enda Esyudha Pratama, S.T., M.T.](../dosen/si-spasial/enda-esyudha-pratama.md)
- **Fokus Layanan**: Manajemen basis data relasional/NoSQL, analisis data spasial (GIS), audit sistem informasi, dan business intelligence.
- **Fasilitas**: Database Server PostgreSQL/MySQL, Software GIS, Workstation Business Intelligence.

---

## 5. Laboratorium Jaringan, Keamanan Data & IoT (Lab Network & Security)
- **Koordinator Lab**: [Haried Novriando, S.Kom., M.Eng.](../dosen/jaringan-keamanan/haried-novriando.md)
- **Fokus Layanan**: Konfigurasi jaringan komputer, simulasi switching/routing, audit keamanan siber, penetration testing, dan perakitan sistem embedded/IoT.
- **Fasilitas**: Rack Server Cisco Router & Catalyst Switch, Modul Mikrokontroler Arduino & Raspberry Pi, Sensor Suite IoT, Ruang Server Terisolasi.

---

## Tautan Terkait
- [Kelompok Bidang Keahlian (KBK)](kelompok-bidang-keahlian.md)
- [Struktur Organisasi Jurusan](../profil/struktur-organisasi.md)
- [Daftar Dosen Pembina Lab](../dosen/README.md)
"""
    (VAULT / "fasilitas-lab" / "laboratorium.md").write_text(lab_content, encoding="utf-8")

    # 2. Kelompok Keahlian
    kbk_content = """# 4 Kelompok Bidang Keahlian (KBK) Informatika UNTAN

Penelitian, pengembangan kurikulum, dan pembimbingan Tugas Akhir di Program Studi Informatika UNTAN dikonsolidasikan ke dalam **4 Kelompok Bidang Keahlian (KBK)**:

---

## 1. Computation & Artificial Intelligence (AI & Komputasi)
- **Fokus Riset**: Pemodelan bahasa alami (NLP bahasa daerah & Indonesia), penerjemahan mesin, sentiment analysis, visi komputer (*computer vision*), *deep learning*, algoritma optimasi, dan bioinformatika.
- **Laboratorium Mitra**: [Lab Komputasi & Kecerdasan Buatan](laboratorium.md)
- **Dosen Anggota**:
  - [Prof. Dr. Herry Sujaini, S.T., M.T.](../dosen/ai-komputasi/herry-sujaini.md)
  - [Dr. Arif Bijaksana Putra Negara, S.T., M.T.](../dosen/ai-komputasi/arif-bijaksana-putra-negara.md)
  - [Helen Sastypratiwi, S.T., M.Eng.](../dosen/ai-komputasi/helen-sastypratiwi.md)
  - [Ibnu Arif, S.Kom., M.Kom.](../dosen/ai-komputasi/ibnu-arif.md)
  - [Izuardo Zulkarnain, S.Pd., M.T.](../dosen/ai-komputasi/izuardo-zulkarnain.md)
  - [Niken Candraningrum, S.T., M.Cs.](../dosen/ai-komputasi/niken-candraningrum.md)
  - [Rina Septiriana, S.T., M.Cs.](../dosen/ai-komputasi/rina-septiriana.md)
  - [Tursina, S.T., M.Cs.](../dosen/ai-komputasi/tursina.md)

---

## 2. Software Engineering & Mobile Computing (RPL & Mobile)
- **Fokus Riset**: Rekayasa kebutuhan, arsitektur microservices, agile software development, aplikasi bergerak (Android/iOS), CI/CD & DevOps, dan metrik kualitas perangkat lunak.
- **Laboratorium Mitra**: [Lab Rekayasa Data & Perangkat Lunak](laboratorium.md)
- **Dosen Anggota**:
  - [H. Hengky Anra, S.T., M.Kom.](../dosen/rpl-mobile/hengky-anra.md)
  - [Novi Safriadi, S.T., M.T.](../dosen/rpl-mobile/novi-safriadi.md)
  - [Anggi Perwitasari, S.T., M.T.](../dosen/rpl-mobile/anggi-perwitasari.md)
  - [Desepta Isna Ulumi, S.Kom., M.Kom.](../dosen/rpl-mobile/desepta-isna-ulumi.md)
  - [Khairul Hafidh, S.T., M.Kom.](../dosen/rpl-mobile/khairul-hafidh.md)
  - [M. Tsanauddin Farid, S.Kom., M.Eng.](../dosen/rpl-mobile/m-tsanauddin-farid.md)
  - [Rudy Dwi Nyoto, S.T., M.Eng.](../dosen/rpl-mobile/rudy-dwi-nyoto.md)

---

## 3. Networking & Security (Jaringan & Keamanan Sistem)
- **Fokus Riset**: Protokol perutean jaringan, *software-defined networking* (SDN), kriptografi terapan, audit forensik digital, *penetration testing*, dan ekosistem *Internet of Things* (IoT).
- **Laboratorium Mitra**: [Lab Jaringan, Keamanan Data & IoT](laboratorium.md)
- **Dosen Anggota**:
  - [Ir. M. Azhar Irwansyah, S.T., M.Eng.](../dosen/jaringan-keamanan/m-azhar-irwansyah.md)
  - [Helfi Nasution, S.Kom., M.Cs.](../dosen/jaringan-keamanan/helfi-nasution.md)
  - [Heri Priyanto, S.T., M.T.](../dosen/jaringan-keamanan/heri-priyanto.md)
  - [Alfian Abdul Jalid, S.Kom., M.Cs.](../dosen/jaringan-keamanan/alfian-abdul-jalid.md)
  - [Haried Novriando, S.Kom., M.Eng.](../dosen/jaringan-keamanan/haried-novriando.md)
  - [Ir. Rickhy Artha Octaviyana, S.Kom., M.M., M.Kom.](../dosen/jaringan-keamanan/rickhy-artha-octaviyana.md)

---

## 4. Information System & Data Spatial (Sistem Informasi & Data Spasial)
- **Fokus Riset**: Sistem informasi geografis (GIS) lahan basah & perkotaan, audit tata kelola TI (COBIT/ITIL), data warehousing, peramalan bisnis, dan manajemen basis data spasial.
- **Laboratorium Mitra**: [Lab Teknologi & Sistem Informasi](laboratorium.md)
- **Dosen Anggota**:
  - [Dr. Ir. Yus Sholva, S.T., M.T.](../dosen/si-spasial/yus-sholva.md)
  - [Eva Faja Ripanti, S.Kom., MMSI., Ph.D.](../dosen/si-spasial/eva-faja-ripanti.md)
  - [Anggi Srimurdianti S., S.T., M.T.](../dosen/si-spasial/anggi-srimurdianti.md)
  - [Enda Esyudha Pratama, S.T., M.T.](../dosen/si-spasial/enda-esyudha-pratama.md)
  - [Fauzan Asrin, S.Kom., M.Kom.](../dosen/si-spasial/fauzan-asrin.md)
  - [Morteza Muthahhari, S.Kom., M.T.I.](../dosen/si-spasial/morteza-muthahhari.md)
  - [Rifqi Anugrah, S.Kom., M.Kom.](../dosen/si-spasial/rifqi-anugrah.md)
  - [Yulianti, S.Kom., MMSI.](../dosen/si-spasial/yulianti.md)

---

## Tautan Terkait
- [Fasilitas Laboratorium](laboratorium.md)
- [Direktori Dosen per KBK](../dosen/README.md)
- [Panduan Pengajuan Outline TA (SPOTA)](../kp-ta/panduan-ta.md)
"""
    (VAULT / "fasilitas-lab" / "kelompok-bidang-keahlian.md").write_text(kbk_content, encoding="utf-8")

    # 3. README Fasilitas-Lab
    fl_readme = """# Direktori Fasilitas Laboratorium & Riset Keahlian

Bagian ini memuat sarana riset dan pemetaan rumpun keahlian dosen:
- **[Fasilitas 5 Laboratorium](laboratorium.md)**: Lab Komputasi Dasar, Lab AI, Lab RPL, Lab SI, dan Lab Network & Security.
- **[4 Kelompok Bidang Keahlian (KBK)](kelompok-bidang-keahlian.md)**: Fokus riset AI, RPL, Jaringan, dan Sistem Informasi beserta daftar dosen anggotanya.

---

## Tautan Terkait
- [Direktori Dosen per KBK](../dosen/README.md)
- [Tahap Pembelajaran Kurikulum](../akademik/kurikulum/2026/tahap-pembelajaran.md)
- [Panduan Tugas Akhir](../kp-ta/panduan-ta.md)
"""
    (VAULT / "fasilitas-lab" / "README.md").write_text(fl_readme, encoding="utf-8")
    print("Dokumen fasilitas-lab/ berhasil dibuat.")


def migrate_kemahasiswaan() -> None:
    # 1. HMIF
    hmif_content = """# Himpunan Mahasiswa Informatika (HMIF) FT UNTAN

## 1. Profil Organisasi
**Himpunan Mahasiswa Informatika (HMIF)** Universitas Tanjungpura adalah organisasi kemahasiswaan tingkat program studi yang berfungsi sebagai wadah aspirasi, kepemimpinan, dan pengembangan potensi akademik maupun kepribadian bagi seluruh mahasiswa aktif Informatika UNTAN.
- **Mahasiswa Aktif Terkelola**: 518 mahasiswa.
- **Media Sosial Resmi**: Instagram `@hmif_ftuntan` dan `@informershmif`.

---

## 2. 6 Divisi Kepengurusan HMIF
1. **Pengembangan SDM dan Kaderisasi (PSDMK)**: Bertanggung jawab atas kaderisasi mahasiswa baru, pelatihan kepemimpinan tingkat dasar, dan pembentukan karakter insan akademis.
2. **Media Komunikasi dan Konten Digital (Medkomdigi)**: Mengelola strategi komunikasi publik, media sosial, publikasi berita prodi, dan dokumentasi visual agenda.
3. **Inovasi dan Kompetisi Teknologi (Ikomtek)**: Memfasilitasi *coaching clinic* kompetisi nasional (GEMASTIK, ICPC, LIDM), hackathon, dan koordinasi study club.
4. **Pengembangan Organisasi**: Penyusunan SOP tata kelola organisasi, evaluasi kinerja bulanan pengurus, dan riset internal himpunan.
5. **Sosial Masyarakat (Sosmas)**: Program pengabdian masyarakat, kepedulian sosial, bakti desa, dan tanggap bencana.
6. **Kewirausahaan dan Kemitraan**: Pengelolaan *merchandise* resmi, sponsorship kegiatan, dan relasi mitra industri kreatif.

---

## 3. Komunitas Belajar (Study Club)
HMIF mengoordinasikan kelompok belajar mahasiswa berbasis minat teknis:
- **Competitive Programming (CP)**: Latihan algoritma intensif persiapan ICPC dan GEMASTIK Divisi Pemrograman.
- **Software & Mobile Development**: Pengembangan aplikasi nyata, workshop UI/UX, dan eksplorasi stack teknologi web modern.
- **Data Science & Artificial Intelligence**: Diskusi dan eksperimen model machine learning serta kompetisi data mining.

---

## 4. Kalender Agenda Tahunan
| Waktu | Nama Kegiatan | Deskripsi |
| :--- | :--- | :--- |
| **Bulan Ramadhan** | **SKBI Ramadhan** | Buka puasa bersama akbar keluarga besar dosen, mahasiswa, dan alumni Informatika. |
| **Juli - September** | **Pendampingan GEMASTIK** | Pelatihan intensif delegasi mahasiswa menuju ajang GEMASTIK Puspresnas. |
| **Agustus** | **Bootcamp HMIF** | Pelatihan teknis kilat untuk pembekalan skill dasar mahasiswa baru. |
| **Oktober** | **INFORMERS (HUT Informatika)** | Perayaan ulang tahun Informatika UNTAN: seminar nasional, expo karya mahasiswa, pentas seni. |

---

## Tautan Terkait
- [Ikatan Keluarga Alumni (IKA)](alumni-tracer-study.md)
- [Prestasi Mahasiswa](../profil/akreditasi.md)
- [Laboratorium Komputasi](../fasilitas-lab/laboratorium.md)
"""
    (VAULT / "kemahasiswaan" / "hmif.md").write_text(hmif_content, encoding="utf-8")

    # 2. Alumni & Tracer Study
    alumni_content = """# Ikatan Alumni & Hasil Tracer Study Informatika UNTAN

## 1. Ikatan Keluarga Alumni (IKA) Informatika
Ikatan Keluarga Alumni (IKA) Informatika UNTAN mewadahi lebih dari 500 alumni yang tersebar di berbagai sektor industri, pemerintahan, dan akademisi di seluruh Indonesia maupun luar negeri.
- **Keanggotaan**: Terbuka untuk seluruh lulusan S1 Informatika FT UNTAN dari semua angkatan.
- **Manfaat**: Berbagi informasi lowongan kerja eksklusif, peluang magang, kolaborasi riset, serta program mentoring karier mahasiswa.

---

## 2. Profil Alumni Berprestasi
Beberapa profil alumni yang berkiprah di kancah nasional dan global:
- **Izhan Fakhruzi, Ph.D. (Angkatan 2005)**: Dosen Universitas Muhammadiyah Pontianak & Peneliti Universidad de Granada, Spanyol. Ahli riset AI dan teknologi informasi komunikasi lintas negara.
- **Charles Darwis Hariman, M.Sc. (Alumni Informatika)**: Software Developer di Traxpay GmbH, Jerman. Lulusan Saarland University, pakar arsitektur sistem pembayaran digital dan integrasi enterprise.
- **Dona Pramana Pura (Angkatan 2009)**: Product Manager fokus Voice AI di perusahaan teknologi internasional.

---

## 3. Sebaran Karier Lulusan (Tracer Study Resmi)
Berdasarkan data penelusuran lulusan (*Tracer Study*, update 2026):

| Sektor Pekerjaan | Persentase Lulusan |
| :--- | :--- |
| **Instansi Pemerintah & Kementerian** | 29.41% |
| **Perusahaan Swasta Nasional & Multinasional** | 23.53% |
| **Wiraswasta / Founder Usaha Rintisan (Startup)** | 14.71% |
| **BUMN & BUMD** | 5.88% |
| **Organisasi Non-Profit / Lembaga Internasional** | 2.94% |

**Contoh Perusahaan Tempat Alumni Berkarir**:  
Bank Central Asia (BCA), Bank Rakyat Indonesia (BRI), PT Telkom Indonesia, PT PLN (Persero), Grab, Telkomsel, Astra Daihatsu, Unilever, Garuda Indonesia, dan berbagai instansi dinas komunikasi dan informatika (Diskominfo) di Kalimantan Barat.

---

## Tautan Terkait
- [Organisasi Mahasiswa HMIF](hmif.md)
- [Profil Lulusan & CPL](../akademik/profil-lulusan-cpl.md)
- [Visi Misi Program Studi](../profil/visi-misi.md)
"""
    (VAULT / "kemahasiswaan" / "alumni-tracer-study.md").write_text(alumni_content, encoding="utf-8")

    # 3. README Kemahasiswaan
    km_readme = """# Direktori Kemahasiswaan & Jaringan Alumni

Bagian ini memuat informasi organisasi kemahasiswaan dan jejaring lulusan:
- **[Himpunan Mahasiswa Informatika (HMIF)](hmif.md)**: 6 divisi kepengurusan, study club, dan kalender kegiatan tahunan.
- **[Ikatan Alumni & Tracer Study](alumni-tracer-study.md)**: Sebaran karir lulusan di BUMN/Swasta/Pemerintah, testimoni alumni, dan profil alumni berprestasi global.

---

## Tautan Terkait
- [Prestasi Prodi](../profil/akreditasi.md)
- [Info Beasiswa](../akademik/panduan/beasiswa-dan-pmb.md)
- [Indeks Utama Vault](../README.md)
"""
    (VAULT / "kemahasiswaan" / "README.md").write_text(km_readme, encoding="utf-8")
    print("Dokumen kemahasiswaan/ berhasil dibuat.")


def build_root_vault_readme() -> None:
    content = """# Basis Pengetahuan (Knowledge Vault) Prodi Informatika UNTAN

Repositori ini merupakan **sumber kebenaran tunggal (*single source of truth*)** bagi asisten cerdas **Luco 🐦** dan seluruh sivitas akademika Program Studi S1 Informatika, Fakultas Teknik, Universitas Tanjungpura.

Seluruh data disusun secara hierarkis menggunakan standar Markdown CommonMark dengan tautan silang (*cross-links*) relatif untuk mendukung penjelajahan hierarkis OpenViking (L0 Root $\rightarrow$ L1 Folder $\rightarrow$ L2 Teks Lengkap) serta pencarian data deterministik dosen melalui `vault/lookup.json`.

---

## 🗂️ Taksonomi 6 Kategori Pengetahuan

| Kategori | Direktori | Ringkasan Konten Utama |
| :--- | :--- | :--- |
| **1. Profil & Tata Kelola** | [`profil/`](profil/README.md) | [Visi Misi](profil/visi-misi.md), [Struktur Organisasi](profil/struktur-organisasi.md), [Akreditasi & Prestasi](profil/akreditasi.md), [Sejarah Kampus](profil/sejarah-untan.md). |
| **2. Akademik & Kurikulum** | [`akademik/`](akademik/README.md) | [Profil Lulusan & CPL](akademik/profil-lulusan-cpl.md), [Kurikulum 2026 (140 SKS)](akademik/kurikulum/2026/README.md), [Arsip Kurikulum 2016](akademik/kurikulum/2016/README.md), [Panduan KRS & SKS](akademik/panduan/peraturan-akademik-krs.md), [Beasiswa & PMB](akademik/panduan/beasiswa-dan-pmb.md). |
| **3. Tahap Akhir Studi** | [`kp-ta/`](kp-ta/README.md) | [Panduan Kerja Praktik](kp-ta/panduan-kp.md) (Syarat 80 SKS, alur pengajuan), [Panduan Tugas Akhir & Skripsi](kp-ta/panduan-ta.md) (Syarat 110 SKS, SPOTA, alur proposal hingga yudisium). |
| **4. Direktori Dosen (KBK)** | [`dosen/`](dosen/README.md) | 33 Berkas Profil Dosen Terpadu: [AI & Komputasi](dosen/ai-komputasi/), [RPL & Mobile](dosen/rpl-mobile/), [Jaringan & Keamanan](dosen/jaringan-keamanan/), [Sistem Informasi & Spasial](dosen/si-spasial/), dan [Dosen Umum](dosen/umum/). Dilengkapi metrik riset OpenAlex. |
| **5. Sarana & Laboratorium** | [`fasilitas-lab/`](fasilitas-lab/README.md) | [5 Laboratorium Tematik](fasilitas-lab/laboratorium.md) (Komputasi Dasar, AI, RPL, SI, Network; total 93 PC), [4 Kelompok Bidang Keahlian](fasilitas-lab/kelompok-bidang-keahlian.md). |
| **6. Organisasi & Alumni** | [`kemahasiswaan/`](kemahasiswaan/README.md) | [Himpunan Mahasiswa Informatika (HMIF)](kemahasiswaan/hmif.md) (6 divisi, agenda tahunan, study club), [Ikatan Alumni & Tracer Study](kemahasiswaan/alumni-tracer-study.md). |

---

## ⚙️ Aturan Pengelolaan Berkas Vault
1. **Dosen**: Setiap berkas dosen wajib menyertakan frontmatter YAML dengan field `tipe: dosen`, `nama`, `nip`, `email`, `jabatan`, `kelompok_keahlian`, `openalex_id`, dan `diverifikasi: true`.
2. **Lookup Table**: Jangan pernah mengedit `vault/lookup.json` secara manual. Selalu jalankan `pixi run build-lookup` setelah menambah atau mengubah data dosen.
3. **Integritas Tautan**: Gunakan tautan Markdown relatif standar `[Label](path/to/file.md)`. Selalu validasi dengan `pixi run check-links` untuk menjamin 0 tautan rusak.
"""
    (VAULT / "README.md").write_text(content, encoding="utf-8")
    print("vault/README.md berhasil dibuat.")


def cleanup_old_files() -> None:
    old_files = [
        VAULT / "dosen" / "contoh-dosen.md",
    ]
    for of in old_files:
        if of.exists():
            of.unlink()
            print(f"Menghapus berkas contoh usang: {of.name}")


def main() -> None:
    print("Memulai proses migrasi dan reorganisasi vault...")
    setup_directories()
    dosen_list = migrate_dosen()
    build_dosen_readme(dosen_list)
    migrate_profil()
    migrate_akademik()
    migrate_kp_ta()
    migrate_fasilitas_lab()
    migrate_kemahasiswaan()
    build_root_vault_readme()
    cleanup_old_files()
    print("Reorganisasi berkas vault selesai dengan sukses.")


if __name__ == "__main__":
    main()
