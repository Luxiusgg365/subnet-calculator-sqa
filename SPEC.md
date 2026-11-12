# SPEC.md - Kalkulator Subnet & VLSM

## 1. Tujuan
Aplikasi web kalkulator IPv4 untuk guru SMK TKJ, setara dengan jodies.de/ipcalc dan melampauinya. Berjalan tanpa internet (tanpa CDN/font/gambar eksternal), hanya `main.py` dan `index.html` (CSS/JS di dalam `index.html`).

## 2. Aturan Validasi

### 2.1 Alamat IPv4
- Tepat 4 oktet dipisah titik.
- Tiap oktet bilangan bulat 0-255.
- Tanpa nol di depan (contoh `192.168.01.1` ditolak).
- Tanpa spasi di dalam atau di tepi nilai yang divalidasi sebagai token (input dari field dipangkas; spasi internal ditolak).
- Input salah -> `ValueError` dengan pesan spesifik berbahasa Indonesia (contoh: "Oktet ke-3 bernilai 256; harus 0-255", "Alamat IPv4 harus terdiri dari tepat 4 oktet", "Oktet tidak boleh diawali nol", "Alamat IPv4 mengandung karakter tidak valid").

### 2.2 Prefix / Netmask
- Prefix: bilangan bulat 0-32. Di luar rentang -> `ValueError`.
- `parse_netmask(teks: str) -> int` menerima: `24`, `/24`, dotted `255.255.255.0`, dan inverse/wildcard `0.0.0.255`.
- Mask harus berkesinambungan (bit 1 berurutan dari kiri). `255.0.255.0` ditolak dengan pesan spesifik.
- Keputusan default: `0.0.0.0` dibaca sebagai /0 (bukan inverse /32); `255.255.255.255` = /32; `0.0.0.255` = /24.

### 2.3 Netmask default kelas
- `prefix_default(ip: str) -> int`: A=8, B=16, C=24.
- Kelas D/E -> `ValueError("Kelas D/E tidak punya netmask default, isi netmask")`.
- Kelas dari oktet pertama: A 0-127, B 128-191, C 192-223, D 224-239, E 240-255.

### 2.4 API
- Semua kesalahan input API -> HTTP 400 dengan body JSON `{"detail": "<pesan>"}`.
- Parameter query ditangkap sebagai `str` lalu divalidasi manual.
- Pasang handler `RequestValidationError` yang mengubah 422 menjadi 400 (sehingga `prefix=abc` tetap 400).

## 3. Kontrak Fungsi (`main.py`)

### 3.1 `hitung_subnet(ip: str, prefix: int) -> dict`
Kunci wajib (nama tidak diubah): `mask, network, broadcast, first_host, last_host, usable_hosts`.
Kunci tambahan: `prefix, wildcard, kelas, jenis, total_alamat, biner`.

- Network dihitung dengan bitwise AND antara IP dan mask (bukan string/aritmatika lain).
- `wildcard` = inverse mask.
- `total_alamat = 2^(32-prefix)`.
- Host usable:
  - prefix 0-30: `2^(32-prefix) - 2`, `first_host = network+1`, `last_host = broadcast-1`.
  - /31 (RFC 3021, point-to-point): 2 host, `broadcast = None`, `first_host` dan `last_host` adalah dua alamat dalam subnet.
  - /32: 1 host, `broadcast = None`, `first_host = last_host = IP`.
- `kelas`: A 0-127, B 128-191, C 192-223, D 224-239, E 240-255.
- `jenis` (paling spesifik): `0.0.0.0/8` "Jaringan ini", `10/8`,`172.16/12`,`192.168/16` "Private Internet (RFC 1918)", `100.64/10` "CGNAT (RFC 6598)", `127/8` "Loopback", `169.254/16` "Link-local (APIPA)", `192.0.2/24`,`198.51.100/24`,`203.0.113/24` "Dokumentasi (TEST-NET)", `224/4` "Multicast", `240/4` "Dicadangkan", `255.255.255.255` "Broadcast terbatas", selain itu "Publik".
- `biner`: dict berisi `ip, mask, wildcard, network, broadcast, first_host, last_host` sebagai string 32-bit bertitik per oktet (mis. `11000000.10101000.00000000.00000001`). Untuk nilai `None` (broadcast/host pada /31,/32 sesuai kasus) simpan `None`. UI menyisipkan celah visual pada batas prefix.

### 3.2 `parse_netmask(teks: str) -> int`
Mengembalikan prefix 0-32. Menerima `24`, `/24`, `255.255.255.0`, `0.0.0.255`. Validasi kontigu; `0.0.0.0` -> 0.

### 3.3 `prefix_default(ip: str) -> int`
A=8, B=16, C=24; D/E -> ValueError sesuai 2.3.

### 3.4 `bagi_subnet(ip, prefix_awal, prefix_baru, offset=0, limit=256) -> dict`
- `prefix_baru >= prefix_awal` (mode `"subnet"`): kunci `mode, jumlah_subnet, host_per_subnet, prefix_awal, prefix_baru, offset, limit, terpotong, subnet`.
  - `jumlah_subnet` = total sebenarnya `2^(prefix_baru-prefix_awal)`.
  - `host_per_subnet` = usable hosts per subnet baru (sesuai aturan /31,/32).
  - `limit` maksimum 1024; daftar `subnet` tidak lebih besar dari limit (setelah offset). `terpotong = (offset + len(subnet) < jumlah_subnet)`.
  - Tiap item `subnet`: `nomor` (mulai 1, global), `network_cidr`, dan semua kunci `hitung_subnet` untuk subnet tersebut.
- `prefix_baru < prefix_awal` (mode `"supernet"`): hasil `hitung_subnet(ip, prefix_baru)` ditambah kunci `mode="supernet"`, `prefix_awal`, `prefix_baru`, `jumlah_jaringan_digabung = 2^(prefix_awal-prefix_baru)`.

### 3.5 `alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]`
- Urutkan kebutuhan dari terbesar. Alokasikan berurutan mulai alamat network.
- Ukuran blok = pangkat 2 terkecil yang >= `kebutuhan + 2` (ruang network+broadcast), minimal /30 (blok 4).
- Tiap hasil: `kebutuhan`, `network_cidr`, plus semua kunci `hitung_subnet`.
- `ValueError` bila: `network_cidr` bukan alamat network valid (host bit tidak nol), daftar kosong atau ada nilai < 1, atau blok tidak muat dalam ruang induk.

## 4. Kontrak API

- `GET /` -> `index.html`.
- `GET /api/subnet?ip=&prefix=` -> JSON hasil `hitung_subnet` (kontrak asli, tidak berubah).
- `POST /api/vlsm` body `{"network":"...","kebutuhan_host":[...]}` -> JSON **LIST** hasil `alokasi_vlsm` (kontrak asli).
- `GET /api/ipcalc?address=&netmask=&netmask2=&offset=&limit=` -> endpoint utama UI.
  - `address` boleh `ip` atau `ip/prefix`; `netmask` opsional (kosong & address tanpa `/` -> `prefix_default`).
  - `netmask2` opsional (pembagian/supernet).
  - Bila address memuat `/` DAN `netmask` terisi dan keduanya berbeda: 400.
  - Respons: `{"hasil": <hitung_subnet>, "pembagian": <bagi_subnet atau null>}`.
  - Query ditangkap string, divalidasi manual; `RequestValidationError` -> 400.
- `GET /__dev/versi` -> hanya bila `APP_ENV=dev` (200 + `{"versi": <int>}`), selain itu 404.

## 5. Halaman Web (`index.html`)

- Dua tab: "Subnet" dan "VLSM".
- Tab Subnet: input Address, Netmask, Netmask kedua opsional ("Pindah ke netmask"); tombol Hitung; hasil langsung saat mengetik (debounce 250 ms) dan Enter; tabel baris Address, Netmask(=bit), Wildcard, Network, Broadcast, HostMin, HostMax, Hosts/Net dengan kolom desimal & biner (celah di batas prefix; bit jaringan biru, host abu-oranye, bit baru hijau bergaris bawah + legenda).
- Keadaan: kosong, sukses, error (pesan di bawah field, `aria-live`).
- Pembagian: tabel subnet + jumlah subnet + hosts per subnet (dan supernet bila netmask2 lebih pendek).
- Nilai tambah (bagian B): Mode Belajar (AND/OR langkah biner), tautan `?a=&m=&m2=` via `history.replaceState`, salin per baris/semua, ekspor CSV subnet/VLSM, chip contoh, tema terang/gelap/otomatis (localStorage try/catch), responsif (360px+), CSS cetak, aksesibel (label, kontras AA, fokus, keyboard), saklar ID/EN (default ID), pesan error spesifik mendidik.
- Tab VLSM: network CIDR, daftar kebutuhan + label opsional, hasil alokasi, batang visual pemakaian, sisa alamat, ekspor CSV.
- Tanpa CDN/font/gambar eksternal. Font monospace sistem untuk tabel.

## 6. Tabel Test Case (wajib)
| Input | Hasil |
|---|---|
| 172.16.5.130/25 | network 172.16.5.128, broadcast 172.16.5.255, 126 host |
| 10.0.0.0/30 | .1 sampai .2, broadcast .3, 2 host |
| 192.168.1.0/31 | point-to-point, 2 host, broadcast None |
| 192.168.1.5/32 | 1 host, broadcast None |
| 10.0.0.0/8 | 16777214 host |
| 0.0.0.0/0 | 4294967294 host |
| 192.168.0.1 tanpa netmask | /24, kelas C, "Private Internet (RFC 1918)" |
| 10.1.2.3 tanpa netmask | /8, kelas A |
| 172.16.0.1 tanpa netmask | /16, kelas B |
| netmask `255.255.255.0`, `/24`, `24`, `0.0.0.255` | semuanya /24 |
| netmask `255.0.255.0`, `33`, `-1`, `abc` | ditolak |
| 127.0.0.1 / 169.254.1.1 / 100.64.0.1 / 224.0.0.1 / 8.8.8.8 | Loopback / Link-local / CGNAT / Multicast (kelas D) / Publik |
| 192.168.0.1/24 pindah ke /26 | 4 subnet: 192.168.0.0, .64, .128, .192 (/26, 62 host tiap subnet) |
| 192.168.5.1/24 pindah ke /22 | supernet 192.168.4.0/22, broadcast 192.168.7.255, 1022 host |
| 256.1.1.1/24, 192.168.01.1/24, 192.168.1, abc, kosong, prefix 33, prefix -1 | ditolak (400 di API) |
| VLSM 192.168.1.0/24 untuk 100, 50, 20, 2 | /25 (.0), /26 (.128), /27 (.192), /30 (.224) |
| VLSM 192.168.1.0/24 untuk 200 dan 100 | ditolak (tidak muat) |
| VLSM 192.168.1.5/24 | ditolak (bukan alamat network) |
| GET /__dev/versi tanpa APP_ENV=dev | 404 |

## 7. Di Luar Cakupan
IPv6, deagregasi rentang, login/akun, basis data, deploy ke layanan hosting (Vercel dan sejenisnya).
