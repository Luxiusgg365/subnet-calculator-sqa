# [Feature] Kalkulator Subnet

## Deskripsi
Membangun aplikasi web Kalkulator IPv4 (subnet) untuk guru SMK TKJ yang setara dengan jodies.de/ipcalc dan melampauinya, sesuai `SPEC.md`.

## Tugas
- [ ] Implementasi fungsi inti: `hitung_subnet`, `parse_netmask`, `prefix_default`, `bagi_subnet`
- [ ] Implementasi endpoint: `GET /`, `GET /api/subnet`, `GET /api/ipcalc`, handler 422->400
- [ ] UI tab Subnet: input address/netmask/netmask2, tabel hasil (desimal+biner), pembagian subnet/supernet
- [ ] Nilai tambah bagian B (Mode Belajar, tautan, salin/CSV, chip, tema, responsif, aksesibel, ID/EN, error spesifik)
- [ ] Test lulus dan coverage >= 95% untuk `main.py`

## Kriteria Penerimaan
Merujuk Tabel Test Case di `SPEC.md`:
- Hasil hitung benar untuk 172.16.5.130/25, 10.0.0.0/30, /31, /32, /8, /0
- Netmask kosong memakai default kelas (A/B/C) dan menolak D/E; netmask CIDR/dotted/inverse diterima, non-kontigu & di luar rentang ditolak
- Kelas dan jenis alamat (Private/Loopback/Link-local/CGNAT/Multicast/Dokumentasi/Publik/dll.) benar
- Pembagian: /24->/26 = 4 subnet; supernet /24->/22 benar
- Input tidak valid ditolak dengan `ValueError`/HTTP 400 + pesan spesifik
- `GET /__dev/versi` 404 tanpa APP_ENV=dev
- UI menampilkan baris Address/Netmask/Wildcard/Network/Broadcast/HostMin/HostMax/Hosts/Net, biner dengan celah batas prefix, warna bit + legenda
- `docs/CHECKLIST-UI.md` bagian A & B lulus pada web berjalan

## Alur Kerja
issue -> branch -> test dulu -> implementasi -> commit -> pull request -> CI -> merge
