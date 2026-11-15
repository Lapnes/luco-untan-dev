"""Cek tautan relatif [teks](path.md) antar-catatan di vault. Exit 1 bila ada yang rusak."""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def broken_links(vault: Path) -> list[tuple[str, str]]:
    bad = []
    for path in sorted(vault.rglob("*.md")):
        text = CODE_RE.sub("", path.read_text(encoding="utf-8"))
        for target in LINK_RE.findall(text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue  # url eksternal / anchor
            rel = target.split("#", 1)[0]
            if not rel:
                continue
            if not (path.parent / rel).resolve().exists():
                bad.append((path.relative_to(vault).as_posix(), target))
    return bad


def main() -> int:
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else "vault")
    bad = broken_links(vault)
    for src, target in bad:
        print(f"RUSAK: {src} -> {target}")
    print(f"{len(bad)} tautan rusak")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
