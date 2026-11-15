"""Pengujian integrasi langsung (live) ke container OpenViking di port :1933.

Tes ini memastikan bahwa:
1. Layanan OpenViking di Docker aktif dan sehat (healthcheck ok).
2. Struktur URI direktori vault dapat dinavigasi (ls).
3. Pencarian semantik (find) mengembalikan format normalisasi (uri, score, snippet).
4. Dokumen (read) dapat dibaca tanpa error.
"""
from __future__ import annotations

import json
import httpx
import pytest

from luco.backends import VikingBackend
from luco.config import get_settings


def is_openviking_live() -> bool:
    """Cek apakah kontainer OpenViking sedang menyala di port 1933."""
    try:
        r = httpx.get("http://127.0.0.1:1933/health", timeout=1.5)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_openviking_live(),
    reason="Kontainer OpenViking tidak aktif di http://127.0.0.1:1933. Jalankan 'pixi run up:deps'.",
)


def test_viking_live_health_endpoint():
    r = httpx.get("http://127.0.0.1:1933/health", timeout=2.0)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("healthy") is True


def test_viking_live_ls_vault_categories():
    settings = get_settings()
    backend = VikingBackend(settings)
    ls_raw = backend.ls("")
    categories = json.loads(ls_raw)

    assert isinstance(categories, list)
    # Harus mencakup folder-folder utama vault prodi
    expected_categories = {"akademik/", "dosen/", "fasilitas-lab/", "kemahasiswaan/", "kp-ta/", "profil/"}
    found = set(categories)
    assert expected_categories.issubset(found), f"Kategori yang hilang: {expected_categories - found}"


def test_viking_live_find_normalization():
    settings = get_settings()
    backend = VikingBackend(settings)
    res_raw = backend.find("kurikulum 2026", limit=3)
    results = json.loads(res_raw)

    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    assert "uri" in first
    assert "score" in first
    assert "snippet" in first
    assert isinstance(first["score"], float)
    # URI tidak boleh mengandung prefix mentah viking://
    assert not first["uri"].startswith("viking://")


def test_viking_live_read_document():
    settings = get_settings()
    backend = VikingBackend(settings)
    content = backend.read("kp-ta/panduan-kp.md")
    assert not content.startswith("ERROR")
    assert "Kerja Praktik" in content or "KP" in content

