from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Literal

from llama_index.core.llms import LLM

RouteCategory = Literal["IN_SCOPE", "OUT_OF_SCOPE", "CONTACT_REDIRECT"]

OUT_OF_SCOPE_MESSAGE = (
    "Maaf, pertanyaan ini di luar cakupan informasi Program Studi Informatika UNTAN. "
    "Luco berfokus pada informasi resmi prodi seperti alur KP, skripsi/TA, kurikulum, "
    "dan profil dosen Informatika UNTAN."
)

CONTACT_REDIRECT_MESSAGE = (
    "Untuk penyampaian kritik, saran, pengaduan, atau penawaran kerja sama resmi, silakan hubungi "
    "langsung kontak resmi Program Studi Informatika UNTAN melalui sekretariat atau surel resmi prodi:\n"
    "- Telepon/WhatsApp: +62 851-7165-5161\n"
    "- Email: info@informatika.untan.ac.id\n"
    "- Instagram: @informatika.untan"
)


@dataclass(frozen=True)
class RouteResult:
    category: RouteCategory
    reason: str
    reply_message: str | None = None


PRODI_KEYWORDS = {
    "ta", "kp", "skripsi", "proposal", "semhas", "sidang", "krs", "sks", "ipk", "dosen",
    "matkul", "mata kuliah", "kurikulum", "kbk", "keahlian", "laboratorium", "lab", "hmif",
    "beasiswa", "ukt", "pmb", "spota", "yudisium", "wisuda", "magang", "alumni", "pa",
    "pembimbing", "bimbingan", "prodi", "jurusan", "informatika", "untan",
    "izuardo", "zulkarnain", "herry", "sujaini", "anggi", "perwitasari", "srimurdianti",
    "desepta", "dimas", "arif", "bijaksana", "yus", "sholva", "enda", "esyudha", "enriko",
    "eva", "ripanti", "fauzan", "asrin", "hengky", "anra", "haried", "novriando",
    "helfi", "nasution", "heri", "priyanto", "ibnu", "azhar", "irwansyah", "khairul",
    "hafidh", "farid", "tsanauddin", "morteza", "muthahhari", "niken", "candraningrum",
    "novi", "safriadi", "rickhy", "artha", "rifqi", "anugrah", "rina", "septiriana",
    "rizki", "firdaus", "rudy", "nyoto", "tursina", "yulianti", "helen", "sastypratiwi",
    "ragil", "amirzaky", "lapnes", "tenzly", "andrean", "stephanus", "aji", "adjie", "prasetya",
    "balin", "niswah", "edwin", "hermili", "etherift",
    "pengembang", "pembuat", "developer", "creator", "sejarah",
    "pedoman", "alur", "syarat", "panduan", "format", "formulir", "ssh", "gateway",
    "benchmark", "benchmart", "evaluasi", "pengujian", "hybrid", "inject", "rag", "hemat", "token", "biaya",
    "kontak", "whatsapp", "wa", "telepon", "instagram", "email", "surel"
}

ADVICE_REQUEST_PATTERNS = [
    r"\bsaran\s+(juga\s+)?dong\b",
    r"\b(minta|kasih|beri|ada)\s+saran\b",
    r"\bsaran\s+(dosen|pa|pembimbing|topik|judul|skripsi|ta|kp|riset|tema|matkul|kurikulum)\b",
    r"\bsarankan\b",
    r"\brekomendasi\s+saran\b",
]

ACADEMIC_COLLAB_PATTERNS = [
    r"\balgoritma\s+kerja\s*sama\b",
    r"\bsistem\s+kerja\s*sama\b",
    r"\b(topik|tema|judul|bidang|riset)\s+.*kerja\s*sama\b",
]

FORMAL_CONTACT_PATTERNS = [
    r"\b(memberikan|memberi|menyampaikan|ajukan|kirim)\s+(saran|kritik|masukan|pengaduan|keluhan)\b",
    r"\bsaran\s+(untuk|ke|bagi)\s+(prodi|jurusan|kampus|lab|laboratorium|fakultas|untan|perbaikan)\b",
    r"\bkritik\s+(dan\s+)?saran\b",
    r"\b(prosedur|penawaran|mengajukan|bentuk)\s+(kerja\s*sama|kerjasama|mou|kemitraan)\b",
    r"\b(kerja\s*sama|kerjasama)\s+(magang\s+industri|industri|institusi|kampus|perusahaan|vendor)\b",
    r"\b(pengaduan|keluhan|komplain)\s+(fasilitas|layanan|prodi|jurusan|kampus)\b",
]

CONVERSATIONAL_WORDS = {
    "halo", "hai", "hi", "kenapa", "yakin", "makasih", "terima kasih",
    "ok", "oke", "siap"
}

CONVERSATIONAL_PHRASES = [
    "siapa kamu", "kamu siapa", "bisa bantu apa", "bisa apa",
    "apa maksud", "maksudnya", "kok kamu", "apa kabar",
    "siapa yang bikin kamu", "siapa yang buat kamu", "siapa pembuat kamu",
    "siapa yang bikin luco", "siapa pembuatmu", "siapa developermu", "siapa developer kamu"
]

BOT_FEEDBACK_WORDS = {"kamu", "luco", "bot", "jawaban", "menjawab", "jawab", "asisten", "pembuat", "pengembang"}


ROUTER_PROMPT = """Kamu adalah router/klasifikator pertanyaan untuk chatbot Prodi Informatika UNTAN (Luco).
Tugasmu: klasifikasikan pertanyaan pengguna ke dalam salah satu kategori:

1. IN_SCOPE:
- Pertanyaan tentang Program Studi Informatika UNTAN (perkuliahan, alur KP, skripsi/TA, kurikulum, mata kuliah, profil dosen/staf, kegiatan kampus).
- Pertanyaan tentang identitas bot, sejarah pembuatan, pembuat/pengembang bot (Balin Niswah, Ragil Amirzaky, Andrean Stephanus, Edwin Hermili, Adjie Prasetya), atau profil mahasiswa Informatika UNTAN.
- Pertanyaan menanyakan nama seseorang (misal: "siapa X?", "kenal X?", "apakah X dosen/mahasiswa sini?").
- Sapaan, obrolan santai, respons percakapan wajar (misal: "halo", "kamu bisa apa?", "yakin?", "apa maksudmu?", "kenapa?").
- Pertanyaan lanjutan atau kata ganti bila ada konteks percakapan sebelumnya.

2. CONTACT_REDIRECT:
- Pesan resmi yang ditujukan untuk menyampaikan saran kebijakan kampus, pengaduan fasilitas resmi kampus, atau tawaran kerja sama kemitraan institusi/industri.
- JANGAN gunakan kategori ini untuk keluhan percakapan pengguna terhadap bot (misal: "kenapa jawabanmu salah?").

3. OUT_OF_SCOPE:
- Pertanyaan yang BENAR-BENAR di luar dunia kampus/akademik secara terang-terangan (misal: "resep rendang", "siapa presiden sekarang", "tugas matematika kalkulus umum", "harga motor").
{context_block}
Pertanyaan Pengguna: {query}

Balas HANYA JSON: {{"category": "IN_SCOPE"|"OUT_OF_SCOPE"|"CONTACT_REDIRECT", "reason": "alasan singkat"}}"""


def classify_heuristics(query: str) -> RouteResult | None:
    q = query.lower().strip()
    words = set(re.findall(r"\w+", q))
    q_padded = f" {q} "

    # 1. Pertanyaan profil dosen / nama orang (misal "siapa pak izuardo?", "siapa izuardo ? aku mau ajukan kerja sama")
    # Selalu loloskan sebagai IN_SCOPE agar agen dapat menjawab profil orang tersebut!
    dosen_and_people = {
        "izuardo", "zulkarnain", "herry", "sujaini", "anggi", "perwitasari", "srimurdianti",
        "desepta", "dimas", "arif", "bijaksana", "yus", "sholva", "enda", "esyudha", "enriko",
        "eva", "ripanti", "fauzan", "asrin", "hengky", "anra", "haried", "novriando",
        "helfi", "nasution", "heri", "priyanto", "ibnu", "azhar", "irwansyah", "khairul",
        "hafidh", "farid", "tsanauddin", "morteza", "muthahhari", "niken", "candraningrum",
        "novi", "safriadi", "rickhy", "artha", "rifqi", "anugrah", "rina", "septiriana",
        "rizki", "firdaus", "rudy", "nyoto", "tursina", "yulianti", "helen", "sastypratiwi",
        "ragil", "amirzaky", "lapnes", "tenzly", "andrean", "stephanus", "aji", "adjie", "prasetya",
        "balin", "niswah", "edwin", "hermili"
    }
    if bool(words & dosen_and_people):
        return RouteResult("IN_SCOPE", "Heuristik nama dosen/pengembang terdeteksi", None)

    # 2. Pengecekan apakah ini permintaan saran/rekomendasi akademik (misal "saran juga dong dosen PA nya")
    # atau topik akademik kerja sama (misal "algoritma kerja sama", "topik ... kerja sama")
    is_advice = any(re.search(p, q) for p in ADVICE_REQUEST_PATTERNS)
    is_academic_collab = any(re.search(p, q) for p in ACADEMIC_COLLAB_PATTERNS)

    # Jika pengguna meminta saran akademik atau topik riset, JANGAN alihkan ke kontak formal!
    if is_advice or is_academic_collab:
        if bool(words & PRODI_KEYWORDS):
            return RouteResult("IN_SCOPE", "Permintaan saran atau topik akademik prodi", None)

    # 3. Deteksi kontak/kritik/saran formal ke institusi
    is_formal_contact = any(re.search(p, q) for p in FORMAL_CONTACT_PATTERNS)
    if is_formal_contact:
        if not (words & BOT_FEEDBACK_WORDS):
            return RouteResult("CONTACT_REDIRECT", "Heuristik kontak/kerjasama resmi", CONTACT_REDIRECT_MESSAGE)

    # 4. Fast-path IN_SCOPE: Kata kunci prodi atau sapaan/percakapan umum
    is_conv = bool(words & CONVERSATIONAL_WORDS) or any(f" {p} " in q_padded or q.startswith(p) for p in CONVERSATIONAL_PHRASES)
    if (words & PRODI_KEYWORDS) or is_conv:
        return RouteResult("IN_SCOPE", "Heuristik kata kunci akademik/dosen/percakapan", None)

    return None


async def classify_query(
    query: str,
    history: list[dict] | None = None,
    llm: LLM | None = None,
) -> RouteResult:
    # 1. Cek heuristik instan (0 ms latency)
    fast = classify_heuristics(query)
    if fast is not None:
        return fast

    if llm is None:
        return RouteResult("IN_SCOPE", "Default in-scope tanpa LLM", None)

    # 2. Susun konteks singkat (4-6 pesan terakhir) jika ada
    context_block = ""
    if history:
        # Ambil maksimal 6 pesan terakhir
        recent = history[-6:]
        lines = [f"- {m['role']}: {m['content'][:150]}" for m in recent]
        context_block = "\nKonteks Percakapan Terakhir:\n" + "\n".join(lines) + "\n"

    # 3. Cek via LLM router
    try:
        resp = await llm.acomplete(ROUTER_PROMPT.format(context_block=context_block, query=query))
        text = str(resp).strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            cat = data.get("category", "IN_SCOPE").upper()
            reason = data.get("reason", "")
            if cat == "OUT_OF_SCOPE":
                return RouteResult("OUT_OF_SCOPE", reason, OUT_OF_SCOPE_MESSAGE)
            if cat == "CONTACT_REDIRECT":
                return RouteResult("CONTACT_REDIRECT", reason, CONTACT_REDIRECT_MESSAGE)
    except Exception:
        pass

    return RouteResult("IN_SCOPE", "Fallback in-scope", None)
