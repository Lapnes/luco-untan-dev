# Basis Pengetahuan (Knowledge Vault) Prodi Informatika UNTAN

Repositori ini merupakan **sumber kebenaran tunggal (*single source of truth*)** bagi asisten cerdas **Luco 🐦** dan seluruh sivitas akademika Program Studi S1 Informatika, Fakultas Teknik, Universitas Tanjungpura.

Seluruh data disusun secara hierarkis menggunakan standar Markdown CommonMark dengan tautan silang (*cross-links*) relatif untuk mendukung penjelajahan hierarkis OpenViking (L0 Root -> L1 Folder -> L2 Teks Lengkap) serta pencarian data deterministik dosen melalui `vault/lookup.json`.

---

## 🗂️ Taksonomi 7 Kategori Pengetahuan

| Kategori | Direktori | Ringkasan Konten Utama |
| :--- | :--- | :--- |
| **1. Profil & Tata Kelola** | [`profil/`](profil/README.md) | [Visi Misi](profil/visi-misi.md), [Struktur Organisasi](profil/struktur-organisasi.md), [Akreditasi & Prestasi](profil/akreditasi.md), [Sejarah Kampus](profil/sejarah-untan.md), [Tim Pengembang Luco](profil/tim-pengembang.md). |
| **2. Akademik & Kurikulum** | [`akademik/`](akademik/README.md) | [Profil Lulusan & CPL](akademik/profil-lulusan-cpl.md), [Kurikulum 2026 (140 SKS)](akademik/kurikulum/2026/README.md), [Arsip Kurikulum 2016](akademik/kurikulum/2016/README.md), [Panduan KRS & SKS](akademik/panduan/peraturan-akademik-krs.md), [Beasiswa & PMB](akademik/panduan/beasiswa-dan-pmb.md). |
| **3. Tahap Akhir Studi** | [`kp-ta/`](kp-ta/README.md) | [Panduan Kerja Praktik](kp-ta/panduan-kp.md) (Syarat 110 SKS, alur KP), [Panduan Tugas Akhir & Skripsi](kp-ta/panduan-ta.md) (Syarat 110 SKS, SPOTA, format naskah 2022, alur wisuda), [Template Dokumen](kp-ta/template-dokumen.md) (26 unduhan berkas resmi). |
| **4. Direktori Dosen (KBK)** | [`dosen/`](dosen/README.md) | 33 Berkas Profil Dosen Terpadu: [AI & Komputasi](dosen/ai-komputasi/), [RPL & Mobile](dosen/rpl-mobile/), [Jaringan & Keamanan](dosen/jaringan-keamanan/), [Sistem Informasi & Spasial](dosen/si-spasial/), dan [Dosen Umum](dosen/umum/). Dilengkapi metrik riset OpenAlex. |
| **5. Sarana & Laboratorium** | [`fasilitas-lab/`](fasilitas-lab/README.md) | [5 Laboratorium Tematik](fasilitas-lab/laboratorium.md) (Komputasi Dasar, AI, RPL, SI, Network; total 93 PC), [4 Kelompok Bidang Keahlian](fasilitas-lab/kelompok-bidang-keahlian.md). |
| **6. Organisasi & Kemahasiswaan** | [`kemahasiswaan/`](kemahasiswaan/README.md) | [Himpunan Mahasiswa Informatika (HMIF)](kemahasiswaan/hmif.md), [Ikatan Alumni & Tracer Study](kemahasiswaan/alumni-tracer-study.md), [Profil Ragil Amirzaky](kemahasiswaan/ragil-amirzaky.md). |
| **7. Berkas & Dokumen Resmi** | [`dokumen/`](dokumen/README.md) | 26 Berkas Dokumen Resmi (SOP KP, form KP-IF, template skripsi, pedoman akademik, sertifikat akreditasi) hasil ekstraksi PyMuPDF4LLM & Mammoth, lengkap dengan opsi naskah `.md` atau unduh berkas asli. |

---

## ⚙️ Aturan Pengelolaan Berkas Vault
1. **Dosen**: Setiap berkas dosen wajib menyertakan frontmatter YAML dengan field `tipe: dosen`, `nama`, `nip`, `email`, `jabatan`, `kelompok_keahlian`, `openalex_id`, dan `diverifikasi: true`.
2. **Lookup Table**: Jangan pernah mengedit `vault/lookup.json` secara manual. Selalu jalankan `pixi run build-lookup` setelah menambah atau mengubah data dosen.
3. **Integritas Tautan**: Gunakan tautan Markdown relatif standar `[Label](path/to/file.md)`. Selalu validasi dengan `pixi run check-links` untuk menjamin 0 tautan rusak.
