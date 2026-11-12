# Kalkulator Subnet & VLSM

Kalkulator IPv4 berbasis web untuk guru SMK TKJ (setara ipcalc, dengan VLSM dan mode belajar). Aplikasi hanya terdiri dari `main.py` dan `index.html` (CSS/JS tertanam), tanpa CDN/font/gambar eksternal.

## Docker - Mode pengembangan (live reload)

Prasyarat: Docker Engine + Compose, `uv`, `gh`.

```bash
make dev      # jalankan dev, log di terminal (Ctrl+C untuk berhenti)
# atau
make up       # jalankan dev di latar belakang
make logs     # lihat log
make stop     # hentikan
```

Buka http://localhost:8100

**Mengapa perubahan file di host otomatis berubah di container:** `docker-compose.yml` memasang bind mount `./:/app` sehingga file `main.py` dan `index.html` di host adalah file yang sama di dalam container. Uvicorn dijalankan dengan `--reload --reload-dir /app --reload-include "*.html"` (lihat `Dockerfile.dev`), sehingga setiap perubahan memicu muat ulang otomatis; browser juga melakukan refresh otomatis saat endpoint dev `/__dev/versi` (hanya aktif bila `APP_ENV=dev`) berubah.

Menjalankan tes di dalam container dev:

```bash
make test
make cov      # coverage
make smoke    # smoke test ke dev (http://127.0.0.1:8100)
```

Bila `pyproject.toml`/`uv.lock` berubah: `make rebuild`.

## Docker - Mode produksi

```bash
make prod-build
make prod-run    # image produksi di http://localhost:8180
make prod-stop
```

Image produksi (`Dockerfile`) memakai base `python:3.12-slim`, memasang dependensi via `uv` dari `pyproject.toml`/`uv.lock`, lalu hanya menyalin `main.py` dan `index.html`. Endpoint `/__dev/versi` mengembalikan 404 di produksi.

Smoke test ke lingkungan mana pun:

```bash
uv run python scripts/smoke_test.py http://127.0.0.1:8180
```

## Catatan

- Port di dalam container tetap 8000; port host dev 8100 dan prod 8180 (agar tidak bentrok dengan layanan lain).
- CI (`.github/workflows/ci.yml`): job `test` (pytest+coverage) lalu job `docker` (build image + smoke test container).
