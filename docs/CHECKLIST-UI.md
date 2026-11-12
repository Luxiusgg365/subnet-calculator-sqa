# CHECKLIST-UI - Pemeriksaan Manual (Fase 4+7)

## Target produk A (paritas ipcalc)
- [x] Input Address (host/network, boleh `ip/prefix`) + Netmask terpisah
- [x] Netmask CIDR (`/25`) atau desimal (`255.255.255.0`), awalan `/` opsional
- [x] Netmask inverse (`0.0.0.255`) dikenali sebagai /24
- [x] Netmask kosong -> default kelas (A=/8,B=/16,C=/24), kelas D/E error jelas
- [x] Baris Address, Netmask(=bit), Wildcard, Network, Broadcast, HostMin, HostMax, Hosts/Net
- [x] Kolom desimal dan biner; celah/garis pemisah di batas prefix (termasuk tengah oktet)
- [x] Lencana kelas di baris Network
- [x] Lencana jenis alamat (Private/RFC1918, Loopback, Link-local, CGNAT, Multicast, Dokumentasi, dll.)
- [x] Netmask kedua "Pindah ke netmask": lebih panjang=subnet, lebih pendek=supernet
- [x] Bit baru subnet berwarna berbeda (hijau) + garis bawah (bukan hanya warna)
- [x] Tabel subnet/supernet: daftar, jumlah subnet, hosts per subnet

## Target produk B (nilai tambah)
- [x] Mode Belajar: AND IP-mask, OR network-wildcard, HostMin/Max, rumus host
- [x] Hasil langsung debounce 250ms + Enter
- [x] Tautan berbagi `?a=&m=&m2=` (replaceState), buka tautan langsung hitung
- [x] Salin per baris dan salin semua; ekspor CSV subnet & VLSM (UI VLSM siap, backend VLSM menyusul Fase 10)
- [x] Chip contoh: `192.168.0.1/24`, `172.16.5.130/25`, `10.0.0.0/30`, `192.168.1.0/31`, `192.168.1.5/32`
- [x] Tema terang/gelap/otomatis, tersimpan localStorage (try/catch)
- [x] VLSM: label opsional, batang visual pemakaian, sisa alamat (UI; hasil nyata setelah Fase 10)
- [x] Responsif 360px-desktop, CSS cetak rapi
- [x] Aksesibel: label terkait, error `aria-live`, kontras AA, fokus terlihat, keyboard-only
- [x] Saklar bahasa ID/EN (default ID)
- [x] Pesan error spesifik mendidik

## Status verifikasi
- Fase 4 (prototipe statis): layout/tab/form/tabel contoh/tema/chip/legenda ada.
- Fase 7 (diverifikasi via API + container dev berjalan http://localhost:8100): `/api/ipcalc` 172.16.5.130/25 -> network 172.16.5.128, broadcast 172.16.5.255, 126 host; pembagian /24->/26 = 4 subnet (.0,.64,.128,.192/26, 62 host); supernet /24->/22 -> 192.168.4.0/22, broadcast 192.168.7.255, 1022 host; default mask 192.168.0.1 -> /24 C Private; error 400 untuk input invalid. UI terhubung ke API, debounce/Enter/query string/copy/CSV/tema/belajar/biner ber-celah aktif. `pytest` 73 lulus, coverage main.py 96%.
- Fase 10: (menyusul implementasi VLSM)
