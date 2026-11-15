import json
from pathlib import Path
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from luco.backends import LocalBackend, _safe_rel  # noqa: E402
from luco.citations import check_citations  # noqa: E402
from luco.config import Settings  # noqa: E402
from luco.lookup import lookup_records  # noqa: E402
import build_lookup  # noqa: E402
import build_manifest  # noqa: E402
import check_links  # noqa: E402

DOSEN = """---
tipe: dosen
nama: Budi Contoh
nip: "123 456"
email: budi@example.invalid
kelompok_keahlian: [NLP, Data Science]
sumber:
  - nama: Profil
    url: https://example.invalid/budi
---
# Budi
[Indeks](index.md)
"""


def make_vault(root: Path) -> Path:
    (root / "dosen").mkdir(parents=True)
    (root / "dosen" / "budi.md").write_text(DOSEN, encoding="utf-8")
    (root / "dosen" / "index.md").write_text("# Indeks\n[Budi](budi.md)\n[Rusak](hilang.md)\n", encoding="utf-8")
    return root


def test_build_lookup_and_search():
    with tempfile.TemporaryDirectory() as d:
        v = make_vault(Path(d))
        recs = build_lookup.build(v)
        assert len(recs) == 1 and recs[0]["nip"] == "123 456"
        assert lookup_records(recs, "nlp")[0]["nama"] == "Budi Contoh"
        assert lookup_records(recs, "123 456")
        assert lookup_records(recs, "Dr. Budi")[0]["nama"] == "Budi Contoh"
        assert lookup_records(recs, "Pak Budi")[0]["nama"] == "Budi Contoh"
        assert lookup_records(recs, "tidak ada") == []


def test_check_links_finds_broken():
    with tempfile.TemporaryDirectory() as d:
        v = make_vault(Path(d))
        bad = check_links.broken_links(v)
        assert bad == [("dosen/index.md", "hilang.md")]


def test_safe_rel_blocks_escape():
    assert _safe_rel("dosen/../dosen/a.md") == "dosen/a.md"
    with pytest.raises(ValueError, match="path keluar"):
        _safe_rel("../rahasia.md")
    with pytest.raises(ValueError, match="path keluar"):
        _safe_rel("dosen/../../rahasia.md")
    with pytest.raises(ValueError, match="path keluar"):
        _safe_rel("~")
    with pytest.raises(ValueError, match="path keluar"):
        _safe_rel("~/rahasia.md")


def test_local_backend_find_read():
    with tempfile.TemporaryDirectory() as d:
        v = make_vault(Path(d))
        b = LocalBackend(Settings(vault_dir=v))
        hits = json.loads(b.find("budi nlp"))
        assert hits and hits[0]["uri"].endswith("budi.md")
        assert "Budi" in b.read("dosen/budi.md")
        assert b.read("../x").startswith("ERROR")  # path keluar vault ditolak, tidak crash


def test_citation_checker():
    tool_out = ["sumber: https://example.invalid/budi dan [Profil](https://example.invalid/budi)"]
    ok = check_citations("Cek [Profil](https://example.invalid/budi)", tool_out)
    assert ok["all_verified"]
    assert ok["has_citations"]
    assert ok["links"] == 1

    bad = check_citations("Cek [Palsu](https://karangan.invalid/x)", tool_out)
    assert not bad["all_verified"] and bad["unverified"][0]["target"].startswith("https://karangan")

    # Uji jawaban tanpa kutipan (tidak boleh dilaporkan terverifikasi)
    empty = check_citations("Jawaban ini tidak punya sitasi sama sekali.", tool_out)
    assert not empty["all_verified"]
    assert not empty["has_citations"]
    assert empty["links"] == 0


def test_build_manifest():
    with tempfile.TemporaryDirectory() as d:
        v = make_vault(Path(d))
        out_file = Path(d) / "manifest.json"
        manifest = build_manifest.build_manifest(v, out_file)

        assert manifest["total_documents"] == 2
        assert "dosen/budi.md" in manifest["documents"]
        doc = manifest["documents"]["dosen/budi.md"]
        assert doc["title"] == "Budi"
        assert len(doc["headings"]) >= 1
        assert doc["headings"][0]["level"] == 1
        assert doc["headings"][0]["line_start"] == 11
        assert out_file.is_file()
