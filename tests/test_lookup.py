import pytest
from luco.config import Settings
from luco.lookup import load_lookup, lookup_records


@pytest.fixture
def real_records():
    return load_lookup(Settings())


def test_lookup_loads_all_33_lecturers(real_records):
    assert len(real_records) == 33
    # Pastikan setiap dosen memiliki nama dan NIP yang valid
    for r in real_records:
        assert r.get("nama")
        assert r.get("nip") and len(str(r["nip"])) == 18
        assert "@" in r.get("email", "")
        assert r.get("file")


def test_lookup_by_exact_name(real_records):
    res = lookup_records(real_records, "Herry Sujaini")
    assert len(res) >= 1
    assert "Herry Sujaini" in res[0]["nama"]
    assert res[0]["nip"] == "196806291997021001"


def test_lookup_by_honorifics_and_titles(real_records):
    # Mahasiswa sering mengetik "Pak Herry", "Prof Herry", atau "Dr. Arif"
    res1 = lookup_records(real_records, "Pak Herry")
    assert any("Herry Sujaini" in r["nama"] for r in res1)

    res2 = lookup_records(real_records, "Prof. Herry")
    assert any("Herry Sujaini" in r["nama"] for r in res2)

    res3 = lookup_records(real_records, "Dr. Arif")
    assert any("Arif Bijaksana" in r["nama"] for r in res3)


def test_lookup_by_nip(real_records):
    res = lookup_records(real_records, "196806291997021001")
    assert len(res) == 1
    assert "Herry Sujaini" in res[0]["nama"]


def test_lookup_by_email(real_records):
    res = lookup_records(real_records, "fianjld@informatika.untan.ac.id")
    assert len(res) == 1
    assert "Alfian Abdul Jalid" in res[0]["nama"]


def test_lookup_by_kbk(real_records):
    # Pencarian berdasarkan Kelompok Bidang Keahlian
    ai_dosen = lookup_records(real_records, "Computation & Artificial Intelligence", limit=20)
    assert len(ai_dosen) == 8

    se_dosen = lookup_records(real_records, "Software Engineering & Mobile Computing", limit=20)
    assert len(se_dosen) == 7

    net_dosen = lookup_records(real_records, "Networking & Security", limit=20)
    assert len(net_dosen) == 6

    si_dosen = lookup_records(real_records, "Information System & Data Spatial", limit=20)
    assert len(si_dosen) == 8


def test_lookup_by_openalex_id(real_records):
    res = lookup_records(real_records, "A5071117671")
    assert len(res) == 1
    assert "Herry Sujaini" in res[0]["nama"]


def test_lookup_by_lecturer_aliases(real_records):
    # Mahasiswa sering memanggil dosen dengan nama panggilan / alias akrab
    edo_res = lookup_records(real_records, "Pak Edo")
    assert any("Izuardo Zulkarnain" in r["nama"] for r in edo_res)

    teza_res = lookup_records(real_records, "Pak Teza")
    assert any("Morteza Muthahhari" in r["nama"] for r in teza_res)

    tz_res = lookup_records(real_records, "Pak Tz")
    assert any("Morteza Muthahhari" in r["nama"] for r in tz_res)

    tur_res = lookup_records(real_records, "Bu Tur")
    assert any("Tursina" in r["nama"] for r in tur_res)

    ulum_res = lookup_records(real_records, "Bu Ulum")
    assert any("Desepta Isna Ulumi" in r["nama"] for r in ulum_res)

    riki_res = lookup_records(real_records, "Pak Riki")
    assert any("Rickhy Artha Octaviyana" in r["nama"] for r in riki_res)

    fian_res = lookup_records(real_records, "Pak Fian")
    assert any("Alfian Abdul Jalid" in r["nama"] for r in fian_res)


def test_lookup_empty_or_unknown(real_records):
    assert lookup_records(real_records, "") == []
    assert lookup_records(real_records, "   ") == []
    assert lookup_records(real_records, "Nama Dosen Fiktif Tidak Ada") == []

