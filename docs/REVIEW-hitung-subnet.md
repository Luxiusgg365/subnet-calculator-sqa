# REVIEW: `hitung_subnet` (baris per baris untuk guru TKJ)

Dokumen ini menelaah fungsi `hitung_subnet(ip: str, prefix: int) -> dict` di `main.py` tanpa mengubah kode. Fokus: cara kerja, kaitan teori subnetting, dan asumsi/keputusan.

## 1. Validasi dan konversi masukan
- `ip_int = _ip_to_int(ip)`: memvalidasi alamat IPv4 (tepat 4 oktet, tiap oktet 0-255, tanpa nol di depan, tanpa spasi, hanya digit) lalu mengubahnya menjadi bilangan bulat 32-bit. Setiap oktet digeser ke posisinya: `(o1<<24)|(o2<<16)|(o3<<8)|o4`. Ini setara representasi biner 32 bit alamat.
- `prefix = _validate_prefix(prefix)`: memastikan prefix bilangan bulat 0-32. Kesalahan menghasilkan `ValueError` dengan pesan spesifik berbahasa Indonesia.

**Teori:** Alamat IPv4 adalah 32 bit; notasi desimal bertitik hanya cara baca empat oktet (8 bit).

## 2. Mask, wildcard, dan operasi AND (inti subnetting)
- `mask_int = _prefix_to_mask(prefix)`: membuat subnet mask dengan `prefix` bit 1 di kiri dan sisanya 0. Rumus: `(0xFFFFFFFF << (32-prefix)) & 0xFFFFFFFF` (khusus prefix 0 -> 0). Contoh /25 -> 25 bit 1 lalu 7 bit 0 = `255.255.255.128`.
- `wildcard_int = (~mask_int) & 0xFFFFFFFF`: kebalikan bit mask (bit host menjadi 1). Dipakai untuk menghitung broadcast dan sering tampil di ACL.
- `net_int = ip_int & mask_int`: **operasi AND bitwise** antara IP dan mask. Inilah cara menentukan alamat network: bit jaringan dipertahankan (AND dengan 1), bit host dipaksa 0 (AND dengan 0). Kode tidak memakai string/aritmatika lain, sesuai spesifikasi.
- `bcast_int = net_int | wild_int`: alamat broadcast = network dengan semua bit host menjadi 1 (OR dengan wildcard). Ekuivalen dengan mengisi bagian host network menjadi 1.

**Teori (contoh 172.16.5.130/25):**
```
IP      10101100.00010000.00000101.10000010 (172.16.5.130)
Mask    11111111.11111111.11111111.10000000 (255.255.255.128)
AND ->  10101100.00010000.00000101.10000000 (172.16.5.128 = network)

Wildcard00000000.00000000.00000000.01111111
OR    ->10101100.00010000.00000101.11111111 (172.16.5.255 = broadcast)
```

## 3. Jumlah alamat, kelas, dan jenis
- `total = 1 << (32 - prefix)` = 2^(32-prefix), total alamat dalam blok.
- `kelas = _kelas_dari_ip_int(ip_int)`: kelas A-E dari oktet pertama (0-127 A, 128-191 B, 192-223 C, 224-239 D, 240-255 E).
- `jenis = _jenis_alamat(...)`: label paling spesifik (RFC 1918, loopback, link-local, CGNAT, multicast, TEST-NET, dll.) dengan pengecekan awalan/CIDR.

## 4. Host usable dan kasus khusus /31, /32
- **/32**: 1 host, `broadcast = None`, `first_host = last_host = IP`, `usable = 1`. Satu alamat tunggal (host route).
- **/31** (RFC 3021, point-to-point): 2 host, `broadcast = None`, `first_host` = alamat network, `last_host` = alamat broadcast bitwise (dua alamat dipakai langsung tanpa network/broadcast tradisional), `usable = 2`.
- **/0-30**: `broadcast` ada, `first_host = network+1`, `last_host = broadcast-1`, `usable = total-2` (dua alamat dicadangkan: network dan broadcast).

**Teori:** Rumus umum host yang dapat dipakai = 2^(32-n)-2; pengecualian /31 dan /32 mengikuti praktik modern (RFC 3021).

## 5. Representasi biner dan keluaran
- `_to_bin32` menghasilkan string 32 bit bertitik per oktet (mis. `11000000.10101000.00000000.00000001`). `biner` menyimpan `ip, mask, wildcard, network, broadcast, first_host, last_host` (None bila tidak berlaku, mis. broadcast pada /31,/32). Celah visual di batas prefix dilakukan di UI, bukan di string data.
- Fungsi mengembalikan semua kunci wajib (`mask, network, broadcast, first_host, last_host, usable_hosts`) dan tambahan (`prefix, wildcard, kelas, jenis, total_alamat, biner`).

## 6. Asumsi dan keputusan yang tidak eksplisit di SPEC.md
- Pesan `ValueError` dibuat spesifik per jenis kesalahan (oktet ke-n, nol di depan, spasi, format netmask) untuk tujuan edukasi; teks pastinya tidak ditentukan SPEC selain "spesifik berbahasa Indonesia".
- `hitung_subnet` menerima `prefix` non-int dalam bentuk string angka sederhana (divalidasi `_validate_prefix`), meski kontrak utama memakai `int`.
- Penentuan `jenis` memakai urutan "paling spesifik" yang mencakup seluruh daftar SPEC (termasuk 0.0.0.0/8, 255.255.255.255, 240/4, TEST-NET spesifik); overlap diselesaikan dengan urutan pemeriksaan di kode.
- Untuk /31, `biner.broadcast` diset `None` (selaras field broadcast None) meski nilai bitwise ada; UI menampilkan sesuai.
- `bagi_subnet` saat `prefix_baru == prefix_awal` diperlakukan mode subnet (kondisi `baru >= awal`) menghasilkan 1 subnet; perilaku ini dicatat sebagai keputusan di `docs/kasus-uji.md`.

Semua perhitungan network/broadcast/host diturunkan dari operasi bitwise pada representasi integer 32-bit IP dan mask.
