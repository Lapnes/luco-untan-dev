"""CLI Monitor & Audit Dashboard untuk Sistem Luco (luco-untan).

Menyediakan pemantauan status layanan, ringkasan audit token & biaya,
serta pelacakan riwayat interaksi pengguna secara real-time.
Mendukung ekspor CSV dan mode live watch.

Penggunaan:
  pixi run monitor             # Tampilan ringkasan instan
  pixi run monitor --watch     # Live watch auto-refresh setiap 3 detik
  pixi run monitor --export    # Ekspor dataset audit ke CSV
  pixi run monitor --limit 20  # Tampilkan 20 catatan terakhir
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

import asyncpg
import httpx

from luco.config import get_settings


# Warna ANSI untuk tampilan terminal
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


async def check_service_health() -> Dict[str, Dict[str, Any]]:
    """Memeriksa status hidup/mati dari seluruh subsistem dependensi."""
    services = {
        "PostgreSQL": {"port": 5432, "status": "UNKNOWN", "detail": ""},
        "OpenViking": {"port": 1933, "status": "UNKNOWN", "detail": ""},
        "IndoBERT Embedder": {"port": 8001, "status": "UNKNOWN", "detail": ""},
        "Antigravity Proxy": {"port": 3000, "status": "UNKNOWN", "detail": ""},
        "Luco API Server": {"port": 8000, "status": "UNKNOWN", "detail": ""},
    }

    settings = get_settings()

    # 1. Cek PostgreSQL
    try:
        conn = await asyncpg.connect(settings.database_url, timeout=1.5)
        count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs")
        await conn.close()
        services["PostgreSQL"]["status"] = "UP"
        services["PostgreSQL"]["detail"] = f"audit_logs={count} baris"
    except Exception as e:
        services["PostgreSQL"]["status"] = "DOWN"
        services["PostgreSQL"]["detail"] = "Gagal koneksi database"

    # 2. Cek HTTP Services
    async with httpx.AsyncClient(timeout=1.5, follow_redirects=True) as client:
        # OpenViking
        try:
            r = await client.get("http://localhost:1933/health")
            if r.status_code == 200:
                services["OpenViking"]["status"] = "UP"
                services["OpenViking"]["detail"] = "port 1933 (healthy)"
            else:
                services["OpenViking"]["status"] = "DEGRADED"
                services["OpenViking"]["detail"] = f"HTTP {r.status_code}"
        except Exception:
            services["OpenViking"]["status"] = "DOWN"
            services["OpenViking"]["detail"] = "Tidak merespons"

        # IndoBERT Embedder
        try:
            r = await client.get("http://localhost:8001/health")
            if r.status_code == 200:
                data = r.json()
                services["IndoBERT Embedder"]["status"] = "UP"
                services["IndoBERT Embedder"]["detail"] = f"{data.get('model', 'indobert')} (dim=768)"
            else:
                services["IndoBERT Embedder"]["status"] = "DEGRADED"
        except Exception:
            services["IndoBERT Embedder"]["status"] = "DOWN"
            services["IndoBERT Embedder"]["detail"] = "Tidak merespons"

        # Antigravity Proxy
        try:
            r = await client.get("http://localhost:3000/")
            if r.status_code in (200, 302, 307):
                services["Antigravity Proxy"]["status"] = "UP"
                services["Antigravity Proxy"]["detail"] = "port 3000 (Gemini Proxy)"
            else:
                services["Antigravity Proxy"]["status"] = "DEGRADED"
        except Exception:
            services["Antigravity Proxy"]["status"] = "DOWN"
            services["Antigravity Proxy"]["detail"] = "Tidak merespons"

        # Luco API Server
        try:
            r = await client.get("http://localhost:8000/health")
            if r.status_code == 200:
                services["Luco API Server"]["status"] = "UP"
                services["Luco API Server"]["detail"] = "port 8000 (FastAPI)"
            else:
                services["Luco API Server"]["status"] = "DEGRADED"
        except Exception:
            services["Luco API Server"]["status"] = "STOPPED"
            services["Luco API Server"]["detail"] = "Gunakan: pixi run serve"

    return services


async def fetch_audit_summary() -> Dict[str, Any]:
    """Mengambil ringkasan metrik audit dari PostgreSQL atau fallback file JSONL."""
    settings = get_settings()
    summary: Dict[str, Any] = {
        "source": "database",
        "total_requests": 0,
        "total_users": 0,
        "total_sessions": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "total_cost_idr": 0.0,
        "avg_latency_s": 0.0,
        "total_rejected": 0,
        "rejection_rate_percent": 0.0,
        "models": [],
    }

    # Coba dari database terlebih dahulu
    try:
        conn = await asyncpg.connect(settings.database_url, timeout=2.0)
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_requests,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(DISTINCT session_id) AS total_sessions,
                COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(estimated_cost_usd), 0) AS total_cost_usd,
                COALESCE(AVG(latency_s), 0) AS avg_latency_s,
                COUNT(*) FILTER (WHERE rejected = TRUE) AS total_rejected
            FROM audit_logs
            """
        )
        if row and row["total_requests"] > 0:
            summary.update(dict(row))
            summary["total_cost_usd"] = float(summary["total_cost_usd"])
            summary["total_cost_idr"] = round(summary["total_cost_usd"] * settings.usd_to_idr, 2)
            summary["avg_latency_s"] = round(float(summary["avg_latency_s"]), 2)
            tot_req = summary["total_requests"]
            summary["rejection_rate_percent"] = round((summary["total_rejected"] / tot_req * 100), 2) if tot_req > 0 else 0.0

            # Breakdown per model
            m_rows = await conn.fetch(
                """
                SELECT model, COUNT(*) AS requests, COALESCE(SUM(total_tokens), 0) AS tokens, COALESCE(SUM(estimated_cost_usd), 0) AS cost_usd
                FROM audit_logs GROUP BY model ORDER BY requests DESC
                """
            )
            summary["models"] = [
                {
                    "model": r["model"],
                    "requests": r["requests"],
                    "tokens": r["tokens"],
                    "cost_usd": float(r["cost_usd"]),
                    "cost_idr": round(float(r["cost_usd"]) * settings.usd_to_idr, 2),
                }
                for r in m_rows
            ]
            await conn.close()
            return summary
        await conn.close()
    except Exception:
        pass

    # Fallback ke logs/audit.jsonl jika database belum terisi atau offline
    summary["source"] = "file (logs/audit.jsonl)"
    audit_path = Path("logs/audit.jsonl")
    if not audit_path.exists():
        return summary

    records = []
    try:
        with audit_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        continue
    except Exception:
        return summary

    if not records:
        return summary

    summary["total_requests"] = len(records)
    summary["total_users"] = len({r.get("user_id") for r in records if r.get("user_id")})
    summary["total_sessions"] = len({r.get("session_id") for r in records if r.get("session_id")})
    summary["total_prompt_tokens"] = sum(r.get("prompt_tokens", 0) for r in records)
    summary["total_completion_tokens"] = sum(r.get("completion_tokens", 0) for r in records)
    summary["total_tokens"] = sum(r.get("total_tokens", 0) for r in records)
    summary["total_cost_usd"] = round(sum(r.get("estimated_cost_usd", 0.0) for r in records), 6)
    summary["total_cost_idr"] = round(sum(r.get("estimated_cost_idr", 0.0) for r in records), 2)
    summary["avg_latency_s"] = round(sum(r.get("latency_s", 0.0) for r in records) / len(records), 2)
    summary["total_rejected"] = sum(1 for r in records if r.get("rejected"))
    summary["rejection_rate_percent"] = round((summary["total_rejected"] / len(records)) * 100, 2)

    # Models breakdown
    models_dict: Dict[str, Dict[str, Any]] = {}
    for r in records:
        m = r.get("model", "unknown")
        if m not in models_dict:
            models_dict[m] = {"model": m, "requests": 0, "tokens": 0, "cost_usd": 0.0, "cost_idr": 0.0}
        models_dict[m]["requests"] += 1
        models_dict[m]["tokens"] += r.get("total_tokens", 0)
        models_dict[m]["cost_usd"] += r.get("estimated_cost_usd", 0.0)
        models_dict[m]["cost_idr"] += r.get("estimated_cost_idr", 0.0)

    summary["models"] = sorted(models_dict.values(), key=lambda x: x["requests"], reverse=True)
    return summary


async def fetch_recent_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Mengambil riwayat log audit terakhir dari PostgreSQL atau logs/audit.jsonl."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(settings.database_url, timeout=2.0)
        rows = await conn.fetch(
            f"""
            SELECT created_at, model, endpoint, question, total_tokens, estimated_cost_usd, latency_s, steps, rejected, reason
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT {limit}
            """
        )
        await conn.close()
        res = []
        for r in rows:
            d = dict(r)
            d["timestamp"] = d["created_at"].strftime("%H:%M:%S") if d.get("created_at") else "-"
            d["estimated_cost_idr"] = round(float(d.get("estimated_cost_usd", 0.0)) * settings.usd_to_idr, 2)
            res.append(d)
        if res:
            return res
    except Exception:
        pass

    # Fallback ke logs/audit.jsonl
    audit_path = Path("logs/audit.jsonl")
    if not audit_path.exists():
        return []

    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    recent = lines[-limit:]
    records = []
    for line in reversed(recent):
        if not line:
            continue
        try:
            d = json.loads(line)
            ts = d.get("timestamp", "")
            d["timestamp"] = ts.split("T")[1][:8] if "T" in ts else ts
            records.append(d)
        except Exception:
            continue
    return records


def export_audit_to_csv(output_path: str = "docs/laporan/raw/luco_audit_dataset.csv") -> int:
    """Mengekspor seluruh catatan audit ke CSV."""
    audit_path = Path("logs/audit.jsonl")
    if not audit_path.exists():
        print(f"{Color.RED}[Error]{Color.RESET} Berkas logs/audit.jsonl tidak ditemukan.")
        return 0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    count = 0
    with audit_path.open("r", encoding="utf-8") as f_in, open(output_path, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow([
            "id", "timestamp", "user_email", "endpoint", "model",
            "question", "prompt_tokens", "completion_tokens", "total_tokens",
            "cost_usd", "cost_idr", "latency_s", "steps", "rejected", "reason"
        ])
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                writer.writerow([
                    r.get("id"), r.get("timestamp"), r.get("user_email") or "-",
                    r.get("endpoint"), r.get("model"),
                    (r.get("question") or "").replace("\n", " "),
                    r.get("prompt_tokens", 0), r.get("completion_tokens", 0), r.get("total_tokens", 0),
                    r.get("estimated_cost_usd", 0.0), r.get("estimated_cost_idr", 0.0),
                    r.get("latency_s", 0.0), r.get("steps", 0),
                    r.get("rejected", False), r.get("reason") or "-"
                ])
                count += 1
            except Exception:
                continue

    return count


async def render_dashboard(limit: int = 10, clear: bool = False):
    """Menampilkan dashboard audit & monitoring yang elegan di terminal."""
    if clear:
        os.system("cls" if os.name == "nt" else "clear")

    services = await check_service_health()
    summary = await fetch_audit_summary()
    recent = await fetch_recent_logs(limit=limit)

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"{Color.CYAN}{Color.BOLD}========================================================================================={Color.RESET}")
    print(f"{Color.CYAN}{Color.BOLD}   LUCO 🐦 MONITOR & AUDIT DASHBOARD — PRODI INFORMATIKA UNTAN{Color.RESET}")
    print(f"{Color.GRAY}   Waktu: {now_str} | Sumber Data: {summary['source']}{Color.RESET}")
    print(f"{Color.CYAN}{Color.BOLD}========================================================================================={Color.RESET}")

    # 1. Health Subsistem
    print(f"\n{Color.BOLD}1. STATUS LAYANAN & INFRASTRUKTUR:{Color.RESET}")
    for name, info in services.items():
        st = info["status"]
        if st == "UP":
            st_color = f"{Color.GREEN}[UP]{Color.RESET}"
        elif st == "STOPPED":
            st_color = f"{Color.YELLOW}[OFF]{Color.RESET}"
        else:
            st_color = f"{Color.RED}[{st}]{Color.RESET}"
        print(f"   - {name:<20}: {st_color} {Color.GRAY}{info['detail']}{Color.RESET}")

    # 2. Ringkasan Eksekutif Audit
    print(f"\n{Color.BOLD}2. RINGKASAN METRIK AUDIT & OPERASIONAL:{Color.RESET}")
    print(f"   - Total Permintaan (Requests) : {Color.BOLD}{summary['total_requests']:,}{Color.RESET}")
    print(f"   - Pengguna / Sesi Aktif       : {summary['total_users']} pengguna / {summary['total_sessions']} sesi")
    print(f"   - Total Konsumsi Token        : {Color.BOLD}{summary['total_tokens']:,}{Color.RESET} ({summary['total_prompt_tokens']:,} in / {summary['total_completion_tokens']:,} out)")
    print(f"   - Total Estimasi Biaya        : {Color.GREEN}Rp {summary['total_cost_idr']:,.2f}{Color.RESET} (${summary['total_cost_usd']:.4f} USD)")
    print(f"   - Rata-rata Latensi Respons   : {summary['avg_latency_s']} detik")
    print(f"   - Rasio Penolakan / Router    : {summary['rejection_rate_percent']}% ({summary['total_rejected']} request fast-reject / out-of-scope)")

    # Breakdown Model
    if summary["models"]:
        print(f"\n   {Color.DIM}Breakdown Penggunaan Model:{Color.RESET}")
        for m in summary["models"]:
            print(f"     * {m['model']:<24}: {m['requests']:>3} req | {m['tokens']:>6,} tok | Rp {m.get('cost_idr', 0.0):>7,.2f}")

    # 3. Log Audit Terakhir
    print(f"\n{Color.BOLD}3. JEJAK AUDIT TERAKHIR ({len(recent)} Transaksi):{Color.RESET}")
    header = f"   {'Waktu':<8} | {'Model':<18} | {'Tokens':<6} | {'Biaya (IDR)':<11} | {'Latensi':<7} | {'Steps':<5} | {'Status':<8} | {'Pertanyaan'}"
    print(f"{Color.GRAY}{header}{Color.RESET}")
    print(f"   {'-'*8}-+-{'-'*18}-+-{'-'*6}-+-{'-'*11}-+-{'-'*7}-+-{'-'*5}-+-{'-'*8}-+-{'-'*20}")

    for r in recent:
        ts = r.get("timestamp", "-")[:8]
        model = r.get("model", "-")[:18]
        tok = r.get("total_tokens", 0)
        cost = r.get("estimated_cost_idr", 0.0)
        lat = f"{r.get('latency_s', 0.0):.2f}s"
        steps = r.get("steps", 0)
        rej = r.get("rejected", False)
        status_str = f"{Color.YELLOW}REJECT{Color.RESET}" if rej else f"{Color.GREEN}OK{Color.RESET}"
        q_snippet = (r.get("question") or "").replace("\n", " ")[:35]
        if len(r.get("question") or "") > 35:
            q_snippet += "..."

        print(f"   {ts:<8} | {model:<18} | {tok:>6} | Rp {cost:>8.2f} | {lat:>7} | {steps:>5} | {status_str:<17} | {q_snippet}")

    print(f"\n{Color.GRAY}Tips: Jalankan 'pixi run monitor --watch' untuk live monitoring real-time, atau '--export' untuk simpan CSV.{Color.RESET}")
    print(f"{Color.CYAN}========================================================================================={Color.RESET}\n")


async def main_async():
    parser = argparse.ArgumentParser(description="Luco Monitor & Audit Dashboard")
    parser.add_argument("-w", "--watch", action="store_true", help="Mode live watch (auto-refresh setiap 3 detik)")
    parser.add_argument("-e", "--export", action="store_true", help="Ekspor data audit ke CSV di docs/laporan/raw/")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Jumlah baris log audit yang ditampilkan (default: 10)")
    args = parser.parse_args()

    if args.export:
        csv_file = "docs/laporan/raw/luco_audit_dataset.csv"
        count = export_audit_to_csv(csv_file)
        print(f"{Color.GREEN}[Sukses]{Color.RESET} Berhasil mengekspor {count} catatan audit ke {csv_file}")
        return

    if args.watch:
        try:
            while True:
                await render_dashboard(limit=args.limit, clear=True)
                await asyncio.sleep(3)
        except KeyboardInterrupt:
            print("\nMonitoring dihentikan.")
    else:
        await render_dashboard(limit=args.limit, clear=False)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

