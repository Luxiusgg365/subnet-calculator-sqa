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
