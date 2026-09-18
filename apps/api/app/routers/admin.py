"""One-shot bootstrap for free hosts (Render/Railway)."""

from __future__ import annotations

import importlib.util
import os
import traceback
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine
from app.models import Course, Lesson, Scenario, Vocabulary

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_bootstrap_secret(x_bootstrap_secret: str | None) -> None:
    expected = os.getenv("BOOTSTRAP_SECRET", "")
    if not expected or x_bootstrap_secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


def _scripts_dir() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        Path("/app/scripts"),
        here.parents[2] / "scripts",  # Docker: /app/app/routers -> /app/scripts
    ]
    if len(here.parents) >= 5:
        candidates.append(here.parents[4] / "scripts")  # local monorepo
    for path in candidates:
        if path.is_dir():
            return path
    raise FileNotFoundError(f"scripts/ not found; tried: {[str(c) for c in candidates]}")


def _run_script(filename: str) -> None:
    """Load scripts/<filename> and call main()."""
    path = _scripts_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    mod_name = f"seed_mod_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot load {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "main"):
        raise RuntimeError(f"{filename} has no main()")
    mod.main()


def _find_seed_path() -> Path:
    return _scripts_dir() / "seed_db.py"


def _run_seed() -> dict:
    """Import and run seed against current DB settings."""
    seed_path = _find_seed_path()
    if not seed_path.exists():
        raise FileNotFoundError(f"seed_db.py not found at {seed_path}")

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


def _ensure_topic_column() -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS topic VARCHAR(64)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_vocabulary_topic ON vocabulary (topic)"))


@router.post("/bootstrap")
def bootstrap(x_bootstrap_secret: str | None = Header(default=None)):
    _require_bootstrap_secret(x_bootstrap_secret)

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


@router.post("/seed-pinyin-topics")
def seed_pinyin_topics(x_bootstrap_secret: str | None = Header(default=None)):
    """Rebuild 5 pinyin lessons + tag vocab topics. Free-tier friendly (no Shell)."""
    _require_bootstrap_secret(x_bootstrap_secret)

    try:
        _ensure_topic_column()
        _run_script("seed_pinyin_course.py")
        _run_script("tag_vocab_topics.py")

        db = SessionLocal()
        try:
            pinyin = db.query(Course).filter(Course.slug == "pinyin").first()
            lesson_count = (
                db.query(Lesson).filter(Lesson.course_id == pinyin.id).count() if pinyin else 0
            )
            tagged = db.query(Vocabulary).filter(Vocabulary.topic.isnot(None)).count()
            return {
                "ok": True,
                "message": "pinyin course + vocab topics seeded",
                "pinyin_lessons": lesson_count,
                "vocab_tagged": tagged,
                "vocab_total": db.query(Vocabulary).count(),
            }
        finally:
            db.close()
    except Exception as exc:
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
            }
        finally:
            db.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
