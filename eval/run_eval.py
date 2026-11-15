"""Jalankan evaluasi: Luco (agentic RAG) vs LLM yang sama tanpa RAG.

  pixi run eval                    # jalankan semua pertanyaan, simpan ke eval/reports/
  pixi run eval -- --judge         # tambah penilaian LLM-as-judge (skor 1-5, halusinasi, penolakan)
  pixi run eval -- --no-baseline   # lewati baseline tanpa RAG

Metrik ringkasan: rata-rata skor, % sitasi terverifikasi, % penolakan benar (out_of_scope/saran_kerjasama/not_in_docs),
rata-rata langkah agent. Ganti `reference` di questions.jsonl dengan jawaban acuan nyata dari dokumen.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from luco.agent import Luco  # noqa: E402

JUDGE_PROMPT = """Kamu penilai. Nilai jawaban chatbot Prodi Informatika UNTAN.
Kategori pertanyaan: {category}
Pertanyaan: {question}
Jawaban acuan / perilaku yang diharapkan: {reference}
Jawaban chatbot: {answer}

Balas HANYA JSON: {{"skor": 1-5, "halusinasi": true/false, "perilaku_benar": true/false, "alasan": "singkat"}}
- skor: ketepatan terhadap acuan (5 = tepat penuh).
- halusinasi: true bila ada fakta spesifik yang tidak didukung acuan.
- perilaku_benar: untuk kategori selain in_scope, true bila chatbot menolak/mengarahkan ke kontak/menyatakan tidak tahu sesuai harapan; untuk in_scope true bila menjawab (bukan menolak)."""


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


async def judge(luco: Luco, q: dict, answer: str) -> dict:
    prompt = JUDGE_PROMPT.format(category=q["category"], question=q["question"], reference=q["reference"], answer=answer)
    for attempt in range(4):
        try:
            resp = await luco.llm.acomplete(prompt)
            parsed = parse_json(str(resp))
            if parsed:
                return parsed
        except Exception as e:
            if attempt == 3:
                return {"skor": None, "halusinasi": False, "perilaku_benar": False, "alasan": f"Gagal judge: {e}"}
            await asyncio.sleep(1.5 * (attempt + 1))
    return {"skor": None, "halusinasi": False, "perilaku_benar": False, "alasan": "Respons judge kosong"}


async def baseline(luco: Luco, question: str) -> str:
    for attempt in range(4):
        try:
            resp = await luco.llm.acomplete(f"Kamu asisten Prodi Informatika UNTAN. Jawab singkat.\n\nPertanyaan: {question}")
            return str(resp)
        except Exception as e:
            if attempt == 3:
                return f"[Gagal mendapatkan baseline dari model: {e}]"
            await asyncio.sleep(1.5 * (attempt + 1))
    return "[Gagal mendapatkan baseline dari model: timeout]"


def mean(xs: list) -> float | None:
    clean = []
    for x in xs:
        if x is None:
            continue
        try:
            clean.append(float(x))
        except (ValueError, TypeError):
            continue
    return round(sum(clean) / len(clean), 2) if clean else None


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--questions", default="eval/questions.jsonl")
    args = ap.parse_args()

    qs = [json.loads(l) for l in Path(args.questions).read_text(encoding="utf-8").splitlines() if l.strip()]
    luco = Luco()
    rows = []
    for q in qs:
        try:
            r = await luco.ask(q["question"], log=True)
        except Exception as e:
            r = {
                "question": q["question"],
                "answer": f"[Error eksekusi Luco: {e}]",
                "steps": 0,
                "trajectory": [],
                "citations": {"links": 0, "has_citations": False, "all_verified": False, "verified": [], "unverified": []},
                "latency_s": 0.0,
                "backend": luco.settings.backend,
                "error": repr(e),
                "rejected": False,
                "reason": None,
            }
        row = {"id": q["id"], "category": q["category"], "question": q["question"], "luco": r}
        if not args.no_baseline:
            row["baseline_answer"] = await baseline(luco, q["question"])
        if args.judge:
            row["luco_judge"] = await judge(luco, q, r["answer"])
            if not args.no_baseline:
                row["baseline_judge"] = await judge(luco, q, row["baseline_answer"])
        rows.append(row)
        sitasi_ok = r["citations"].get("all_verified", True)
        print(f"{q['id']} [{q['category']}] steps={r['steps']} sitasi_ok={sitasi_ok}")

    out = Path("eval/reports") / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    with_links = [r for r in rows if r["luco"]["citations"].get("links", 0)]
    print("\n== RINGKASAN ==")
    print("rata-rata langkah:", mean([r["luco"]["steps"] for r in rows]))
    print("sitasi terverifikasi (jawaban bertautan):", f"{sum(r['luco']['citations']['all_verified'] for r in with_links)}/{len(with_links)}")
    if args.judge:
        for name in ("luco_judge", "baseline_judge"):
            js = [r[name] for r in rows if name in r]
            if js:
                print(f"{name}: skor={mean([j.get('skor') for j in js])} halusinasi={sum(bool(j.get('halusinasi')) for j in js)}/{len(js)} perilaku_benar={sum(bool(j.get('perilaku_benar')) for j in js)}/{len(js)}")
    print("laporan:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
