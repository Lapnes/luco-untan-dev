"""Masukkan vault ke OpenViking.

  pixi run ingest                 # satu kali untuk seluruh folder vault/
  pixi run ingest -- --per-file   # per file (bila mode folder tidak mempertahankan struktur)
  pixi run ingest -- --vectors-only  # lewati ringkasan VLM (L0/L1), hanya embedding

CATATAN: perilaku add_resource untuk folder dan struktur URI hasilnya belum diverifikasi.
Jalankan `pixi run spike` setelah ingest untuk melihat struktur sebenarnya.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from luco.config import get_settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-file", action="store_true")
    ap.add_argument("--vectors-only", action="store_true")
    args = ap.parse_args()

    from openviking_sdk import SyncHTTPClient

    s = get_settings()
    client = SyncHTTPClient(
        url=s.viking_url,
        api_key=s.viking_api_key,
        account="default",
        user="default",
        timeout=300.0,
    )
    client.initialize()
    print("health:", client.health())

    options = {"reason": "luco vault import"}
    if args.vectors_only:
        options["processing_mode"] = "vectors_only"

    if not args.per_file:
        res = client.add_resource(path=str(s.vault_dir.resolve()), to=s.viking_root, wait=True, options=options)
        print(res)
    else:
        for p in sorted(s.vault_dir.rglob("*.md")):
            rel = p.relative_to(s.vault_dir).as_posix()
            target = f"{s.viking_root}/{rel}"
            res = client.add_resource(path=str(p.resolve()), to=target, wait=True, options=options)
            print(rel, "->", res)
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
