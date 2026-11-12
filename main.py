import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "Parameter permintaan tidak valid"})


@app.get("/")
def index():
    return FileResponse(INDEX_PATH)


@app.get("/api/ping")
def ping():
    return {"ok": True}


@app.get("/__dev/versi")
def dev_versi():
    if os.getenv("APP_ENV") != "dev":
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    mtimes = []
    for name in ("main.py", "index.html"):
        p = BASE_DIR / name
        if p.exists():
            mtimes.append(p.stat().st_mtime_ns)
    return {"versi": max(mtimes) if mtimes else 0}


# ---------- util & validasi ----------

def _err(msg: str):
    raise ValueError(msg)


def _ip_to_int(ip: str) -> int:
    if ip is None:
        _err("Alamat IPv4 tidak boleh kosong")
    if not isinstance(ip, str):
        _err("Alamat IPv4 harus berupa teks")
    if ip == "":
        _err("Alamat IPv4 tidak boleh kosong")
    if ip != ip.strip() or any(c.isspace() for c in ip):
        _err("Alamat IPv4 tidak boleh mengandung spasi")
    parts = ip.split(".")
    if len(parts) != 4:
        _err("Alamat IPv4 harus terdiri dari tepat 4 oktet")
    nums = []
    for i, p in enumerate(parts, start=1):
        if p == "":
            _err(f"Oktet ke-{i} kosong; harus 0-255")
        if not re.fullmatch(r"[0-9]+", p):
            _err(f"Oktet ke-{i} mengandung karakter tidak valid; harus angka 0-255")
        if len(p) > 1 and p[0] == "0":
            _err(f"Oktet ke-{i} tidak boleh diawali nol")
        try:
            v = int(p)
        except Exception:
            _err(f"Oktet ke-{i} bukan angka yang valid")
        if v < 0 or v > 255:
            _err(f"Oktet ke-{i} bernilai {v}; harus 0-255")
        nums.append(v)
    return (nums[0] << 24) | (nums[1] << 16) | (nums[2] << 8) | nums[3]


def _int_to_ip(n: int) -> str:
    n &= 0xFFFFFFFF
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def _prefix_to_mask(prefix: int) -> int:
    if prefix == 0:
        return 0
    return (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF


def _to_bin32(n: int) -> str:
    n &= 0xFFFFFFFF
    b = f"{n:032b}"
    return ".".join(b[i:i+8] for i in range(0, 32, 8))


def _validate_prefix(prefix: Any) -> int:
    if isinstance(prefix, bool):
        _err("Prefix harus bilangan bulat 0-32")
    if isinstance(prefix, float):
        _err("Prefix harus bilangan bulat 0-32")
    if isinstance(prefix, str):
        if prefix.strip() == "":
            _err("Prefix tidak boleh kosong")
        if not re.fullmatch(r"-?[0-9]+", prefix.strip()):
            _err("Prefix harus bilangan bulat 0-32")
        prefix = int(prefix.strip())
    if not isinstance(prefix, int):
        _err("Prefix harus bilangan bulat 0-32")
    if prefix < 0 or prefix > 32:
        _err(f"Prefix {prefix} di luar rentang; harus 0-32")
    return prefix


def parse_netmask(teks: str) -> int:
    if teks is None:
        _err("Netmask tidak boleh kosong")
    if not isinstance(teks, str):
        _err("Netmask harus berupa teks")
    s = teks.strip()
    if s == "":
        _err("Netmask tidak boleh kosong")
    # CIDR /24 atau 24
    if s.startswith("/"):
        s2 = s[1:]
    else:
        s2 = s
    if re.fullmatch(r"[0-9]+", s2) and "." not in s2:
        v = int(s2)
        if v < 0 or v > 32:
            _err(f"Prefix {v} di luar rentang; harus 0-32")
        return v
    # dotted mask atau inverse
    if "." in s:
        val = _ip_to_int(s.strip())
        # cek kontigu sebagai mask normal (1s then 0s)
        inv = (~val) & 0xFFFFFFFF
        # normal contiguous: val + (lowest set block?) easier: 0*1+0+ pattern in bits
        def contiguous_mask(v):
            # v has contiguous 1s from MSB
            if v == 0:
                return True, 0
            # find trailing zeros count in 32-bit: v == (..1100..)
            # contiguous if v + (1<<tz) == 1<<32 (mod)
            tz = (v & -v).bit_length() - 1
            ones = 32 - tz
            return v == (_prefix_to_mask(ones)), ones
        ok, ones = contiguous_mask(val)
        if ok:
            # 0.0.0.0 -> /0 (keputusan default)
            return ones
        # try inverse/wildcard: contiguous 0s then 1s => inv is contiguous mask
        ok2, ones2 = contiguous_mask(inv)
        if ok2:
            # inverse: 0.0.0.255 means host bits 1 -> /24
            return ones2
        _err("Netmask tidak berkesinambungan; bit 1 harus berurutan dari kiri")
    _err("Format netmask tidak dikenali; gunakan /24, 24, 255.255.255.0, atau 0.0.0.255")


def _kelas_dari_ip_int(ip_int: int) -> str:
    first = (ip_int >> 24) & 0xFF
    if 0 <= first <= 127:
        return "A"
    if 128 <= first <= 191:
        return "B"
    if 192 <= first <= 223:
        return "C"
    if 224 <= first <= 239:
        return "D"
    return "E"


def prefix_default(ip: str) -> int:
    ip_int = _ip_to_int(ip)
    k = _kelas_dari_ip_int(ip_int)
    if k == "A":
        return 8
    if k == "B":
        return 16
    if k == "C":
        return 24
    _err("Kelas D/E tidak punya netmask default, isi netmask")


def _in_cidr(ip_int: int, net_str: str, pref: int) -> bool:
    net_int = _ip_to_int(net_str)
    mask = _prefix_to_mask(pref)
    return (ip_int & mask) == (net_int & mask)


def _jenis_alamat(ip_str: str, ip_int: int) -> str:
    if ip_str == "255.255.255.255":
        return "Broadcast terbatas"
    if _in_cidr(ip_int, "0.0.0.0", 8):
        return "Jaringan ini"
    if _in_cidr(ip_int, "10.0.0.0", 8) or _in_cidr(ip_int, "172.16.0.0", 12) or _in_cidr(ip_int, "192.168.0.0", 16):
        return "Private Internet (RFC 1918)"
    if _in_cidr(ip_int, "100.64.0.0", 10):
        return "CGNAT (RFC 6598)"
    if _in_cidr(ip_int, "127.0.0.0", 8):
        return "Loopback"
    if _in_cidr(ip_int, "169.254.0.0", 16):
        return "Link-local (APIPA)"
    if _in_cidr(ip_int, "192.0.2.0", 24) or _in_cidr(ip_int, "198.51.100.0", 24) or _in_cidr(ip_int, "203.0.113.0", 24):
        return "Dokumentasi (TEST-NET)"
    if _in_cidr(ip_int, "224.0.0.0", 4):
        return "Multicast"
    if _in_cidr(ip_int, "240.0.0.0", 4):
        return "Dicadangkan"
    return "Publik"


def hitung_subnet(ip: str, prefix: int) -> dict:
    ip_int = _ip_to_int(ip)
    prefix = _validate_prefix(prefix)
    mask_int = _prefix_to_mask(prefix)
    wild_int = (~mask_int) & 0xFFFFFFFF
    net_int = ip_int & mask_int
    bcast_int = net_int | wild_int
    total = 1 << (32 - prefix)
    kelas = _kelas_dari_ip_int(ip_int)
    jenis = _jenis_alamat(_int_to_ip(ip_int), ip_int)

    if prefix == 32:
        broadcast = None
        first_host = _int_to_ip(ip_int)
        last_host = _int_to_ip(ip_int)
        usable = 1
    elif prefix == 31:
        broadcast = None
        first_host = _int_to_ip(net_int)
        last_host = _int_to_ip(bcast_int)
        usable = 2
    else:
        broadcast = _int_to_ip(bcast_int)
        first_host = _int_to_ip(net_int + 1)
        last_host = _int_to_ip(bcast_int - 1)
        usable = total - 2

    def b(val):
        if val is None:
            return None
        if isinstance(val, int):
            return _to_bin32(val)
        return _to_bin32(_ip_to_int(val))

    biner = {
        "ip": _to_bin32(ip_int),
        "mask": _to_bin32(mask_int),
        "wildcard": _to_bin32(wild_int),
        "network": _to_bin32(net_int),
        "broadcast": _to_bin32(bcast_int) if prefix < 31 else None,
        "first_host": b(first_host),
        "last_host": b(last_host),
    }

    return {
        "mask": _int_to_ip(mask_int),
        "network": _int_to_ip(net_int),
        "broadcast": broadcast,
        "first_host": first_host,
        "last_host": last_host,
        "usable_hosts": usable,
        "prefix": prefix,
        "wildcard": _int_to_ip(wild_int),
        "kelas": kelas,
        "jenis": jenis,
        "total_alamat": total,
        "biner": biner,
    }


def bagi_subnet(ip, prefix_awal, prefix_baru, offset=0, limit=256) -> dict:
    ip_int = _ip_to_int(str(ip))
    prefix_awal = _validate_prefix(prefix_awal)
    prefix_baru = _validate_prefix(prefix_baru)
    try:
        offset = int(offset)
        limit = int(limit)
    except Exception:
        _err("Offset dan limit harus bilangan bulat")
    if offset < 0:
        _err("Offset tidak boleh negatif")
    if limit < 0:
        _err("Limit tidak boleh negatif")
    if limit > 1024:
        limit = 1024

    if prefix_baru < prefix_awal:
        h = hitung_subnet(_int_to_ip(ip_int), prefix_baru)
        h["mode"] = "supernet"
        h["prefix_awal"] = prefix_awal
        h["prefix_baru"] = prefix_baru
        h["jumlah_jaringan_digabung"] = 1 << (prefix_awal - prefix_baru)
        return h

    # subnet mode (baru >= awal)
    jumlah = 1 << (prefix_baru - prefix_awal)
    base_net = ip_int & _prefix_to_mask(prefix_awal)
    block = 1 << (32 - prefix_baru)
    host_per = hitung_subnet(_int_to_ip(base_net), prefix_baru)["usable_hosts"]
    items = []
    start = offset
    end = min(offset + limit, jumlah)
    for i in range(start, end):
        net_i = base_net + i * block
        h = hitung_subnet(_int_to_ip(net_i), prefix_baru)
        item = {"nomor": i + 1, "network_cidr": f"{h['network']}/{prefix_baru}"}
        item.update(h)
        items.append(item)
    terpotong = (offset + len(items)) < jumlah
    return {
        "mode": "subnet",
        "jumlah_subnet": jumlah,
        "host_per_subnet": host_per,
        "prefix_awal": prefix_awal,
        "prefix_baru": prefix_baru,
        "offset": offset,
        "limit": limit,
        "terpotong": terpotong,
        "subnet": items,
    }


def alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]:
    if network_cidr is None or not isinstance(network_cidr, str):
        _err("Network CIDR harus berupa teks")
    if not isinstance(kebutuhan_host, list):
        _err("Kebutuhan host harus berupa daftar")
    if len(kebutuhan_host) == 0:
        _err("Daftar kebutuhan host tidak boleh kosong")
    kebutuhan = []
    for k in kebutuhan_host:
        if isinstance(k, bool) or not isinstance(k, int):
            _err("Setiap kebutuhan host harus bilangan bulat >= 1")
        if k < 1:
            _err("Setiap kebutuhan host harus bilangan bulat >= 1")
        kebutuhan.append(k)

    s = network_cidr.strip()
    if "/" not in s:
        _err("Network CIDR harus dalam format alamat/prefix, mis. 192.168.1.0/24")
    ip_part, pref_part = s.rsplit("/", 1)
    ip_int = _ip_to_int(ip_part.strip())
    if pref_part.strip().isdigit() or (pref_part.strip().startswith("-") and pref_part.strip()[1:].isdigit()):
        pref = _validate_prefix(pref_part.strip())
    else:
        pref = parse_netmask(pref_part.strip())
    net_base = ip_int & _prefix_to_mask(pref)
    if net_base != ip_int:
        _err("Network CIDR bukan alamat network yang valid; bit host harus nol")
    parent_total = 1 << (32 - pref)
    parent_end = net_base + parent_total

    terurut = sorted(kebutuhan, reverse=True)
    hasil = []
    cursor = net_base
    for need in terurut:
        ukuran_dibutuhkan = need + 2
        bits_host = 0
        while (1 << bits_host) < ukuran_dibutuhkan:
            bits_host += 1
        if bits_host < 2:
            bits_host = 2  # minimal /30
        sub_prefix = 32 - bits_host
        if sub_prefix < pref:
            _err("Kebutuhan host tidak muat dalam network yang disediakan")
        blok = 1 << bits_host
        # align cursor ke batas blok
        if cursor % blok != 0:
            cursor = ((cursor // blok) + 1) * blok
        if cursor + blok > parent_end:
            _err("Kebutuhan host tidak muat dalam network yang disediakan")
        h = hitung_subnet(_int_to_ip(cursor), sub_prefix)
        item = {"kebutuhan": need, "network_cidr": f"{h['network']}/{sub_prefix}"}
        item.update(h)
        hasil.append(item)
        cursor += blok
    return hasil


# ---------- API ----------

def _bad(msg: str):
    return JSONResponse(status_code=400, content={"detail": msg})


def _parse_prefix_param(val: str):
    try:
        if val is None or str(val).strip() == "":
            _err("Prefix tidak boleh kosong")
        s = str(val).strip()
        if not re.fullmatch(r"-?[0-9]+", s):
            _err("Prefix harus bilangan bulat 0-32")
        p = int(s)
        if p < 0 or p > 32:
            _err(f"Prefix {p} di luar rentang; harus 0-32")
        return p
    except ValueError:
        raise


@app.get("/api/subnet")
def api_subnet(ip: str = Query(...), prefix: str = Query(...)):
    try:
        p = _parse_prefix_param(prefix)
        hasil = hitung_subnet(ip, p)
        return hasil
    except ValueError as e:
        return _bad(str(e))


def _parse_address_and_mask(address: str, netmask: str | None):
    if address is None or str(address).strip() == "":
        _err("Alamat tidak boleh kosong")
    addr = str(address).strip()
    if addr != address or any(c.isspace() for c in addr):
        _err("Alamat tidak boleh mengandung spasi")
    ip_part = addr
    prefix_from_addr = None
    if "/" in addr:
        left, right = addr.rsplit("/", 1)
        if left == "" or right == "":
            _err("Format alamat/prefix tidak valid")
        ip_part = left
        prefix_from_addr = parse_netmask("/" + right) if not ("." in right) else parse_netmask(right)
        # right could be number; parse_netmask handles
        try:
            if right.strip().isdigit() or (right.strip().startswith("-")):
                # number
                rv = int(right.strip())
                if rv < 0 or rv > 32:
                    _err(f"Prefix {rv} di luar rentang; harus 0-32")
                prefix_from_addr = rv
            elif "." in right:
                prefix_from_addr = parse_netmask(right)
            else:
                prefix_from_addr = parse_netmask("/" + right.lstrip("/"))
        except ValueError:
            raise
    # determine prefix
    nm = None
    if netmask is not None and str(netmask).strip() != "":
        nm = parse_netmask(str(netmask).strip())
    if prefix_from_addr is not None and nm is not None and prefix_from_addr != nm:
        _err("Prefix pada address dan netmask berbeda; pilih salah satu")
    if prefix_from_addr is not None:
        pref = prefix_from_addr
    elif nm is not None:
        pref = nm
    else:
        pref = prefix_default(ip_part)
    # validate ip
    _ip_to_int(ip_part)
    return ip_part, pref


@app.get("/api/ipcalc")
def api_ipcalc(
    address: str = Query(...),
    netmask: str | None = Query(None),
    netmask2: str | None = Query(None),
    offset: str | int = Query(0),
    limit: str | int = Query(256),
):
    try:
        ip_part, pref = _parse_address_and_mask(address, netmask)
        hasil = hitung_subnet(ip_part, pref)
        pembagian = None
        if netmask2 is not None and str(netmask2).strip() != "":
            p2 = parse_netmask(str(netmask2).strip())
            pembagian = bagi_subnet(ip_part, pref, p2, offset=offset, limit=limit)
        return {"hasil": hasil, "pembagian": pembagian}
    except ValueError as e:
        return _bad(str(e))


@app.post("/api/vlsm")
async def api_vlsm(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _bad("Body JSON tidak valid")
    if not isinstance(body, dict):
        return _bad("Body harus berupa objek JSON")
    network = body.get("network")
    kebutuhan = body.get("kebutuhan_host")
    try:
        if network is None or not isinstance(network, str):
            _err("Field 'network' harus berupa string CIDR")
        if not isinstance(kebutuhan, list):
            _err("Field 'kebutuhan_host' harus berupa daftar angka")
        hasil = alokasi_vlsm(network, kebutuhan)
        return JSONResponse(content=hasil)
    except ValueError as e:
        return _bad(str(e))
