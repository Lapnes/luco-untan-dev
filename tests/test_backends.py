import json
from unittest.mock import MagicMock, patch
import pytest

from luco.backends import LocalBackend, VikingBackend
from luco.config import Settings


def test_viking_backend_initialization_and_methods():
    settings = Settings(
        viking_url="http://127.0.0.1:1933",
        viking_root="viking://resources/luco",
    )

    with patch("openviking_sdk.SyncHTTPClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.initialize = MagicMock()
        mock_client.find = MagicMock(return_value={
            "resources": [{"uri": "viking://resources/luco/akademik/kurikulum/2026/tahap-pembelajaran.md", "score": 0.92, "abstract": "Kurikulum 2026"}]
        })
        mock_client.read = MagicMock(return_value="# Kurikulum 2026")
        mock_client.ls = MagicMock(return_value=[{"name": "profil", "isDir": True}, {"name": "akademik", "isDir": True}])

        vb = VikingBackend(settings)
        mock_client.initialize.assert_called_once()

        # 1. Test find
        find_res = json.loads(vb.find("kurikulum 2026"))
        assert len(find_res) == 1
        assert "tahap-pembelajaran" in find_res[0]["uri"]

        # 2. Test read
        read_res = vb.read("akademik/kurikulum/2026/tahap-pembelajaran.md")
        assert "Kurikulum 2026" in read_res
        mock_client.read.assert_called_with(uri="viking://resources/luco/akademik/kurikulum/2026/tahap-pembelajaran.md")

        # 3. Test ls
        ls_res = json.loads(vb.ls(""))
        assert "profil/" in ls_res
        mock_client.ls.assert_called_with(uri="viking://resources/luco")


def test_viking_backend_graceful_init_failure():
    settings = Settings(viking_url="http://127.0.0.1:1933")

    with patch("openviking_sdk.SyncHTTPClient") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.initialize.side_effect = ConnectionRefusedError("OpenViking container still booting")

        # Inisialisasi tidak boleh crash (tidak melempar exception ke pemanggil)
        vb = VikingBackend(settings)
        assert vb.root == settings.viking_root


def test_local_backend_stopword_and_title_boost(tmp_path):
    # Buat dua dokumen uji: satu pendek dengan kata kunci di judul, satu panjang mengulang kata umum
    doc1 = tmp_path / "visi-misi.md"
    doc1.write_text("# Visi dan Misi Informatika\nMenjadi program studi unggul.", encoding="utf-8")

    doc2 = tmp_path / "tabel-umum.md"
    doc2.write_text("# Halaman Lain\nInformatika " * 50, encoding="utf-8")

    b = LocalBackend(Settings(vault_dir=tmp_path))
    hits = json.loads(b.find("apa visi dan misi informatika"))
    assert len(hits) >= 1
    # Berkas visi-misi.md harus menduduki peringkat #1 berkat bobot judul & stopword filtering
    assert hits[0]["uri"] == "visi-misi.md"

