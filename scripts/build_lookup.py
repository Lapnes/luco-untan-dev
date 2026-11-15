"""Bangun vault/lookup.json dari frontmatter catatan bertipe `dosen`.

Jalankan: pixi run build-lookup
Sumber kebenaran = vault. JANGAN edit lookup.json manual.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELDS = ["nama", "nip", "email", "jabatan", "kelompok_keahlian", "openalex_id", "diverifikasi", "alias"]


def parse_frontmatter(text: str) -> dict:
    m = FM_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def build(vault: Path) -> list[dict]:
    records = []
    for path in sorted(vault.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm.get("tipe") != "dosen":
            continue
        rec = {k: fm.get(k) for k in FIELDS}
        rec["nip"] = None if rec["nip"] is None else str(rec["nip"])
        rec["file"] = path.relative_to(vault).as_posix()
        rec["sumber"] = fm.get("sumber") or []
        records.append(rec)
    records.sort(key=lambda r: (r.get("nama") or "").lower())
    return records


def main() -> int:
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else "vault")
    out = vault / "lookup.json"
    records = build(vault)
    missing = [r["file"] for r in records if not r.get("nama") or not r.get("nip")]
    out.write_text(json.dumps({"dosen": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(records)} dosen -> {out}")
    for f in missing:
        print(f"PERINGATAN: nama/nip kosong di {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
