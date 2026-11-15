import pytest
from luco.clarifications import detect_clarification


def test_detect_clarification_bimbingan_ambigu():
    res = detect_clarification("mau bimbingan dong")
    assert res is not None
    assert res["id"] == "bimbingan"
    assert "bimbingan" in res["title"].lower()
    assert len(res["options"]) == 4
    assert any("tugas akhir" in opt.lower() for opt in res["options"])
    assert any("kerja praktik" in opt.lower() for opt in res["options"])


def test_detect_clarification_syarat_ujian_ambigu():
    res = detect_clarification("syarat ujian apa aja?")
    assert res is not None
    assert res["id"] == "syarat_ujian"
    assert len(res["options"]) >= 3


def test_detect_clarification_not_triggered_for_specific_ta():
    # Pertanyaan spesifik tentang TA tidak boleh memicu klarifikasi ambigu
    res = detect_clarification("Apa syarat mengajukan proposal TA/skripsi?")
    assert res is None


def test_detect_clarification_not_triggered_for_specific_kp():
    # Pertanyaan spesifik tentang KP tidak boleh memicu klarifikasi ambigu
    res = detect_clarification("Gimana alur pendaftaran Kerja Praktik di Informatika UNTAN?")
    assert res is None


def test_detect_clarification_dynamic_extraction():
    answer_text = (
        "Biar lebih jelas, kamu mau info yang mana?\n"
        "1. Alur Skripsi\n"
        "2. Alur Kerja Praktik\n"
        "3. Dosen PA\n"
    )
    res = detect_clarification("pertanyaan ambigu umum", answer=answer_text)
    assert res is not None
    assert res["id"] == "dynamic_clarification"
    assert len(res["options"]) == 3
    assert res["options"][0] == "Alur Skripsi"
