# DESIGN.md - Prototipe UI Kalkulator Subnet & VLSM

## Token Warna
- Terang: bg `#ffffff`, surface `#f8f9fa`, border `#dadce0`, text `#202124`, muted `#5f6368`, aksen `#1a73e8`, error `#d93025`.
- Gelap: bg `#202124`, surface `#303134`, border `#5f6368`, text `#e8eaed`, muted `#9aa0a6`, aksen `#8ab4f8`, error `#f28b82`.
- Otomatis: `prefers-color-scheme`.
- Bit: jaringan `#1a73e8` (terang)/`#8ab4f8` (gelap), host `#e37400`/`#fbbc04`, bit baru subnet `#188038`/`#81c995` + garis bawah.

## Tipografi & Jarak
- UI: system sans (`system-ui, -apple-system, Segoe UI, Roboto, sans-serif`).
- Tabel/bit: monospace sistem (`ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`).
- Spasi basis 8px; kartu padding 16-24px, radius 12px.

## Komponen
- Header: judul, saklar tema (terang/gelap/otomatis), saklar bahasa ID/EN.
- Tab: Subnet | VLSM.
- Form Subnet: input Address, Netmask, Netmask2 opsional, tombol Hitung, chip contoh, saklar Mode Belajar.
- Hasil: tabel baris (Address/Netmask/Wildcard/Network/Broadcast/HostMin/HostMax/Hosts/Net) kolom Label, Desimal, Biner; lencana kelas & jenis; legenda warna bit.
- Pembagian: ringkasan (jumlah subnet/host per subnet atau info supernet) + tabel subnet (aksi salin, ekspor CSV).
- VLSM: input network, baris kebutuhan+label, tombol tambah/hitung, tabel alokasi, batang pemakaian, sisa alamat, ekspor CSV.
- Keadaan: kosong (placeholder), sukses (tabel), error (pesan bawah field, `aria-live="polite"`).

## Responsif & Cetak
- Grid 1 kolom < 720px, 2 kolom >= 720px; target sentuh >= 44px; tabel scroll horizontal di ponsel 360px.
- `@media print`: sembunyikan kontrol interaktif non-esensial, latar putih, kontras tinggi.

## Aksesibilitas
- Label `for`/`id`, fokus terlihat (`:focus-visible`), kontras AA, navigasi keyboard, pesan error `aria-live`, warna bukan satu-satunya pembeda (bit baru bergaris bawah).

## Perilaku
- Hitung saat Enter dan debounce 250ms saat mengetik; query string `?a=&m=&m2=` via `history.replaceState`; salin per baris/semua; localStorage tema (try/catch).
