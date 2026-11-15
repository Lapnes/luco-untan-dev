from __future__ import annotations

import json
import re

from .config import Settings

COMMON_HONORIFICS = {
    "dr", "dr.", "prof", "prof.", "ir", "ir.", "ph.d", "phd", "m.kom", "mkom",
    "s.kom", "skom", "s.t", "st", "m.t", "mt", "m.cs", "mcs", "m.m", "mm",
    "pak", "bapak", "bu", "ibu", "siapa", "itu", "profil", "dosen", "tentang",
}


def load_lookup(settings: Settings) -> list[dict]:
    if not settings.lookup_json.exists():
        return []
    return json.loads(settings.lookup_json.read_text(encoding="utf-8")).get("dosen", [])


def _clean_query_terms(query: str) -> list[str]:
    # Mengabaikan gelar akademis, sapaan, dan kata tanya umum agar pencarian nama/alias seperti 'Pak Edo' tetap cocok dengan 'Edo'
    raw = [t.strip(".,;:()") for t in query.lower().split()]
    filtered = [t for t in raw if t and t not in COMMON_HONORIFICS]
    return filtered or raw


def lookup_records(records: list[dict], query: str, limit: int = 10) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []

    terms = _clean_query_terms(q)
    out = []
    for r in records:
        kk = r.get("kelompok_keahlian")
        kk_items = kk if isinstance(kk, list) else ([str(kk)] if kk else [])
        aliases = r.get("alias") or []
        alias_items = aliases if isinstance(aliases, list) else [str(aliases)]
        hay = " ".join(
            str(x)
            for x in [
                r.get("nama"),
                r.get("nip"),
                r.get("email"),
                r.get("jabatan"),
                r.get("openalex_id"),
                r.get("file"),
                *kk_items,
                *alias_items,
            ]
            if x
        ).lower()
        if q in hay or all(t in hay for t in terms):
            out.append(r)
    return out[:limit]
