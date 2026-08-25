#!/bin/sh
set -e
cd /app

python - <<'PY'
import traceback

from app.core.database import Base, SessionLocal, engine
from app.models import Scenario, Vocabulary

print("Creating tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    count = db.query(Vocabulary).count()
    print(f"Vocab rows: {count}")
    if count == 0:
        print("Empty DB — auto-seeding...")
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
