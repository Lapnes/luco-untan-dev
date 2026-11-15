"""Spike OpenViking: cek koneksi, struktur URI hasil ingest, dan kualitas find untuk pertanyaan Indonesia.

  pixi run spike

Yang dicek (catat hasilnya):
  1. health OK dan ls root menampilkan struktur folder vault
  2. find() untuk pertanyaan in_scope di eval/questions.jsonl mengembalikan dokumen yang benar
  3. read() pada URI hasil find mengembalikan teks penuh (termasuk frontmatter `sumber`)
  4. tautan relatif [nama](path.md) bisa di-resolve lewat read_doc
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from luco.backends import VikingBackend  # noqa: E402
from luco.config import get_settings  # noqa: E402


def show(title: str, obj) -> None:
    text = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, default=str)
    print(f"\n=== {title} (type={type(obj).__name__}) ===\n{text[:1500]}")


def main() -> int:
    s = get_settings()
    b = VikingBackend(s)
    print("health:", b.client.health())
    show("ls root", b.ls(""))

    qfile = Path("eval/questions.jsonl")
    questions = [json.loads(l) for l in qfile.read_text(encoding="utf-8").splitlines() if l.strip()] if qfile.exists() else []
    for q in [x for x in questions if x.get("category") == "in_scope"][:10]:
        show(f"find: {q['question']}", b.find(q["question"], limit=3))
        print("harapan sumber:", q.get("expected_sources"))

    if len(sys.argv) > 1:
        show(f"read {sys.argv[1]}", b.read(sys.argv[1]))
    else:
        print("\nTip: python scripts/spike.py dosen/index.md  # uji read dengan path relatif")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
