"""Ambil publikasi dosen dari OpenAlex ke crawl-output/ (STAGING, bukan vault).

Input : crawl-output/dosen_seed.json  -> [{"nama": "...", "openalex_id": "A123..."}]
Output: crawl-output/<slug>.md        -> tabel publikasi untuk diverifikasi manual,
        lalu disalin ke vault/dosen/<slug>.md. Jangan menimpa tabel yang sudah diverifikasi.

Set OPENALEX_MAILTO di .env agar mendapat polite pool OpenAlex.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import httpx

OUT = Path("crawl-output")
API = "https://api.openalex.org/works"


def slug(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def fetch_works(author_id: str, mailto: str | None) -> list[dict]:
    params = {
        "filter": f"author.id:{author_id}",
        "per-page": 200,
        "select": "title,publication_year,doi,primary_location",
        "sort": "publication_year:desc",
    }
    if mailto:
        params["mailto"] = mailto
    r = httpx.get(API, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])


def table(works: list[dict]) -> str:
    rows = ["| Tahun | Judul | Venue | Tautan |", "|---|---|---|---|"]
    for w in works:
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "-"
        doi = w.get("doi")
        link = f"[DOI]({doi})" if doi else "-"
        title = (w.get("title") or "-").replace("|", "/")
        rows.append(f"| {w.get('publication_year') or '-'} | {title} | {venue} | {link} |")
    return "\n".join(rows)


def main() -> int:
    seed = OUT / "dosen_seed.json"
    if not seed.exists():
        print(f"Buat {seed} dulu: [{{'nama': '...', 'openalex_id': 'A...'}}]")
        return 1
    mailto = os.getenv("OPENALEX_MAILTO")
    for d in json.loads(seed.read_text(encoding="utf-8")):
        works = fetch_works(d["openalex_id"], mailto)
        (OUT / f"{slug(d['nama'])}.md").write_text(
            f"# {d['nama']}\n\n> HASIL CRAWL, BELUM DIVERIFIKASI\n\n## Publikasi\n{table(works)}\n", encoding="utf-8"
        )
        print(f"{d['nama']}: {len(works)} karya")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
