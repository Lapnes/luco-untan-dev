"""Modul Deteksi & Template Klarifikasi Aktif (Interview / Grill-Me Mode) untuk Pertanyaan Ambigu di Luco."""
from __future__ import annotations

import re
from typing import Any


CLARIFICATION_PRESETS: list[dict[str, Any]] = [
    {
        "id": "bimbingan",
        "keywords": ["bimbingan", "dibimbing", "mahasiswa bimbingan", "minta bimbing"],
        "negative_keywords": ["tugas akhir", "skripsi", "kerja praktik", " kp ", "pa", "dosen pa", "krs"],
        "title": "Kamu mau bimbingan soal apa?",
        "options": [
            "Bimbingan Tugas Akhir / Skripsi (SPOTA)",
            "Bimbingan Kerja Praktik (KP)",
            "Bimbingan Akademik (Dosen PA & KRS)",
            "Bimbingan Lomba / Riset KBK Lab",
        ],
        "reply": (
            "Halo! Di Informatika UNTAN, bimbingan memiliki beberapa jalur resmi yang berbeda. "
            "Biar Luco bisa berikan alur dan syarat yang tepat sasaran, kamu mau bimbingan yang mana? "
            "Silakan pilih opsi di bawah ya 🐦"
        ),
    },
    {
        "id": "syarat_ujian",
        "keywords": ["syarat ujian", "ujian apa", "mau ujian", "jadwal ujian", "alur ujian"],
        "negative_keywords": ["skripsi", "ta", "semhas", " kp ", "uts", "uas"],
        "title": "Ujian apa yang ingin kamu ketahui syaratnya?",
        "options": [
            "Ujian Sidang Skripsi / Tugas Akhir",
            "Seminar Hasil (Semhas) Skripsi",
            "Seminar / Ujian Kerja Praktik (KP)",
            "Ujian Tengah / Akhir Semester (UTS / UAS)",
        ],
        "reply": (
            "Setiap tahapan ujian di Informatika UNTAN memiliki berkas dan prasyarat SKS yang berbeda. "
            "Ujian apa yang sedang kamu persiapkan? Pilih opsi di bawah ya 🐦"
        ),
    },
    {
        "id": "pendaftaran",
        "keywords": ["cara daftar", "alur pendaftaran", "mau daftar", "link pendaftaran"],
        "negative_keywords": [" kp ", "kerja praktik", "skripsi", "ta", "spota", "yudisium", "wisuda", "pmb", "beasiswa"],
        "title": "Pendaftaran apa yang kamu tuju?",
        "options": [
            "Pendaftaran Kerja Praktik (KP)",
            "Pendaftaran Proposal / Sidang Tugas Akhir",
            "Pendaftaran Yudisium & Wisuda",
            "Pendaftaran Mahasiswa Baru (PMB) & Beasiswa",
        ],
        "reply": (
            "Ada beberapa jenis pendaftaran akademik di Informatika UNTAN. "
            "Pendaftaran mana yang ingin kamu tanyakan alurnya? Silakan pilih opsi di bawah ya 🐦"
        ),
    },
    {
        "id": "kurikulum",
        "keywords": ["kurikulum", "sebaran matkul", "mata kuliah wajib"],
        "negative_keywords": ["2026", "2016", "perbedaan", "bedanya", "obe"],
        "title": "Kurikulum mana yang ingin kamu pelajari?",
        "options": [
            "Kurikulum 2026 (OBE - Total 140 SKS)",
            "Arsip Historis Kurikulum 2016 (Total 144 SKS)",
            "Perbedaan Kurikulum 2026 vs 2016",
            "Pemetaan CPL & 4 Tahap Pembelajaran",
        ],
        "reply": (
            "Saat ini Informatika UNTAN menerapkan Kurikulum 2026 berbasis OBE, dengan arsip Kurikulum 2016 untuk mahasiswa lama. "
            "Kurikulum mana yang ingin kamu lihat detailnya? Silakan pilih di bawah ya 🐦"
        ),
    },
    {
        "id": "dosen_pembimbing",
        "keywords": ["pembimbing", "cari pembimbing", "pilih pembimbing"],
        "negative_keywords": ["tugas akhir", "skripsi", " kp ", "pa", "krs"],
        "title": "Informasi pembimbing apa yang kamu butuhkan?",
        "options": [
            "Dosen Pembimbing Tugas Akhir (Alur SPOTA & KBK)",
            "Dosen Pembimbing Kerja Praktik (Koordinator KP)",
            "Dosen Pembimbing Akademik (Dosen PA untuk KRS)",
            "Daftar Profil & Bidang Riset Dosen Informatika",
        ],
        "reply": (
            "Penentuan dosen pembimbing di Informatika UNTAN tergantung pada keperluanmu (TA, KP, atau PA). "
            "Informasi pembimbing mana yang ingin kamu ketahui? Silakan pilih opsi di bawah 🐦"
        ),
    },
]


def detect_clarification(question: str, answer: str = "") -> dict[str, Any] | None:
    """Mendeteksi apakah pertanyaan pengguna memerlukan klarifikasi aktif (grill-me card)."""
    q_lower = f" {question.lower().strip()} "

    # 1. Cek Preset Ambigu Berdasarkan Kata Kunci
    for preset in CLARIFICATION_PRESETS:
        has_kw = any(kw in q_lower for kw in preset["keywords"])
        has_neg = any(neg in q_lower for neg in preset["negative_keywords"])
        if has_kw and not has_neg:
            return {
                "id": preset["id"],
                "title": preset["title"],
                "options": preset["options"],
                "reply_override": preset.get("reply"),
                "allow_custom": True,
            }

    # 2. Cek apakah jawaban LLM berisi pertanyaan klarifikasi dengan opsi bernomor (1. ..., 2. ...)
    if ("?" in answer or "klarifikasi" in answer.lower() or "bisa bantu apa" in answer.lower()) and ("1." in answer and "2." in answer):
        options = []
        for line in answer.splitlines():
            line_s = line.strip()
            m = re.match(r"^\d+[\.\)]\s*(.+)$", line_s)
            if m:
                opt_text = m.group(1).strip()
                # Bersihkan bold markdown bila ada
                opt_text = re.sub(r"^\*\*|\*\*$", "", opt_text).strip()
                if len(opt_text) > 3 and len(opt_text) < 80:
                    options.append(opt_text)
        if len(options) >= 2:
            # Ambil judul pertanyaan klarifikasi
            title = "Pilih opsi di bawah untuk memperjelas pertanyaanmu:"
            for line in answer.splitlines():
                if "?" in line and len(line.strip()) < 80:
                    title = line.strip().lstrip("-* ").replace("**", "")
                    break
            return {
                "id": "dynamic_clarification",
                "title": title,
                "options": options[:5],
                "allow_custom": True,
            }

    return None
