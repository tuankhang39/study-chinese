"""One-shot bootstrap for free hosts (Render/Railway)."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from app.core.database import Base, engine

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/bootstrap")
def bootstrap(x_bootstrap_secret: str | None = Header(default=None)):
    expected = os.getenv("BOOTSTRAP_SECRET", "")
    if not expected or x_bootstrap_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    Base.metadata.create_all(bind=engine)

    candidates = [
        Path("/app/scripts/seed_db.py"),
        Path(__file__).resolve().parents[4] / "scripts" / "seed_db.py",
    ]
    seed_path = next((p for p in candidates if p.exists()), None)
    if not seed_path:
        raise HTTPException(status_code=500, detail="seed_db.py not found")

    runpy.run_path(str(seed_path), run_name="__main__")
    return {"ok": True, "message": "bootstrap complete"}
