import os
import pytest
from fastapi.testclient import TestClient

import main
from main import (
    app,
    bagi_subnet,
    hitung_subnet,
    parse_netmask,
    prefix_default,
)

client = TestClient(app, raise_server_exceptions=False)


def _get(path):
    return client.get(path)


# --- parse_netmask ---
@pytest.mark.parametrize("teks,expected", [
    ("24", 24),
    ("/24", 24),
    ("255.255.255.0", 24),
    ("0.0.0.255", 24),
    ("0.0.0.0", 0),
    ("255.255.255.255", 32),
    ("/8", 8),
    ("255.0.0.0", 8),
])
def test_parse_netmask_valid(teks, expected):
    assert parse_netmask(teks) == expected


@pytest.mark.parametrize("teks", [
    "255.0.255.0",
    "33",
    "-1",
    "abc",
    "/33",
    "256.0.0.0",
])
def test_parse_netmask_invalid(teks):
    with pytest.raises(ValueError):
        parse_netmask(teks)


# --- prefix_default ---
@pytest.mark.parametrize("ip,expected", [
    ("192.168.0.1", 24),
    ("10.1.2.3", 8),
    ("172.16.0.1", 16),
])
def test_prefix_default(ip, expected):
    assert prefix_default(ip) == expected


@pytest.mark.parametrize("ip", ["224.0.0.1", "240.0.0.1", "239.255.255.255"])
def test_prefix_default_kelas_de(ip):
    with pytest.raises(ValueError):
        prefix_default(ip)


# --- hitung_subnet ---
def test_hitung_subnet_25():
    h = hitung_subnet("172.16.5.130", 25)
    assert h["network"] == "172.16.5.128"
    assert h["broadcast"] == "172.16.5.255"
    assert h["usable_hosts"] == 126
    assert h["mask"] == "255.255.255.128"
    assert h["wildcard"] == "0.0.0.127"
    assert h["first_host"] == "172.16.5.129"
    assert h["last_host"] == "172.16.5.254"
    assert h["prefix"] == 25
    assert h["kelas"] == "B"


def test_hitung_subnet_30():
    h = hitung_subnet("10.0.0.0", 30)
    assert h["network"] == "10.0.0.0"
    assert h["broadcast"] == "10.0.0.3"
    assert h["first_host"] == "10.0.0.1"
    assert h["last_host"] == "10.0.0.2"
    assert h["usable_hosts"] == 2


def test_hitung_subnet_31():
    h = hitung_subnet("192.168.1.0", 31)
    assert h["usable_hosts"] == 2
    assert h["broadcast"] is None
    assert h["network"] == "192.168.1.0"
    assert h["first_host"] in ("192.168.1.0", "192.168.1.1")
    assert h["last_host"] in ("192.168.1.0", "192.168.1.1")


def test_hitung_subnet_32():
    h = hitung_subnet("192.168.1.5", 32)
    assert h["usable_hosts"] == 1
    assert h["broadcast"] is None
    assert h["first_host"] == "192.168.1.5"
    assert h["last_host"] == "192.168.1.5"
    assert h["network"] == "192.168.1.5"


def test_hitung_subnet_8():
    h = hitung_subnet("10.0.0.0", 8)
    assert h["usable_hosts"] == 16777214


def test_hitung_subnet_0():
    h = hitung_subnet("0.0.0.0", 0)
    assert h["usable_hosts"] == 4294967294
    assert h["network"] == "0.0.0.0"
    assert h["broadcast"] == "255.255.255.255"


def test_hitung_subnet_kunci_wajib():
    h = hitung_subnet("192.168.0.1", 24)
    for k in ("mask", "network", "broadcast", "first_host", "last_host", "usable_hosts"):
        assert k in h
    for k in ("prefix", "wildcard", "kelas", "jenis", "total_alamat", "biner"):
        assert k in h
    for bk in ("ip", "mask", "wildcard", "network", "broadcast", "first_host", "last_host"):
        assert bk in h["biner"]


@pytest.mark.parametrize("ip,kelas,jenis_sub", [
    ("192.168.0.1", "C", "Private Internet"),
    ("10.1.2.3", "A", "Private Internet"),
    ("172.16.0.1", "B", "Private Internet"),
    ("127.0.0.1", "A", "Loopback"),
    ("169.254.1.1", "B", "Link-local"),
    ("100.64.0.1", "A", "CGNAT"),
    ("224.0.0.1", "D", "Multicast"),
    ("8.8.8.8", "A", "Publik"),
])
def test_hitung_subnet_kelas_jenis(ip, kelas, jenis_sub):
    h = hitung_subnet(ip, prefix_default(ip) if kelas in ("A", "B", "C") else 24)
    assert h["kelas"] == kelas
    assert jenis_sub in h["jenis"]


# --- validasi input ---
@pytest.mark.parametrize("ip,prefix", [
    ("256.1.1.1", 24),
    ("192.168.01.1", 24),
    ("192.168.1", 24),
    ("abc", 24),
    ("", 24),
    ("192.168.1.1", 33),
    ("192.168.1.1", -1),
])
def test_hitung_subnet_invalid(ip, prefix):
    with pytest.raises(ValueError):
        hitung_subnet(ip, prefix)


# --- bagi_subnet ---
def test_bagi_subnet_24_ke_26():
    r = bagi_subnet("192.168.0.1", 24, 26)
    assert r["mode"] == "subnet"
    assert r["jumlah_subnet"] == 4
    assert r["host_per_subnet"] == 62
    assert len(r["subnet"]) == 4
    nets = [s["network_cidr"] for s in r["subnet"]]
    assert "192.168.0.0/26" in nets
    assert "192.168.0.64/26" in nets
    assert "192.168.0.128/26" in nets
    assert "192.168.0.192/26" in nets


def test_supernet_24_ke_22():
    r = bagi_subnet("192.168.5.1", 24, 22)
    assert r["mode"] == "supernet"
    assert r["network"] == "192.168.4.0"
    assert r["broadcast"] == "192.168.7.255"
    assert r["usable_hosts"] == 1022
    assert r["jumlah_jaringan_digabung"] == 4


# --- API ---
def test_api_subnet_valid():
    r = _get("/api/subnet?ip=172.16.5.130&prefix=25")
    assert r.status_code == 200
    d = r.json()
    assert d["network"] == "172.16.5.128"
    assert d["broadcast"] == "172.16.5.255"
    assert d["usable_hosts"] == 126


def test_api_subnet_invalid():
    r = _get("/api/subnet?ip=256.1.1.1&prefix=24")
    assert r.status_code == 400


def test_api_subnet_bad_prefix():
    r = _get("/api/subnet?ip=192.168.1.1&prefix=abc")
    assert r.status_code == 400


def test_api_ipcalc_basic():
    r = _get("/api/ipcalc?address=172.16.5.130/25")
    assert r.status_code == 200
    d = r.json()
    assert "hasil" in d
    assert d["hasil"]["network"] == "172.16.5.128"


def test_api_ipcalc_pembagian():
    r = _get("/api/ipcalc?address=192.168.0.1/24&netmask2=/26")
    assert r.status_code == 200
    d = r.json()
    assert d["pembagian"] is not None
    assert d["pembagian"]["jumlah_subnet"] == 4


def test_api_ipcalc_default_mask():
    r = _get("/api/ipcalc?address=192.168.0.1")
    assert r.status_code == 200
    d = r.json()
    assert d["hasil"]["prefix"] == 24
    assert "Private Internet" in d["hasil"]["jenis"]


def test_api_ipcalc_konflik_prefix():
    r = _get("/api/ipcalc?address=192.168.1.1/24&netmask=/25")
    assert r.status_code == 400


def test_get_root():
    r = _get("/")
    assert r.status_code == 200
    assert "html" in r.text.lower()


def test_dev_versi_tanpa_env():
    # tanpa APP_ENV=dev -> 404
    r = _get("/__dev/versi")
    assert r.status_code == 404


def test_dev_versi_dengan_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    r = _get("/__dev/versi")
    assert r.status_code == 200
    assert "versi" in r.json()

# --- tambahan untuk coverage ---

def test_ping():
    r = _get("/api/ping")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_parse_netmask_none_empty():
    with pytest.raises(ValueError):
        parse_netmask(None)
    with pytest.raises(ValueError):
        parse_netmask("")
    with pytest.raises(ValueError):
        parse_netmask("   ")


def test_parse_netmask_dotted_invalid():
    with pytest.raises(ValueError):
        parse_netmask("255.255.255.256")
    with pytest.raises(ValueError):
        parse_netmask("abc.def.gha.jkl")


def test_ip_validation_variants():
    with pytest.raises(ValueError):
        hitung_subnet(None, 24)
    with pytest.raises(ValueError):
        hitung_subnet(" 1.2.3.4", 24)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4 ", 24)
    with pytest.raises(ValueError):
        hitung_subnet("1..3.4", 24)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4.5", 24)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.a", 24)


def test_prefix_validation():
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", "abc")
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", "")
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", 1.5)


def test_bagi_subnet_limit_offset():
    r = bagi_subnet("192.168.0.1", 24, 26, offset=1, limit=2)
    assert r["offset"] == 1
    assert r["limit"] == 2
    assert len(r["subnet"]) == 2
    assert r["subnet"][0]["nomor"] == 2
    assert r["terpotong"] is True
    r2 = bagi_subnet("192.168.0.1", 24, 26, offset=0, limit=5000)
    assert r2["limit"] == 1024


def test_bagi_subnet_errors():
    with pytest.raises(ValueError):
        bagi_subnet("192.168.0.1", 24, 26, offset=-1)
    with pytest.raises(ValueError):
        bagi_subnet("192.168.0.1", 24, 26, limit=-1)
    with pytest.raises(ValueError):
        bagi_subnet("192.168.0.1", 24, 26, offset="x")


def test_api_ipcalc_with_netmask_param():
    r = _get("/api/ipcalc?address=192.168.0.1&netmask=255.255.255.0")
    assert r.status_code == 200
    assert r.json()["hasil"]["prefix"] == 24


def test_api_ipcalc_invalid_address():
    r = _get("/api/ipcalc?address=")
    assert r.status_code == 400
    r = _get("/api/ipcalc?address=192.168.1.1/24/25")
    assert r.status_code == 400


def test_api_ipcalc_supernet():
    r = _get("/api/ipcalc?address=192.168.5.1/24&netmask2=/22")
    assert r.status_code == 200
    d = r.json()
    assert d["pembagian"]["mode"] == "supernet"
    assert d["pembagian"]["network"] == "192.168.4.0"


# --- VLSM ---

def test_alokasi_vlsm_basic():
    from main import alokasi_vlsm
    hasil = alokasi_vlsm("192.168.1.0/24", [100, 50, 20, 2])
    assert [h["network_cidr"] for h in hasil] == [
        "192.168.1.0/25",
        "192.168.1.128/26",
        "192.168.1.192/27",
        "192.168.1.224/30",
    ]
    assert hasil[0]["kebutuhan"] == 100


def test_alokasi_vlsm_unordered():
    from main import alokasi_vlsm
    hasil = alokasi_vlsm("192.168.1.0/24", [2, 100, 20, 50])
    assert [h["network_cidr"] for h in hasil] == [
        "192.168.1.0/25",
        "192.168.1.128/26",
        "192.168.1.192/27",
        "192.168.1.224/30",
    ]


def test_alokasi_vlsm_tidak_muat():
    from main import alokasi_vlsm
    with pytest.raises(ValueError):
        alokasi_vlsm("192.168.1.0/24", [200, 100])


def test_alokasi_vlsm_bukan_network():
    from main import alokasi_vlsm
    with pytest.raises(ValueError):
        alokasi_vlsm("192.168.1.5/24", [10])


def test_alokasi_vlsm_minimal_dan_invalid():
    from main import alokasi_vlsm
    hasil = alokasi_vlsm("192.168.1.0/24", [1])
    assert hasil[0]["network_cidr"] == "192.168.1.0/30"
    with pytest.raises(ValueError):
        alokasi_vlsm("192.168.1.0/24", [])
    with pytest.raises(ValueError):
        alokasi_vlsm("192.168.1.0/24", [0])
    with pytest.raises(ValueError):
        alokasi_vlsm("192.168.1.0/24", [-1])


def test_api_vlsm_ok():
    r = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [100, 50, 20, 2]})
    assert r.status_code == 200
    hasil = r.json()
    assert isinstance(hasil, list)
    assert [b["network_cidr"] for b in hasil] == [
        "192.168.1.0/25",
        "192.168.1.128/26",
        "192.168.1.192/27",
        "192.168.1.224/30",
    ]


def test_api_vlsm_bad_body():
    r = client.post("/api/vlsm", content="notjson", headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    r = client.post("/api/vlsm", json=[1,2,3])
    assert r.status_code == 400
    r = client.post("/api/vlsm", json={"network": 123, "kebutuhan_host": [10]})
    assert r.status_code == 400
    r = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": "x"})
    assert r.status_code == 400


def test_parse_netmask_slash_zero():
    assert parse_netmask("/0") == 0
    assert parse_netmask("0") == 0


def test_hitung_jenis_others():
    assert "Jaringan ini" in hitung_subnet("0.0.0.1", 8)["jenis"]
    assert "Broadcast terbatas" in hitung_subnet("255.255.255.255", 32)["jenis"]
    assert "Dicadangkan" in hitung_subnet("240.0.0.1", 4)["jenis"]
    assert "Dokumentasi" in hitung_subnet("192.0.2.1", 24)["jenis"]

# --- coverage tambahan ---

def test_validation_internal_branches():
    with pytest.raises(ValueError):
        hitung_subnet(123, 24)
    with pytest.raises(ValueError):
        parse_netmask(123)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", True)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", 1.0)
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", "  ")
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", "1.2")
    with pytest.raises(ValueError):
        hitung_subnet("1.2.3.4", None)


def test_validation_handler_422():
    # trigger RequestValidationError -> 422->400 handler (missing required query)
    r = client.get("/api/subnet")
    assert r.status_code == 400


def test_api_vlsm_network_not_str():
    r = client.post("/api/vlsm", json={"network": None, "kebutuhan_host": [10]})
    assert r.status_code == 400


def test_parse_address_edge_cases():
    # address with spaces around not allowed by our check
    r = _get("/api/ipcalc?address= 192.168.1.1/24")
    assert r.status_code == 400
    # malformed / 
    r = _get("/api/ipcalc?address=192.168.1.1/")
    assert r.status_code == 400
    r = _get("/api/ipcalc?address=/24")
    assert r.status_code == 400


def test_more_coverage_branches():
    # parse_netmask string non-numeric non-dotted
    with pytest.raises(ValueError):
        parse_netmask("abc")
    # leading/trailing spaces in netmask token handled? parse_netmask strips
    assert parse_netmask(" /24 ") == 24
    # address internal space caught in ipcalc
    r = _get("/api/ipcalc?address=192.168.1.1 /24")
    assert r.status_code == 400
    # prefix param edge via api subnet
    r = _get("/api/subnet?ip=1.2.3.4&prefix= 24 ")
    assert r.status_code == 200
    # ipcalc with explicit netmask different form same value ok
    r = _get("/api/ipcalc?address=10.0.0.1&netmask=/8")
    assert r.status_code == 200 and r.json()["hasil"]["prefix"] == 8
    # bagi_subnet invalid limit type
    with pytest.raises(ValueError):
        bagi_subnet("1.2.3.4",24,26,limit="x")
    # address with prefix in right containing dot
    r = _get("/api/ipcalc?address=10.0.0.1/255.0.0.0")
    assert r.status_code == 200 and r.json()["hasil"]["prefix"] == 8
