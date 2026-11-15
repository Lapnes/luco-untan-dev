"""Backend pengetahuan: OpenViking (HTTP SDK) atau Local (kata kunci di vault).

Kedua backend punya antarmuka sama: find / read / ls.
Backend Local juga jadi jalur cadangan dan pembanding di evaluasi.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Protocol

from .config import Settings


class Backend(Protocol):
    def find(self, query: str, limit: int = 5) -> str: ...
    def read(self, uri: str) -> str: ...
    def ls(self, uri: str = "") -> str: ...


def _safe_rel(path: str) -> str:
    """Normalisasi path relatif vault; tolak keluar dari root."""
    parts = []
    for part in path.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == ".." or part == "~":
            if not parts:
                raise ValueError("path keluar dari vault")
            parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


class LocalBackend:
    """Pencarian kata kunci sederhana (tanpa embedding). Untuk cadangan & baseline."""

    def __init__(self, settings: Settings):
        self.root = settings.vault_dir
        self._cache: dict[Path, tuple[float, str, str, str]] = {}

    def _get_file_data(self, p: Path) -> tuple[str, str, str]:
        mtime = p.stat().st_mtime
        cached = self._cache.get(p)
        if cached and cached[0] == mtime:
            return cached[1], cached[2], cached[3]
        text = p.read_text(encoding="utf-8")
        low = text.lower()
        first = next((l.strip() for l in text.splitlines() if l.strip() and not l.startswith("---")), "")
        self._cache[p] = (mtime, text, low, first)
        return text, low, first

    def _files(self) -> list[Path]:
        return sorted(p for p in self.root.rglob("*.md") if not p.name.startswith("_"))

    def find(self, query: str, limit: int = 5) -> str:
        stopwords = {"dan", "yang", "untuk", "dari", "pada", "ke", "di", "ini", "itu", "atau", "apa", "siapa", "berapa", "bagaimana", "dimana", "ada", "saja"}
        terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2 and t not in stopwords]
        if not terms:
            terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 1]
        scored = []
        for p in self._files():
            _, low, first = self._get_file_data(p)
            rel_posix = p.relative_to(self.root).as_posix()
            rel_low = rel_posix.lower()
            first_low = first.lower()

            # Skor frekuensi kata dasar
            score = sum(low.count(t) for t in terms)
            # Bobot penguat jika istilah muncul di baris judul pertama atau nama berkas
            score += sum(10 for t in terms if t in first_low)
            score += sum(15 for t in terms if t in rel_low)

            if score > 0:
                scored.append((score, rel_posix, first[:160]))
        scored.sort(reverse=True)
        return json.dumps(
            [{"uri": u, "score": s, "snippet": snip} for s, u, snip in scored[:limit]],
            ensure_ascii=False,
        )

    def read(self, uri: str) -> str:
        try:
            rel = _safe_rel(uri.split("://", 1)[-1] if "://" in uri else uri)
        except ValueError as e:
            return f"ERROR: {e}"
        p = self.root / rel
        if not p.is_file():
            return f"ERROR: file tidak ditemukan: {rel}"
        text, _, _ = self._get_file_data(p)
        return text

    def ls(self, uri: str = "") -> str:
        try:
            rel = _safe_rel(uri)
        except ValueError as e:
            return f"ERROR: {e}"
        d = self.root / rel
        if not d.is_dir():
            return f"ERROR: folder tidak ditemukan: {rel}"
        return json.dumps(sorted(x.name + ("/" if x.is_dir() else "") for x in d.iterdir()), ensure_ascii=False)


class VikingBackend:
    """OpenViking via openviking-sdk (HTTP)."""

    def __init__(self, settings: Settings):
        from openviking_sdk import SyncHTTPClient

        self.settings = settings
        self.root = settings.viking_root
        self.client = SyncHTTPClient(
            url=settings.viking_url,
            api_key=settings.viking_api_key,
            account="default",
            user="default",
        )
        try:
            self.client.initialize()
        except Exception as e:
            # Cegah startup crash jika container OpenViking masih dalam proses booting
            print(f"[warning] Inisialisasi OpenViking ditunda: {e}")

    def _uri(self, uri: str) -> str:
        if uri.startswith("viking://"):
            return uri
        return f"{self.root}/{_safe_rel(uri)}"

    @staticmethod
    def _dump(obj: Any) -> str:
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, ensure_ascii=False, default=str)
        except TypeError:
            return str(obj)

    def find(self, query: str, limit: int = 5) -> str:
        try:
            try:
                raw = self.client.find(query=query, limit=limit, target_uri=self.root)
            except TypeError:
                raw = self.client.find(query=query, limit=limit)
            
            # Normalisasi output agar seragam dengan LocalBackend: [{"uri": ..., "score": ..., "snippet": ...}]
            items = []
            if isinstance(raw, dict):
                items = raw.get("resources") or []
            elif isinstance(raw, list):
                items = raw
            
            normalized = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                u = item.get("uri", "")
                rel_u = u.replace(f"{self.root}/", "") if u.startswith(self.root) else u
                if rel_u.startswith("viking://"):
                    rel_u = rel_u.split("://", 1)[-1]
                
                score = round(float(item.get("score", 0.0)), 4)
                snippet = item.get("abstract", "") or item.get("snippet", "")
                
                # Jika snippet kosong dari engine, ambil cuplikan baris pertama dokumen
                if not snippet and rel_u:
                    doc_text = self.read(rel_u)
                    if doc_text and not doc_text.startswith("ERROR"):
                        lines = [l.strip() for l in doc_text.splitlines() if l.strip() and not l.startswith("---")]
                        snippet = lines[0][:160] if lines else ""
                
                normalized.append({
                    "uri": rel_u,
                    "score": score,
                    "snippet": snippet
                })
            
            if normalized:
                return json.dumps(normalized[:limit], ensure_ascii=False)
            return json.dumps([], ensure_ascii=False)
        except Exception as e:
            print(f"[warning] OpenViking find gagal ({e}), menggunakan fallback pencarian lokal...")
            return LocalBackend(self.settings).find(query=query, limit=limit)

    def read(self, uri: str) -> str:
        target = self._uri(uri)
        try:
            out = self.client.read(uri=target)
            if out:
                return self._dump(out)
        except Exception:
            pass

        # OpenViking menyimpan resource file dalam sub-direktori dengan nama stem
        # Contoh: kp-ta/panduan-kp.md disimpan di .../kp-ta/panduan-kp/panduan-kp.md
        if target.endswith(".md"):
            stem = target[:-3]
            filename = target.split("/")[-1]
            try:
                out = self.client.read(uri=f"{stem}/{filename}")
                if out:
                    return self._dump(out)
            except Exception:
                pass

        # Fallback ke pembacaan vault lokal jika tidak ditemukan di OpenViking
        try:
            clean_path = uri.replace(f"{self.root}/", "") if uri.startswith(self.root) else uri
            return LocalBackend(self.settings).read(clean_path)
        except Exception as e:
            return f"ERROR read({uri}): {e}"

    def ls(self, uri: str = "") -> str:
        try:
            raw = self.client.ls(uri=self._uri(uri) if uri else self.root)
            if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "name" in raw[0]:
                entries = []
                rel_base = _safe_rel(uri) if uri else ""
                local_dir = self.settings.vault_dir / rel_base if self.settings.vault_dir.is_dir() else None
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name", "")
                    is_dir = bool(item.get("isDir"))
                    # Rekonsiliasi: Jika file ada di disk lokal sebagai {name}.md tapi OpenViking melabelinya isDir=True
                    if local_dir and is_dir:
                        if (local_dir / f"{name}.md").is_file() and not (local_dir / name).is_dir():
                            name = f"{name}.md"
                            is_dir = False
                    entries.append(name + ("/" if is_dir else ""))
                return json.dumps(sorted(entries), ensure_ascii=False)
            return self._dump(raw)
        except Exception as e:
            print(f"[warning] OpenViking ls gagal ({e}), menggunakan fallback lokal...")
            return LocalBackend(self.settings).ls(uri=uri)


def make_backend(settings: Settings) -> Backend:
    if settings.backend == "local":
        return LocalBackend(settings)
    return VikingBackend(settings)
