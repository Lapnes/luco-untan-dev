from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from llama_index.core.tools import FunctionTool

from .backends import Backend
from .config import Settings
from .lookup import load_lookup, lookup_records

MAX_READ_CHARS = 12000


@dataclass
class Recorder:
    """Merekam setiap panggilan tool untuk log trajectory, audit telemetri, dan pengecekan sitasi."""

    calls: list[dict] = field(default_factory=list)

    def add(
        self,
        tool: str,
        args: dict,
        output: str,
        duration_ms: float = 0.0,
        t_start: float = 0.0,
        t_end: float = 0.0,
        files_accessed: list[str] | None = None,
        lines_accessed: str = "-",
    ) -> None:
        idx = len(self.calls) + 1
        summary = output[:200] + "..." if len(output) > 200 else output
        self.calls.append({
            "call_index": idx,
            "tool": tool,
            "args": args,
            "output_chars": len(output),
            "duration_ms": round(duration_ms, 2),
            "t_start": t_start,
            "t_end": t_end,
            "files_accessed": files_accessed or [],
            "lines_accessed": lines_accessed,
            "output_summary": summary,
            "_output": output,
        })

    @property
    def outputs(self) -> list[str]:
        return [c["_output"] for c in self.calls]

    def trace(self) -> list[dict]:
        """Format trajectory yang bersih dan informatif untuk audit dan UI."""
        res = []
        for c in self.calls:
            item = {k: v for k, v in c.items() if k != "_output"}
            # Sertakan cuplikan output atau teks output aman
            item["output"] = c["_output"][:3000] if len(c["_output"]) > 3000 else c["_output"]
            res.append(item)
        return res


def make_tools(
    backend: Backend,
    settings: Settings,
    rec: Recorder,
    user_id: str | None = None,
    current_session_id: str | None = None,
) -> list[FunctionTool]:
    """Menyiapkan 4 alat RAG inti Prodi Informatika UNTAN dengan telemetri presisi tinggi."""
    records = load_lookup(settings)

    def cari_profil_dosen(query: str) -> str:
        """Cari data dosen yang tepat (nama, NIP, email, jabatan, kelompok keahlian, file profil) dari tabel lookup. Utamakan tool ini untuk NIP/email/jabatan."""
        t_start = time.time()
        matches = lookup_records(records, query)
        out = json.dumps(matches, ensure_ascii=False)
        t_end = time.time()
        duration_ms = (t_end - t_start) * 1000

        files = [m.get("file") for m in matches if m.get("file")]
        if not files:
            files = ["vault/lookup.json"]
        lines = f"{len(matches)} entri profil terdeteksi"

        rec.add(
            tool="cari_profil_dosen",
            args={"query": query},
            output=out,
            duration_ms=duration_ms,
            t_start=t_start,
            t_end=t_end,
            files_accessed=files,
            lines_accessed=lines,
        )
        return out

    def telusuri_direktori_prodi(query: str) -> str:
        """Cari dokumen prodi (KP, TA, kurikulum, dosen, dll.) berdasarkan pertanyaan. Mengembalikan daftar kandidat (uri, ringkasan, skor)."""
        t_start = time.time()
        out = backend.find(query)
        t_end = time.time()
        duration_ms = (t_end - t_start) * 1000

        # Ekstraksi berkas/URI yang ditemukan di hasil penelusuran
        found_files = list(dict.fromkeys(re.findall(r"(?:vault/|kp-ta/|akademik/|dosen/|dokumen/|profil/)[^\s\)\],]+", out)))
        if not found_files:
            found_files = ["vault/manifest.json"]
        lines = f"{len(found_files)} kandidat berkas relevan"

        rec.add(
            tool="telusuri_direktori_prodi",
            args={"query": query},
            output=out,
            duration_ms=duration_ms,
            t_start=t_start,
            t_end=t_end,
            files_accessed=found_files,
            lines_accessed=lines,
        )
        return out

    def baca_dokumen_lengkap(path: str) -> str:
        """Baca isi lengkap sebuah dokumen. `path` boleh berupa URI hasil pencarian atau path relatif dari tautan Markdown (mis. dosen/nama.md)."""
        t_start = time.time()
        try:
            out = backend.read(path)
        except Exception as e:  # noqa: BLE001
            out = f"ERROR: {e}"
        if len(out) > MAX_READ_CHARS:
            out = out[:MAX_READ_CHARS] + "\n...[dipotong]"
        t_end = time.time()
        duration_ms = (t_end - t_start) * 1000

        line_count = len(out.splitlines())
        lines = f"Baris 1 - {line_count}"

        rec.add(
            tool="baca_dokumen_lengkap",
            args={"path": path},
            output=out,
            duration_ms=duration_ms,
            t_start=t_start,
            t_end=t_end,
            files_accessed=[path],
            lines_accessed=lines,
        )
        return out

    def list_docs(path: str = "") -> str:
        """Lihat isi folder (mis. 'dosen' atau '' untuk root). Berguna untuk menemukan halaman indeks."""
        t_start = time.time()
        try:
            out = backend.ls(path)
        except Exception as e:  # noqa: BLE001
            out = f"ERROR: {e}"
        t_end = time.time()
        duration_ms = (t_end - t_start) * 1000

        line_count = len(out.splitlines())
        lines = f"Direktori: {line_count} baris berkas"

        rec.add(
            tool="list_docs",
            args={"path": path},
            output=out,
            duration_ms=duration_ms,
            t_start=t_start,
            t_end=t_end,
            files_accessed=[path or "root/"],
            lines_accessed=lines,
        )
        return out

    # Aliases untuk kompatibilitas
    find_docs = telusuri_direktori_prodi
    read_doc = baca_dokumen_lengkap
    lookup_dosen = cari_profil_dosen

    return [
        FunctionTool.from_defaults(fn=cari_profil_dosen),
        FunctionTool.from_defaults(fn=telusuri_direktori_prodi),
        FunctionTool.from_defaults(fn=baca_dokumen_lengkap),
        FunctionTool.from_defaults(fn=list_docs),
    ]
