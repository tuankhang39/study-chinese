#!/bin/sh
set -e
cd /app
python - <<'PY'
from app.core.database import Base, SessionLocal, engine
from app.models import Vocabulary, Scenario

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if db.query(Vocabulary).count() == 0:
        print("Empty DB — run seed from host or /api/admin/bootstrap once")
    else:
        print(f"Vocab rows: {db.query(Vocabulary).count()}, scenarios: {db.query(Scenario).count()}")
finally:
    db.close()
PY
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
