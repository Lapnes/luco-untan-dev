"""REPL sederhana: pixi run chat"""
import asyncio

from .agent import Luco


async def main() -> None:
    luco = Luco()
    history: list[dict] = []
    print("Luco 🐦 siap. Ketik 'exit' untuk keluar.")
    while True:
        q = input("\nKamu: ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        r = await luco.ask(q, history=history, record_audit=True, endpoint="cli")
        print(f"\nLuco: {r['answer']}")
        if r["citations"]["unverified"]:
            print(f"[peringatan] tautan belum terverifikasi: {r['citations']['unverified']}")
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": r["answer"]}]


if __name__ == "__main__":
    asyncio.run(main())
