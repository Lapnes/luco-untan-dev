"""
Orkestrator Utama Pembuatan Dokumen Laporan Lengkap (.docx)
Sistematika Resmi 9 Poin (F. Sistematika Laporan) — Luco UNTAN 2026
"""

import os
import sys
import shutil

# Tambahkan direktori root proyek ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import docx

from scripts.build_full_report import (
    setup_document_styles,
    add_cover_page,
)
from scripts.report_sections_v2_part1 import (
    add_front_matter_v2,
    add_section_1,
    add_section_2,
    add_section_3,
    add_section_4,
)
from scripts.report_sections_v2_part2 import (
    add_section_5,
    add_section_6,
    add_section_7,
)
from scripts.report_sections_v2_part3 import (
    add_section_8,
    add_section_9,
    add_references_v2,
    add_appendices_v2,
)

def main():
    print("=== MEMULAI GENERASI DOKUMEN LAPORAN SISTEMATIKA 9 POIN (.DOCX) ===")
    
    doc = docx.Document()
    
    # Setup Margins, Tipografi Times New Roman & Header-Footer
    print("[1/10] Mengatur margin A4 (4-3-3-3 cm), tipografi, dan header-footer...")
    setup_document_styles(doc)
    
    # Halaman Sampul (Cover Page)
    print("[2/10] Menyusun Halaman Sampul Resmi dengan Logo Luco...")
    add_cover_page(doc)
    
    # Front Matter: Lembar Konsultasi, Ringkasan Eksekutif (ID & EN), Kata Pengantar, Daftar Isi
    print("[3/10] Menyusun Lembar Konsultasi, Ringkasan Eksekutif, Kata Pengantar, & Daftar Isi...")
    add_front_matter_v2(doc)
    
    # 1. Judul proyek dan identitas anggota kelompok
    # 2. Pendahuluan: latar belakang, rumusan masalah, tujuan, dan manfaat
    print("[4/10] Menyusun Bagian 1 (Identitas & Judul) dan Bagian 2 (Pendahuluan)...")
    add_section_1(doc)
    add_section_2(doc)
    
    # 3. Landasan teori singkat: konsep dan metode AI yang digunakan
    # 4. Data: sumber data, deskripsi, dan tahapan preprocessing
    print("[5/10] Menyusun Bagian 3 (Landasan Teori AI) dan Bagian 4 (Data & Preprocessing)...")
    add_section_3(doc)
    add_section_4(doc)
    
    # 5. Perancangan sistem: diagram alir/arsitektur, input, proses AI, dan output
    # 6. Implementasi: perangkat lunak, tahapan pengembangan, dan cara menjalankan prototipe
    print("[6/10] Menyusun Bagian 5 (Perancangan Sistem & ERD) dan Bagian 6 (Implementasi)...")
    add_section_5(doc)
    add_section_6(doc)
    
    # 7. Pengujian dan evaluasi: skenario uji, metrik yang sesuai, hasil, dan pembahasan
    print("[7/10] Menyusun Bagian 7 (Pengujian 78 Pytest, IndoBERT, 3 Mode, Multi-turn)...")
    add_section_7(doc)
    
    # 8. Etika dan keterbatasan: potensi bias, privasi, risiko kesalahan, serta penggunaan Generative AI
    # 9. Kesimpulan dan saran pengembangan
    print("[8/10] Menyusun Bagian 8 (Etika, Privasi, Anti-Joki) dan Bagian 9 (Kesimpulan & Saran)...")
    add_section_8(doc)
    add_section_9(doc)
    
    # Daftar Pustaka & Lampiran (Lampiran 1, 2, 3)
    print("[9/10] Menyusun Daftar Pustaka dan Lampiran 1 s.d. 3...")
    add_references_v2(doc)
    add_appendices_v2(doc)
    
    # Simpan Berkas .docx ke direktori final dan root
    print("[10/10] Menyimpan berkas docx...")
    out_dir = "docs/laporan/final"
    os.makedirs(out_dir, exist_ok=True)
    
    # Nama berkas sesuai permintaan user
    filename_target = "Laporan_Tugas_Besar_AI_Luco_UNTAN_2026.docx"
    filename_alt = "Laporan_Tugas_Besar_Kecerdasan_Buatan_2026_Luco.docx"
    
    path_final_1 = os.path.join(out_dir, filename_target)
    path_final_2 = os.path.join(out_dir, filename_alt)
    
    doc.save(path_final_1)
    shutil.copyfile(path_final_1, path_final_2)
    shutil.copyfile(path_final_1, filename_target)
    shutil.copyfile(path_final_1, filename_alt)
    
    file_size_kb = os.path.getsize(path_final_1) / 1024
    print(f"=== SELESAI! Dokumen berhasil disimpan di:")
    print(f"  1. {filename_target} (Root Workspace)")
    print(f"  2. {path_final_1}")
    print(f"  3. {filename_alt} (Root Workspace)")
    print(f"  4. {path_final_2}")
    print(f"Ukuran berkas: {file_size_kb:.1f} KB")

if __name__ == "__main__":
    main()
