#!/bin/sh
set -e
cd /app

# 1) Schema first (foreground, short per-statement tx) so we never hold
#    AccessExclusiveLock while uvicorn is already serving traffic.
python - <<'PY'
import traceback
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import User

DDL = [
    "ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS image_url VARCHAR(512)",
    "ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS topic VARCHAR(64)",
    "CREATE INDEX IF NOT EXISTS ix_vocabulary_topic ON vocabulary (topic)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'user'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(32) DEFAULT 'free'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR(128)",
    "ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS coming_soon BOOLEAN DEFAULT false",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS lesson_type VARCHAR(32) DEFAULT 'dialogue_core'",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 12",
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS unlock_rule VARCHAR(32) DEFAULT 'sequential'",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS completed_step_keys JSON DEFAULT '[]'",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS item_results JSON",
    "ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
    "UPDATE users SET role = 'user' WHERE role IS NULL",
    "UPDATE users SET plan = 'free' WHERE plan IS NULL",
]

try:
    print("Creating tables...", flush=True)
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("SET lock_timeout = '3s'"))
        conn.execute(text("SET statement_timeout = '15s'"))
        for stmt in DDL:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"DDL skip/fail: {stmt[:60]}… ({exc})", flush=True)
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)"))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"Index skip: {exc}", flush=True)

    if settings.super_admin_email and settings.super_admin_password:
        db = SessionLocal()
        try:
            email = settings.super_admin_email.lower().strip()
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                db.add(
                    User(
                        email=email,
                        password_hash=hash_password(settings.super_admin_password),
                        display_name="Super Admin",
                        role="super_admin",
                        plan="unlimit",
                    )
                )
                db.commit()
                print(f"Created Super Admin: {email}", flush=True)
            elif (existing.role or "") != "super_admin":
                existing.role = "super_admin"
                existing.plan = existing.plan or "unlimit"
                db.add(existing)
                db.commit()
                print(f"Promoted Super Admin: {email}", flush=True)
        finally:
            db.close()
    print("Schema ready.", flush=True)
except Exception:
    traceback.print_exc()
    print("Schema bootstrap failed — API will still start", flush=True)
PY

# 2) Seed data in background (no DDL) so empty DBs fill without blocking API.
(
  sleep 2
  python - <<'PY' || true
import traceback
from app.core.database import SessionLocal
from app.models import Scenario, Vocabulary

try:
    db = SessionLocal()
    try:
        count = db.query(Vocabulary).count()
        print(f"Vocab rows: {count}", flush=True)
        if count == 0:
            print("Empty DB — auto-seeding...", flush=True)
            from app.routers.admin import _run_seed
            print("Auto-seed OK:", _run_seed(), flush=True)
        else:
            print(f"Scenarios: {db.query(Scenario).count()}", flush=True)
    finally:
        db.close()
except Exception:
    traceback.print_exc()
    print("Auto-seed failed — call POST /api/admin/bootstrap after deploy", flush=True)
PY
) &

# 3) Serve API (unbuffered logs).
export PYTHONUNBUFFERED=1
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
