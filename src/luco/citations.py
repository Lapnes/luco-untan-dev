"""Pengecek sitasi: setiap tautan di jawaban harus muncul di teks yang benar-benar dibaca agent."""
from __future__ import annotations

import re

# Negative lookbehind (?<!!) mencegah tautan gambar Markdown ![alt](url) dianggap sebagai sitasi dokumen
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
URL_RE = re.compile(r"https?://[^\s)>\]\"']+")


def extract_links(answer: str) -> list[tuple[str, str]]:
    return LINK_RE.findall(answer)


def known_urls(tool_outputs: list[str]) -> set[str]:
    urls: set[str] = set()
    for out in tool_outputs:
        urls.update(u.rstrip(".,;") for u in URL_RE.findall(out))
        urls.update(m[1] for m in LINK_RE.findall(out))
    return urls


def check_citations(answer: str, tool_outputs: list[str]) -> dict:
    """Kembalikan {links, verified, unverified, all_verified, has_citations}. Tautan tanpa skema (path relatif) dicek sebagai teks."""
    known = known_urls(tool_outputs)
    blob = "\n".join(tool_outputs)
    verified, unverified = [], []
    seen_targets: set[str] = set()

    for text, target in extract_links(answer):
        # 1. Exact URL / path in known tool URLs or raw tool output blob
        ok = target in known or (not re.match(r"^[a-z][a-z0-9+.-]*:", target) and target in blob)
        
        # 2. Resilient relative path & title matching against tool output blob
        if not ok and not re.match(r"^[a-z][a-z0-9+.-]*:", target):
            clean_target = target.split("#")[0].strip("/")
            stem = clean_target.split("/")[-1].removesuffix(".md").lower()
            blob_low = blob.lower()
            if (len(stem) >= 4 and stem in blob_low) or (len(text.strip()) >= 6 and text.strip().lower() in blob_low):
                ok = True

        norm_target = target.strip().lower()

        # Deduplikasi: bila target sama sudah ada, pertahankan judul yang lebih deskriptif
        if norm_target in seen_targets:
            for existing in verified + unverified:
                if existing["target"].strip().lower() == norm_target:
                    if len(text.strip()) > len(existing["text"].strip()):
                        existing["text"] = text
                        existing["title"] = text
            continue

        seen_targets.add(norm_target)
        item = {
            "text": text,
            "target": target,
            "title": text,
            "path": target,
            "url": target,
        }
        (verified if ok else unverified).append(item)

    total = len(verified) + len(unverified)
    return {
        "links": total,
        "verified": verified,
        "unverified": unverified,
        "all_verified": bool(verified) and not unverified,
        "has_citations": total > 0,
    }
