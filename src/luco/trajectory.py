"""Log trajectory (JSONL): satu baris per pertanyaan. Dipakai untuk analisis & bukti evaluasi."""
from __future__ import annotations

import json
import time
from pathlib import Path


def log_trajectory(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
