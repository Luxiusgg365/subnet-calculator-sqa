# Kalkulator Subnet & VLSM

Kalkulator IPv4 berbasis web untuk pembelajaran subnetting (setara ipcalc).

## Menjalankan (Docker, mode dev, live reload)

```bash
make dev
# atau di latar belakang
make up
```

Buka http://localhost:8100 . Perubahan `main.py` dan `index.html` di host langsung terlihat (uvicorn `--reload` + bind mount `./:/app`).

Hentikan: `make stop`

## Test

```bash
make test
make cov
```

## Produksi

```bash
make prod-build
make prod-run   # http://localhost:8180
make prod-stop
```
