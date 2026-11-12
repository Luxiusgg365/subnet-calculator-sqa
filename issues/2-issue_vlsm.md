# [Feature] VLSM

## Deskripsi
Menambahkan kalkulasi dan antarmuka VLSM (Variable Length Subnet Masking) pada aplikasi Kalkulator Subnet, sesuai `SPEC.md`.

## Tugas
- [ ] Implementasi `alokasi_vlsm(network_cidr, kebutuhan_host)` dan endpoint `POST /api/vlsm` (kembalikan LIST)
- [ ] UI tab VLSM: input network, kebutuhan + label opsional, tabel alokasi, batang pemakaian, sisa alamat, ekspor CSV
- [ ] Test VLSM ditulis lebih dulu, lalu implementasi sampai hijau
- [ ] Coverage `main.py` >= 95%

## Kriteria Penerimaan
- VLSM 192.168.1.0/24 untuk [100,50,20,2] -> /25 (.0), /26 (.128), /27 (.192), /30 (.224)
- Urutan kebutuhan acak menghasilkan alokasi benar (diurutkan desc)
- Tidak muat (mis. [200,100] dalam /24) -> ValueError / 400
- network_cidr bukan alamat network (mis. 192.168.1.5/24) -> ditolak
- Minimal blok /30; daftar kosong atau nilai <1 -> ditolak
- UI menampilkan label, batang visual pemakaian, sisa alamat, ekspor CSV

## Alur Kerja
issue -> branch -> test dulu -> implementasi -> commit -> pull request -> CI -> merge
