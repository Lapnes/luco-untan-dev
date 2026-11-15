import pytest
from luco.router import (
    CONTACT_REDIRECT_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
    classify_heuristics,
    classify_query,
)


def test_router_heuristics():
    # Saran / kritik / kerjasama
    r1 = classify_heuristics("Saya ingin memberikan saran untuk perbaikan lab")
    assert r1 is not None and r1.category == "CONTACT_REDIRECT"
    assert r1.reply_message == CONTACT_REDIRECT_MESSAGE

    r2 = classify_heuristics("Bagaimana prosedur kerja sama magang industri?")
    assert r2 is not None and r2.category == "CONTACT_REDIRECT"

    # Pertanyaan normal prodi langsung IN_SCOPE tanpa penolakan (reply_message is None)
    r3 = classify_heuristics("Apa syarat seminar proposal skripsi?")
    assert r3 is not None and r3.category == "IN_SCOPE" and r3.reply_message is None

    # Nama dosen prodi langsung IN_SCOPE
    r4 = classify_heuristics("siapa izuardo ?")
    assert r4 is not None and r4.category == "IN_SCOPE" and r4.reply_message is None

    # Keluhan bot bukan kontak/saran prodi formal (tidak salah redirect)
    r5 = classify_heuristics("kenapa kamu ga pernah jawab yang benar ?")
    assert r5 is not None and r5.category == "IN_SCOPE" and r5.reply_message is None

    # Pertanyaan non-prodi tanpa kata kunci jatuh ke LLM router (return None)
    r6 = classify_heuristics("Berapa jarak dari bumi ke bulan?")
    assert r6 is None

    # Pengembang dan pembuat Luco langsung IN_SCOPE
    r7 = classify_heuristics("siapa Ragil Amirzaky?")
    assert r7 is not None and r7.category == "IN_SCOPE" and r7.reply_message is None

    r8 = classify_heuristics("siapa yang bikin kamu?")
    assert r8 is not None and r8.category == "IN_SCOPE" and r8.reply_message is None

    r9 = classify_heuristics("siapa pengembang luco?")
    assert r9 is not None and r9.category == "IN_SCOPE" and r9.reply_message is None

    # Sejarah dan kontributor Luco langsung IN_SCOPE
    r10 = classify_heuristics("siapa Balin Niswah?")
    assert r10 is not None and r10.category == "IN_SCOPE" and r10.reply_message is None

    r11 = classify_heuristics("siapa Edwin Hermili?")
    assert r11 is not None and r11.category == "IN_SCOPE" and r11.reply_message is None

    r12 = classify_heuristics("siapa Adjie Prasetya?")
    assert r12 is not None and r12.category == "IN_SCOPE" and r12.reply_message is None

    # Pengujian anti-false-positive: Permintaan saran topik/PA tidak boleh dialihkan ke kontak
    r13 = classify_heuristics("buatkan alur lengkap dan pedoman TA untuk ku... aku mau tema SSH Gateway saran juga dong Dosen PA nya siapa...")
    assert r13 is not None and r13.category == "IN_SCOPE" and r13.reply_message is None

    # Topik algoritma kerja sama tidak boleh salah redirect ke kontak kemitraan
    r14 = classify_heuristics("bisa ga ta dengan topik banchmark algoritma kerja sama ?")
    assert r14 is not None and r14.category == "IN_SCOPE" and r14.reply_message is None

    # Pertanyaan profil dosen dengan maksud kerjasama tidak boleh diblokir
    r15 = classify_heuristics("siapa pak izuardo ? aku mau ajukan kerja sama")
    assert r15 is not None and r15.category == "IN_SCOPE" and r15.reply_message is None


@pytest.mark.asyncio
async def test_router_fallback_without_llm():
    res = await classify_query("Apa syarat seminar proposal skripsi?", llm=None)
    assert res.category == "IN_SCOPE"

    # Pertanyaan lanjutan dengan riwayat singkat
    history = [
        {"role": "user", "content": "Siapa ketua jurusan informatika?"},
        {"role": "assistant", "content": "Ketua jurusan adalah Dr. X"},
    ]
    res2 = await classify_query("Berapa email beliau?", history=history, llm=None)
    assert res2.category == "IN_SCOPE"


class MockRouterLLM:
    def __init__(self, category: str, reason: str):
        self.category = category
        self.reason = reason

    async def acomplete(self, prompt: str) -> str:
        return f'{{"category": "{self.category}", "reason": "{self.reason}"}}'


@pytest.mark.asyncio
async def test_router_llm_classification_out_of_scope():
    # Menguji penolakan pertanyaan di luar cakupan via Router LLM
    mock_llm = MockRouterLLM(category="OUT_OF_SCOPE", reason="Pertanyaan di luar ranah kampus")
    res = await classify_query("Berapa harga sepeda motor beat baru?", llm=mock_llm)
    assert res.category == "OUT_OF_SCOPE"
    assert res.reply_message == OUT_OF_SCOPE_MESSAGE
    assert "di luar cakupan" in res.reply_message.lower()


@pytest.mark.asyncio
async def test_router_llm_classification_contact_redirect():
    # Menguji pengalihan saran formal ke kontak prodi via Router LLM untuk pertanyaan di luar heuristik instan
    mock_llm = MockRouterLLM(category="CONTACT_REDIRECT", reason="Permohonan kemitraan formal")
    res = await classify_query("Penawaran kemitraan vendor pengadaan komputer kantor", llm=mock_llm)
    assert res.category == "CONTACT_REDIRECT"
    assert res.reply_message == CONTACT_REDIRECT_MESSAGE
    assert "sekretariat atau surel resmi prodi" in res.reply_message.lower()

