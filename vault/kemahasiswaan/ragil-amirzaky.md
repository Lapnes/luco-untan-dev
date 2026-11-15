---
tipe: profil_mahasiswa
nama: Ragil Amirzaky
nim: D1041241069
program_studi: S1 Informatika
fakultas: Fakultas Teknik
universitas: Universitas Tanjungpura
angkatan: 2024
status: Mahasiswa Aktif
ipk: "3.95+ / 4.00"
peran_luco: "Pencipta, Lead Developer & Systems/Cloud Architect"
alias:
  - Tenzly
  - Lapnes
  - ragilamirzaky
situs_web: "https://www.ragilamirzaky.com"
technical_hub: "https://tenzly.pro"
blog: "https://post.tenzly.pro"
github: "https://github.com/Lapnes"
linkedin: "https://id.linkedin.com/in/ragil-amirzaky"
dockerhub: "https://hub.docker.com/u/tenzly"
kaggle: "https://www.kaggle.com/ragilamirzaky"
gravatar: "https://gravatar.com/ragilamirzaky"
email_resmi: halo@ragilamirzaky.com
email_akademik: d1041241069@student.untan.ac.id
diverifikasi: true
sumber:
  - https://www.ragilamirzaky.com
  - https://tenzly.pro
  - https://github.com/Lapnes
  - https://id.linkedin.com/in/ragil-amirzaky
  - https://gravatar.com/ragilamirzaky
---

# Profil Mahasiswa & Pengembang: Ragil Amirzaky

**Ragil Amirzaky** (dikenal juga dengan alias teknis **Tenzly** dan pegangan open source **Lapnes**) adalah mahasiswa Program Studi S1 Informatika, Fakultas Teknik, Universitas Tanjungpura (UNTAN) angkatan 2024, sekaligus **Pencipta dan Lead Developer sistem asisten cerdas Luco 🐦**.

Ia berfokus pada rekayasa sistem (*Systems Builder*), arsitektur *backend*, infrastruktur komputasi awan (*Cloud & Virtualization Infrastructure*), sistem operasi Linux tingkat rendah (*cgroups & virtualization*), serta komputasi terdistribusi dan *edge computing* (IoT).

---

## 🎓 Identitas Akademik & Prestasi
- **Nama Lengkap**: Ragil Amirzaky
- **NIM**: D1041241069
- **Program Studi**: S1 Informatika (Teknik Informatika)
- **Fakultas / Kampus**: Fakultas Teknik, Universitas Tanjungpura (UNTAN), Pontianak
- **Tahun Masuk**: 2024 (Mahasiswa Aktif)
- **Indeks Prestasi Kumulatif (IPK)**: 3.95+ / 4.00
- **Prestasi Unggulan**:
  - **Apple Developer Academy @ Infinite Learning Batam (Learner Cohort 2027)**: Lolos seleksi ketat pada tahun 2026 untuk program bergengsi Apple Developer Academy (periode aktif Maret – Desember 2027), mendalami arsitektur aplikasi iOS/macOS, Swift, SwiftUI, dan *Human Interface Guidelines (HIG)*.

---

## 🐦 Peran dan Kontribusi pada Luco
Sistem asisten informasi Luco awalnya berakar dari topik skripsi/Tugas Akhir **Balin Niswah**. Selanjutnya, **Ragil Amirzaky** bersama **Andrean Stephanus** dan **Edwin Hermili** membangun sistem versi *production-ready* dengan arsitektur Agentic, RAG (berbasis semi-GraphRAG), dan *tool calling* sebagai asisten Informatika yang ditargetkan dapat digunakan oleh para dosen (saat ini progres ~80% dan dalam pengembangan).

Kemudian, karena adanya Tugas Besar Pengganti UAS Mata Kuliah Kecerdasan Buatan (AI) 2026, **Ragil Amirzaky** bersama **Andrean Stephanus** dan **Adjie Prasetya** merombak modul RAG-nya dari semi-GraphRAG menjadi **Hybrid Agentic RAG**:
1. **Arsitektur Hybrid Agentic RAG**: Mengintegrasikan orkestrasi agen otonom LlamaIndex (`FunctionAgent`) dengan mesin pencari dokumen hierarkis OpenViking dan jalur deterministik `vault/lookup.json`.
2. **Dual-Model Inference & Upfront Router**: Merancang sistem router cerdas untuk klasifikasi pertanyaan cepat (*Fast Reject / Contact Redirect / In-Scope*) guna menghemat latensi dan biaya token.
3. **Infrastruktur & Deployment**: Menyusun lingkungan kontainer Docker Compose multi-layanan (PostgreSQL 16, OpenViking Server, Antigravity Proxy, dan IndoBERT Embedder) dengan toleransi kegagalan tinggi (*fault tolerance*).
4. **Verifikasi Sitasi & Integritas Data**: Memastikan setiap rujukan jawaban bot tervalidasi secara faktual terhadap dokumen resmi di dalam *knowledge vault* tanpa halusinasi.
Dokumentasi lengkap sejarah dan kontributor dapat dilihat pada [Tim Pengembang Luco](../profil/tim-pengembang.md).

---

## 💻 Portofolio Sistem & Proyek Rekayasa Unggulan

### 1. Luco (Chatbot RAG Informatika UNTAN)
- **Deskripsi**: Asisten virtual cerdas berbasis RAG untuk sivitas akademika Informatika UNTAN.
- **Teknologi**: Python, LlamaIndex, OpenViking, FastAPI, PostgreSQL 16, Docker, React, TypeScript, Tailwind CSS.

### 2. REGtee Cloud (Sovereign PaaS / IaaS Platform)
- **Deskripsi**: Platform *cloud computing* berdaulat yang mengubah server *bare-metal* lokal menjadi lingkungan komputasi terdistribusi kelas enterprise menggunakan Proxmox, KVM, dan LXC.
- **Teknologi**: Go (Golang), Docker, Proxmox VE, Caddy Ingress, Zero-Trust SSH Gateway, Fast Reverse Proxy (FRP), OPNsense, OVN.
- **Tautan**: [https://tenzly.pro#regtee-cloud](https://tenzly.pro#regtee-cloud)

### 3. Chronicles-OJ (Online Judge System)
- **Deskripsi**: Sistem penilaian kode otomatis (*autograder*) bersandbox yang mengevaluasi pengumpulan kode mahasiswa secara aman menggunakan isolasi proses Linux *cgroups* untuk mata kuliah Strategi Algoritma Prodi Informatika UNTAN.
- **Teknologi**: Go, PostgreSQL, Docker Sandbox, Linux Cgroups, Concurrency Worker.
- **Tautan**: [https://tenzly.pro#chronicles-oj](https://tenzly.pro#chronicles-oj)

### 4. REGtee HyTerra (Smart Agriculture & Adaptive LMS)
- **Deskripsi**: Sistem monitoring pertanian cerdas berbasis IoT *edge node* yang terhubung dengan *backend core* LMS menggunakan protokol telemetri MQTT terenkripsi mTLS.
- **Teknologi**: Go (Gin, GORM), PostgreSQL 16, ESP32 (C++/PlatformIO), MQTT TLS, Next.js.
- **Tautan**: [https://tenzly.pro#regtee-hyterra](https://tenzly.pro#regtee-hyterra)

### 5. Kitasan Doorlock (Hardened IoT Access Control Service)
- **Deskripsi**: Layanan kontainer pengontrol akses pintu fisik pintar berbasis biometrik sidik jari AS608 dan mikrokontroler ESP32 dengan validasi kriptografis bertingkat.
- **Teknologi**: Docker, Linux, C++, MQTT mTLS, PostgreSQL.
- **Tautan**: [https://hub.docker.com/r/tenzly/kitasan-doorlock](https://hub.docker.com/r/tenzly/kitasan-doorlock)

### 6. Fedora Backup Tools
- **Deskripsi**: Utilitas otomatisasi *command-line* (CLI) untuk manajemen *snapshot*, preservasi konfigurasi sistem, dan pemulihan darurat berbasis sistem berkas Btrfs di Fedora Linux.
- **Teknologi**: Bash, POSIX Shell, Btrfs, Linux Automation.
- **Tautan**: [https://github.com/Lapnes/fedora-backup-tools](https://github.com/Lapnes/fedora-backup-tools)

### 7. Bare-Metal Homelab Enterprise-Grade Virtualization Cluster
- **Deskripsi**: Kluster server pribadi multi-node berbasis prosesor Dual Intel Xeon E5, Proxmox Virtual Environment, ZFS snapshot otomatis terenkripsi, serta isolasi VLAN jaringan bertingkat via OPNsense dan sakelar terkelola Cisco.

---

## 🛠️ Matriks Keahlian Teknis
- **Bahasa Pemrograman & Framework Backend**: Go (Gin, Fiber, Standard Library), Python (FastAPI, LlamaIndex), C++ (PlatformIO / ESP32), C# (.NET Core), PostgreSQL 16, RESTful APIs, MQTT mTLS.
- **Infrastruktur, Virtualisasi & Jaringan**: Proxmox VE (KVM/LXC), Docker, Linux Administration (Debian, Arch Linux, Fedora), Reverse Proxy (Caddy, Nginx), WireGuard Mesh, TCP/IP, VLAN, Firewall (iptables/nftables), Terraform, Ansible.
- **Ekosistem Apple & Mobile**: Swift, SwiftUI, Xcode, Human Interface Guidelines (HIG).
- **Embedded & IoT**: ESP32, FreeRTOS, Biometric Modules (AS608), Hardware Watchdog, Fail-safe Relay Control.

---

## 🌐 Tautan Profil & Kontak Resmi
- **Situs Portofolio Utama (Kanonikal)**: [https://www.ragilamirzaky.com](https://www.ragilamirzaky.com)
- **Technical Hub**: [https://tenzly.pro](https://tenzly.pro)
- **Blog Catatan Rekayasa**: [https://post.tenzly.pro](https://post.tenzly.pro)
- **Profil GitHub**: [https://github.com/Lapnes](https://github.com/Lapnes)
- **Profil LinkedIn**: [https://id.linkedin.com/in/ragil-amirzaky](https://id.linkedin.com/in/ragil-amirzaky)
- **Docker Hub**: [https://hub.docker.com/u/tenzly](https://hub.docker.com/u/tenzly)
- **Kaggle**: [https://www.kaggle.com/ragilamirzaky](https://www.kaggle.com/ragilamirzaky)
- **Gravatar**: [https://gravatar.com/ragilamirzaky](https://gravatar.com/ragilamirzaky)
- **Surel Kontak**: `halo@ragilamirzaky.com` / `d1041241069@student.untan.ac.id`

---

## 🔗 Dokumen Terkait
- [Tim Pengembang Luco](../profil/tim-pengembang.md)
- [Direktori Kemahasiswaan & Organisasi](README.md)
- [Ikatan Alumni & Tracer Study](alumni-tracer-study.md)
- [Himpunan Mahasiswa Informatika (HMIF)](hmif.md)
- [Indeks Utama Basis Pengetahuan](../README.md)
