"""Periksa status OpenViking, jumlah chunk, vektor database, dan sebaran dokumen vault.

Jalankan:
    pixi run check-chunks
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from luco.config import get_settings
from openviking_sdk import SyncHTTPClient


def count_files(client: SyncHTTPClient, uri: str) -> int:
    try:
        items = client.ls(uri)
    except Exception:
        return 0
    count = 0
    for it in items:
        if it.get("isDir"):
            count += count_files(client, it["uri"])
        else:
            count += 1
    return count


def main() -> int:
    s = get_settings()
    print("=" * 60)
    print("🔍 PEMERIKSAAN KESEHATAN & CHUNK OPENVIKING (LUCO)")
    print("=" * 60)

    try:
        c = SyncHTTPClient(
            url=s.viking_url,
            api_key=s.viking_api_key,
            account="default",
            user="default",
            timeout=10.0,
        )
        c.initialize()
    except Exception as e:
        print(f"❌ Gagal menghubungkan ke OpenViking di {s.viking_url}: {e}")
        print("💡 Pastikan service berjalan dengan: pixi run up:deps")
        return 1

    health = c.health()
    status_icon = "✅" if health else "❌"
    print(f"\n1. Status Layanan OpenViking ({s.viking_url})")
    print(f"   Health Check: {status_icon} {'SEHAT (Online)' if health else 'OFFLINE'}")

    # VikingDB Vector Stats
    try:
        db_stat = c.vikingdb_status()
        print(f"\n2. Status Vektor Database (VikingDB)")
        print(f"   Nama Backend : {db_stat.get('name')}")
        print(f"   Status Vektor:\n   " + db_stat.get("status", "").replace("\n", "\n   "))
    except Exception as e:
        print(f"   Gagal membaca status VikingDB: {e}")

    # Stat Resources Root
    try:
        res_stat = c.stat(s.viking_root)
        total_chunks = res_stat.get("count", 0)
        print(f"\n3. Statistik Resource Root ({s.viking_root})")
        print(f"   Total Chunk / Simpul Teks : {total_chunks} chunk")
    except Exception as e:
        print(f"   Gagal membaca stat resource root: {e}")
        total_chunks = 0

    # Breakdown per folder
    print(f"\n4. Sebaran Chunk per Direktori Knowledge Vault:")
    print("   " + "-" * 52)
    print(f"   {'Direktori / Kategori':<25} | {'Jumlah Chunk':<15} | {'Format'}")
    print("   " + "-" * 52)

    try:
        top_items = c.ls(s.viking_root)
        for it in sorted(top_items, key=lambda x: x.get("name", "")):
            name = it["name"]
            if it.get("isDir"):
                cnt = count_files(c, it["uri"])
                print(f"   {name + '/':<25} | {cnt:<15} | Direktori")
            else:
                print(f"   {name:<25} | {1:<15} | Metadata")
    except Exception as e:
        print(f"   Gagal menguraikan direktori: {e}")

    print("   " + "-" * 52)
    print(f"   {'TOTAL KESELURUHAN':<25} | {total_chunks:<15} | Node Terindeks")
    print("   " + "-" * 52)
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
