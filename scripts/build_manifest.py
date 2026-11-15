"""Manifest Generator (fase build-time).

Sesuai rancangan Lembar Konsultasi Tugas Besar UAS AI 2026:
"Manifest Generator memindai berkas-berkas tersebut pada fase build-time
untuk membuat JSON Tree Manifest yang memetakan hirarki heading beserta nomor barisnya."

Hasil ditulis ke: vault/manifest.json
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


def parse_headings_from_text(text: str) -> list[dict]:
    lines = text.splitlines()
    headings: list[dict] = []
    
    # Deteksi posisi heading (#, ##, ###, dll.)
    heading_re = re.compile(r"^(#{1,6})\s+(.+)$")
    
    raw_positions = []
    for idx, line in enumerate(lines, start=1):
        # Lewati bagian frontmatter YAML
        m = heading_re.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            raw_positions.append({"level": level, "title": title, "line_start": idx})
            
    # Tentukan line_end untuk setiap heading
    total_lines = len(lines)
    for i, h in enumerate(raw_positions):
        next_start = raw_positions[i + 1]["line_start"] if i + 1 < len(raw_positions) else total_lines + 1
        h["line_end"] = max(h["line_start"], next_start - 1)
        headings.append(h)
        
    return headings


def build_manifest(vault_dir: Path, output_file: Path) -> dict:
    manifest = {
        "version": "1.0",
        "description": "JSON Tree Manifest hirarki heading dokumen vault/ untuk navigasi agen LLM",
        "total_documents": 0,
        "documents": {},
    }
    
    files = sorted(p for p in vault_dir.rglob("*.md") if not p.name.startswith("_") and not p.name.startswith("."))
    manifest["total_documents"] = len(files)
    
    for p in files:
        rel = p.relative_to(vault_dir).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeError:
            continue
            
        headings = parse_headings_from_text(text)
        
        # Cari judul utama (H1 pertama atau nama berkas)
        h1 = next((h["title"] for h in headings if h["level"] == 1), p.stem.replace("-", " ").title())
        
        manifest["documents"][rel] = {
            "title": h1,
            "total_lines": len(text.splitlines()),
            "headings_count": len(headings),
            "headings": headings,
        }
        
    output_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    vault_dir = root / "vault"
    output_file = vault_dir / "manifest.json"
    
    if not vault_dir.is_dir():
        print(f"ERROR: folder {vault_dir} tidak ditemukan", file=sys.stderr)
        return 1
        
    manifest = build_manifest(vault_dir, output_file)
    print(f"Manifest berhasil dibuat: {manifest['total_documents']} dokumen dipetakan -> {output_file.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

