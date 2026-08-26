"""One-shot bootstrap for free hosts (Render/Railway)."""

from __future__ import annotations

import os
import traceback
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException

from app.core.database import Base, SessionLocal, engine
from app.models import Scenario, Vocabulary

router = APIRouter(prefix="/admin", tags=["admin"])


def _find_seed_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        Path("/app/scripts/seed_db.py"),
        here.parents[2] / "scripts" / "seed_db.py",  # Docker: /app/app/routers -> /app/scripts
    ]
    if len(here.parents) >= 5:
        candidates.append(here.parents[4] / "scripts" / "seed_db.py")  # local monorepo
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"seed_db.py not found; tried: {[str(c) for c in candidates]}")


def _run_seed() -> dict:
    """Import and run seed against current DB settings."""
    import importlib.util

    seed_path = _find_seed_path()

    spec = importlib.util.spec_from_file_location("seed_db_mod", seed_path)
    if not spec or not spec.loader:
        raise RuntimeError("Cannot load seed_db module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Skip writing license file on read-only containers
        v = mod.seed_vocab(db)
        s = mod.seed_scenarios(db)
        total = db.query(Vocabulary).count()
        scenarios = db.query(Scenario).count()
        return {
            "vocab_added": v,
            "scenarios_added": s,
            "vocab_total": total,
            "scenarios_total": scenarios,
        }
    finally:
        db.close()


@router.post("/bootstrap")
def bootstrap(x_bootstrap_secret: str | None = Header(default=None)):
    expected = os.getenv("BOOTSTRAP_SECRET", "")
    if not expected or x_bootstrap_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        Base.metadata.create_all(bind=engine)
        result = _run_seed()
        return {"ok": True, "message": "bootstrap complete", **result}
    except Exception as exc:
        # Return detail so Render logs / client can debug without SSH
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "type": type(exc).__name__,
                "trace": traceback.format_exc()[-2000:],
            },
        ) from exc


@router.get("/stats")
def stats():
    """Public-ish health for seed status (no secret)."""
    try:
        db = SessionLocal()
        try:
            return {
                "vocab": db.query(Vocabulary).count(),
                "scenarios": db.query(Scenario).count(),
                "with_images": db.query(Vocabulary)
                .filter(Vocabulary.image_url.isnot(None))
                .count(),
            }
        finally:
            db.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
