import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/")
def index():
    return FileResponse(INDEX_PATH)


@app.get("/api/ping")
def ping():
    return {"ok": True}


@app.get("/__dev/versi")
def dev_versi():
    if os.getenv("APP_ENV") != "dev":
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    mtimes = []
    for name in ("main.py", "index.html"):
        p = BASE_DIR / name
        if p.exists():
            mtimes.append(p.stat().st_mtime_ns)
    return {"versi": max(mtimes) if mtimes else 0}


def hitung_subnet(ip: str, prefix: int) -> dict:
    raise NotImplementedError


def parse_netmask(teks: str) -> int:
    raise NotImplementedError


def prefix_default(ip: str) -> int:
    raise NotImplementedError


def bagi_subnet(ip, prefix_awal, prefix_baru, offset=0, limit=256) -> dict:
    raise NotImplementedError
