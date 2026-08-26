#!/bin/sh
set -e
cd /app

python - <<'PY'
import traceback

from app.core.database import Base, SessionLocal, engine
from app.models import Scenario, Vocabulary

print("Creating tables...")
Base.metadata.create_all(bind=engine)

# Ensure columns added after initial deploy (create_all won't ALTER)
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS image_url VARCHAR(512)"))

db = SessionLocal()
try:
    count = db.query(Vocabulary).count()
    print(f"Vocab rows: {count}")
    missing_images = (
        db.query(Vocabulary).filter(Vocabulary.image_url.is_(None)).count() if count else 0
    )
    if count == 0 or missing_images > 50:
        print("Seeding / backfilling vocab images...")
        try:
            from app.routers.admin import _run_seed

            result = _run_seed()
            print("Auto-seed OK:", result)
        except Exception:
            traceback.print_exc()
            print("Auto-seed failed — call POST /api/admin/bootstrap after deploy")
    else:
        print(f"Scenarios: {db.query(Scenario).count()}")
finally:
    db.close()
PY

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
