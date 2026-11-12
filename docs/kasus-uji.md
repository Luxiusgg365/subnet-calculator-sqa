# Kasus Uji Kalkulator Subnet & VLSM

Dokumen ini disusun dari sudut pandang guru TKJ dan penguji perangkat lunak. Status: **pasti** = sesuai SPEC/keputusan baku; **keputusan** = ambigu di sumber, memakai default Fase 3.

## 1. Subnet normal dan prefix khusus

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Subnet /25 | 172.16.5.130/25 | network 172.16.5.128, broadcast 172.16.5.255, HostMin .129, HostMax .254, 126 host usable | pasti |
| Subnet /30 | 10.0.0.0/30 | network .0, broadcast .3, HostMin .1, HostMax .2, 2 host | pasti |
| /31 point-to-point (RFC 3021) | 192.168.1.0/31 | 2 host usable, broadcast None, first/last = .0 dan .1 | pasti |
| /32 host tunggal | 192.168.1.5/32 | 1 host usable, broadcast None, first_host=last_host=IP | pasti |
| /8 | 10.0.0.0/8 | 16777214 host, mask 255.0.0.0 | pasti |
| /16 | 172.16.0.0/16 | 65534 host | pasti |
| /24 | 192.168.1.0/24 | 254 host | pasti |
| /0 | 0.0.0.0/0 | network 0.0.0.0, broadcast 255.255.255.255, 4294967294 host | pasti |

## 2. Kelas jaringan (A-E)

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Kelas A | 10.1.2.3 | kelas A | pasti |
| Kelas B | 172.16.0.1 | kelas B | pasti |
| Kelas C | 192.168.0.1 | kelas C | pasti |
| Kelas D | 224.0.0.1 | kelas D (multicast) | pasti |
| Kelas E | 240.0.0.1 | kelas E (dicadangkan) | pasti |

## 3. Alamat khusus / jenis

| Kasus | Input | Jenis yang diharapkan | Status |
|---|---|---|---|
| Private RFC 1918 | 10.0.0.1, 172.16.5.1, 192.168.0.1 | Private Internet (RFC 1918) | pasti |
| Loopback | 127.0.0.1 | Loopback | pasti |
| Link-local APIPA | 169.254.1.1 | Link-local (APIPA) | pasti |
| CGNAT | 100.64.0.1 | CGNAT (RFC 6598) | pasti |
| Multicast | 224.0.0.1 | Multicast | pasti |
| Dokumentasi TEST-NET | 192.0.2.1, 198.51.100.1, 203.0.113.1 | Dokumentasi (TEST-NET) | pasti |
| Jaringan ini | 0.0.0.1 | Jaringan ini (0.0.0.0/8) | pasti |
| Broadcast terbatas | 255.255.255.255 | Broadcast terbatas | pasti |
| Dicadangkan | 240.0.0.1 | Dicadangkan | pasti |
| Publik | 8.8.8.8 | Publik | pasti |

## 4. Netmask default kelas (kolom netmask kosong)

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Default A | 10.1.2.3 tanpa netmask | /8 | pasti |
| Default B | 172.16.0.1 tanpa netmask | /16 | pasti |
| Default C | 192.168.0.1 tanpa netmask | /24 | pasti |
| Default D/E | 224.0.0.1 atau 240.0.0.1 tanpa netmask | ValueError: "Kelas D/E tidak punya netmask default, isi netmask" | pasti |

## 5. Format dan interpretasi netmask

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| CIDR | /24, 24 | prefix 24 | pasti |
| Dotted | 255.255.255.0 | prefix 24 | pasti |
| Inverse (wildcard) | 0.0.0.255 | prefix 24 | pasti |
| 0.0.0.0 | 0.0.0.0 | /0 (bukan inverse /32) | keputusan→default Fase 3 |
| 255.255.255.255 | 255.255.255.255 | /32 | pasti |
| Tidak berkesinambungan | 255.0.255.0 | ditolak (ValueError) | pasti |
| Prefix di luar rentang | 33, -1 | ditolak | pasti |
| Bukan angka | abc | ditolak | pasti |

## 6. Input tidak valid (IP/prefix)

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Oktet > 255 | 256.1.1.1/24 | ditolak, pesan spesifik oktet ke-1 | pasti |
| Nol di depan | 192.168.01.1/24 | ditolak | pasti |
| Spasi | " 192.168.1.1" | ditolak | pasti |
| Kurang oktet | 192.168.1 | ditolak | pasti |
| Lebih oktet | 192.168.1.1.1 | ditolak | pasti |
| Bukan angka | abc | ditolak | pasti |
| Kosong | "" | ditolak | pasti |
| Prefix 33/-1 | 192.168.1.1/33, /-1 | ditolak | pasti |
| Alamat+prefix ganda beda | address "192.168.1.1/24" dan netmask "/25" | 400 (konflik) | pasti |

## 7. Pembagian subnet dan supernet

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Subnetting /24→/26 | 192.168.0.1/24 pindah ke /26 | 4 subnet: .0, .64, .128, .192; 62 host per subnet; terpotong=false bila limit>=4 | pasti |
| Supernet /24→/22 | 192.168.5.1/24 pindah ke /22 | supernet 192.168.4.0/22, broadcast 192.168.7.255, 1022 host, jumlah_jaringan_digabung 4 | pasti |
| Limit/offset | offset & limit | jumlah_subnet total sebenarnya, daftar <= limit, terpotong benar | pasti |
| prefix_baru == prefix_awal | sama | 1 subnet (network asli) | keputusan→masuk mode subnet (baru>=awal) |

## 8. VLSM

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| Normal | 192.168.1.0/24 kebutuhan [100,50,20,2] | /25 .0, /26 .128, /27 .192, /30 .224 | pasti |
| Urutan acak | kebutuhan [2,100,20,50] | hasil sama (diurutkan desc) | pasti |
| Tidak muat | 192.168.1.0/24 kebutuhan [200,100] | ValueError tidak muat | pasti |
| Bukan alamat network | 192.168.1.5/24 | ValueError (host bit tidak nol) | pasti |
| Minimal blok /30 | kebutuhan 1 atau 2 | dialokasikan /30 (blok 4) | pasti |
| Daftar kosong/nilai <1 | [], [0], [-1] | ValueError | pasti |

## 9. API & UI khusus

| Kasus | Input | Hasil yang diharapkan | Status |
|---|---|---|---|
| GET / | - | 200 HTML | pasti |
| GET /api/subnet valid | ip=172.16.5.130&prefix=25 | 200, JSON hitung_subnet | pasti |
| GET /api/subnet invalid | ip=256.1.1.1 | 400 + detail | pasti |
| POST /api/vlsm | network+kebutuhan | 200 LIST hasil | pasti |
| GET /__dev/versi tanpa APP_ENV=dev | - | 404 | pasti |
| GET /__dev/versi dengan APP_ENV=dev | - | 200 + versi | pasti |
| Param query non-angka | prefix=abc | 400 (bukan 422) | pasti |
