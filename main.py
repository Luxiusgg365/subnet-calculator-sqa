import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"


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
