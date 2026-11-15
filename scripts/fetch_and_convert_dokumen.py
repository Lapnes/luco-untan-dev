"""Download dan konversi seluruh 26 berkas resmi Informatika UNTAN ke Markdown (.md).

Menggunakan PyMuPDF4LLM untuk berkas PDF dan Mammoth untuk berkas DOCX.
Menyimpan berkas mentah asli ke data/dokumen_raw/ dan hasil Markdown ke vault/dokumen/.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import re
import sys
import time

import httpx
import mammoth
import pymupdf
import pymupdf4llm

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "dokumen_raw"
VAULT_DOKUMEN_DIR = ROOT_DIR / "vault" / "dokumen"

API_URL = "https://api.ifuntanhub.dev/items/berkas?limit=100"
ASSET_BASE_URL = "https://api.ifuntanhub.dev/assets"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def detect_file_type(content: bytes, filename: str) -> str:
    if content.startswith(b"%PDF") or filename.lower().endswith(".pdf"):
        return "pdf"
    if content.startswith(b"PK") or filename.lower().endswith(".docx"):
        return "docx"
    return "unknown"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    VAULT_DOKUMEN_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Menghubungi Directus API: {API_URL}")
    with httpx.Client(timeout=60.0) as client:
        resp = client.get(API_URL)
        if resp.status_code != 200:
            print(f"ERROR: API returned status {resp.status_code}")
            sys.exit(1)

        items = resp.json().get("data", [])
        published = [it for it in items if it.get("status") == "published" and it.get("file")]
        print(f"Ditemukan {len(published)} berkas berstatus published.\n")

        manifest_docs = []

        for idx, item in enumerate(published, 1):
            doc_id = item.get("id")
            nama_berkas = item.get("nama_berkas", f"dokumen_{doc_id}").strip()
            file_id = item.get("file")
            tgl = item.get("tanggal_upload", "")[:10]
            download_url = f"{ASSET_BASE_URL}/{file_id}"

            print(f"[{idx}/{len(published)}] Mengunduh: {nama_berkas} ({file_id})")
            file_resp = client.get(download_url)
            if file_resp.status_code != 200:
                print(f"  FAILED to download ({file_resp.status_code})")
                continue

            content = file_resp.content

            # Ekstrak filename dari header Content-Disposition bila ada
            cd = file_resp.headers.get("Content-Disposition", "")
            raw_filename = ""
            if "filename=" in cd:
                match = re.search(r'filename="?([^";]+)"?', cd)
                if match:
                    raw_filename = match.group(1).strip()

            ftype = detect_file_type(content, raw_filename)
            if not raw_filename:
                raw_filename = f"{slugify(nama_berkas)}.{ftype}"

            # Simpan file biner asli ke data/dokumen_raw/
            safe_raw_name = f"{idx:02d}_{re.sub(r'[^a-zA-Z0-9._-]', '_', raw_filename)}"
            raw_path = RAW_DIR / safe_raw_name
            raw_path.write_bytes(content)

            # Konversi ke Markdown
            t0 = time.time()
            md_body = ""
            if ftype == "pdf":
                try:
                    doc = pymupdf.open(stream=content, filetype="pdf")
                    md_body = pymupdf4llm.to_markdown(doc)
                except Exception as e:
                    md_body = f"*Gagal mengekstrak teks PDF secara otomatis: {e}*\n"
            elif ftype == "docx":
                try:
                    result = mammoth.convert_to_markdown(io.BytesIO(content))
                    md_body = result.value
                except Exception as e:
                    md_body = f"*Gagal mengekstrak dokumen Word secara otomatis: {e}*\n"
            else:
                md_body = "*Format berkas tidak didukung untuk ekstraksi Markdown.*"

            dur = round(time.time() - t0, 2)

            # Susun berkas Markdown dengan Frontmatter
            slug = f"{idx:02d}-{slugify(nama_berkas)}"
            md_filename = f"{slug}.md"
            md_file_path = VAULT_DOKUMEN_DIR / md_filename

            fm_title = nama_berkas.replace('"', '\\"')
            frontmatter = f"""---
tipe: dokumen_resmi
id: {doc_id}
judul: "{fm_title}"
berkas_asli: "data/dokumen_raw/{safe_raw_name}"
url_asli: "{download_url}"
format: "{ftype.upper()}"
ukuran_byte: {len(content)}
tanggal_upload: "{tgl}"
sumber: "{download_url}"
---

# {nama_berkas}

> **Informasi Berkas Resmi:**
> - **Format Asli:** {ftype.upper()} ({len(content):,} bytes)
> - **Tautan Unduh Berkas Asli (Raw):** [{raw_filename}]({download_url})
> - **Tanggal Terbit:** {tgl}

---

{md_body.strip()}
"""
            md_file_path.write_text(frontmatter, encoding="utf-8")
            print(f"  -> Tersimpan: {md_filename} ({len(md_body):,} karakter, {dur}s)")

            manifest_docs.append({
                "no": idx,
                "id": doc_id,
                "nama": nama_berkas,
                "format": ftype.upper(),
                "ukuran": f"{len(content):,} bytes",
                "tanggal": tgl,
                "md_path": f"dokumen/{md_filename}",
                "raw_path": f"data/dokumen_raw/{safe_raw_name}",
                "raw_url": download_url,
                "raw_filename": raw_filename,
            })

        # Buat halaman indeks vault/dokumen/README.md
        index_lines = [
            "# Katalog Berkas Resmi & Dokumen Akademik Informatika UNTAN",
            "",
            "Katalog seluruh dokumen resmi Program Studi S1 Informatika FT UNTAN hasil ekstraksi `PyMuPDF4LLM` & `Mammoth`.",
            "Tersedia pilihan untuk melihat versi naskah terformat Markdown (.md) atau mengunduh berkas biner asli (.pdf / .docx).",
            "",
            "---",
            "",
            "| No | Nama Dokumen Resmi | Format | Ukuran | Tanggal | Versi Markdown (.md) | Berkas Asli (PDF/DOCX) |",
            "| :---: | :--- | :---: | :---: | :---: | :--- | :--- |",
        ]
        for d in manifest_docs:
            index_lines.append(
                f"| {d['no']} | **{d['nama']}** | `{d['format']}` | {d['ukuran']} | {d['tanggal']} | "
                f"[Buka Naskah Markdown]({d['md_path'].replace('dokumen/', '')}) | "
                f"[Unduh {d['format']}]({d['raw_url']}) |"
            )

        index_lines.extend([
            "",
            "---",
            "",
            "## Tautan Terkait",
            "- [Template Dokumen & Panduan Tipografi](../kp-ta/template-dokumen.md)",
            "- [Panduan Tugas Akhir & Skripsi](../kp-ta/panduan-ta.md)",
            "- [Panduan Kerja Praktik](../kp-ta/panduan-kp.md)",
        ])

        (VAULT_DOKUMEN_DIR / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
        print(f"\nIndeks berhasil dibuat: vault/dokumen/README.md ({len(manifest_docs)} dokumen)")


if __name__ == "__main__":
    main()

