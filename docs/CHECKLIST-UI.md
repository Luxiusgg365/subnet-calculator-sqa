# CHECKLIST-UI - Pemeriksaan Manual (Fase 4+7)

## Target produk A (paritas ipcalc)
- [ ] Input Address (host/network, boleh `ip/prefix`) + Netmask terpisah
- [ ] Netmask CIDR (`/25`) atau desimal (`255.255.255.0`), awalan `/` opsional
- [ ] Netmask inverse (`0.0.0.255`) dikenali sebagai /24
- [ ] Netmask kosong -> default kelas (A=/8,B=/16,C=/24), kelas D/E error jelas
- [ ] Baris Address, Netmask(=bit), Wildcard, Network, Broadcast, HostMin, HostMax, Hosts/Net
- [ ] Kolom desimal dan biner; celah/garis pemisah di batas prefix (termasuk tengah oktet)
- [ ] Lencana kelas di baris Network
- [ ] Lencana jenis alamat (Private/RFC1918, Loopback, Link-local, CGNAT, Multicast, Dokumentasi, dll.)
- [ ] Netmask kedua "Pindah ke netmask": lebih panjang=subnet, lebih pendek=supernet
- [ ] Bit baru subnet berwarna berbeda (hijau) + garis bawah (bukan hanya warna)
- [ ] Tabel subnet/supernet: daftar, jumlah subnet, hosts per subnet

## Target produk B (nilai tambah)
- [ ] Mode Belajar: AND IP-mask, OR network-wildcard, HostMin/Max, rumus host
- [ ] Hasil langsung debounce 250ms + Enter
- [ ] Tautan berbagi `?a=&m=&m2=` (replaceState), buka tautan langsung hitung
- [ ] Salin per baris dan salin semua; ekspor CSV subnet & VLSM
- [ ] Chip contoh: `192.168.0.1/24`, `172.16.5.130/25`, `10.0.0.0/30`, `192.168.1.0/31`, `192.168.1.5/32`
- [ ] Tema terang/gelap/otomatis, tersimpan localStorage (try/catch)
- [ ] VLSM: label opsional, batang visual pemakaian, sisa alamat
- [ ] Responsif 360px-desktop, CSS cetak rapi
- [ ] Aksesibel: label terkait, error `aria-live`, kontras AA, fokus terlihat, keyboard-only
- [ ] Saklar bahasa ID/EN (default ID)
- [ ] Pesan error spesifik mendidik

## Status verifikasi (diisi Fase 7/10)
- Fase 4 (prototipe statis): layout/tab/form/tabel contoh/tema dasar/chip ada; logika API belum terhubung.
- Fase 7: (isi saat verifikasi web)
- Fase 10: (isi saat verifikasi VLSM)
