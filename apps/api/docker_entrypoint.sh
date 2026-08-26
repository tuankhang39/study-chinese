#!/bin/sh
set -e
cd /app

# Start API immediately. Schema/seed runs in background WITHOUT holding
# open transactions across ALTER (that deadlocks /api/home).
(
  sleep 1
  python - <<'PY' || true
import traceback
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Course, Scenario, User, Vocabulary

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS image_url VARCHAR(512)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'user'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(32) DEFAULT 'free'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR(128)"))
        conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
        conn.execute(text("ALTER TABLE courses ADD COLUMN IF NOT EXISTS coming_soon BOOLEAN DEFAULT false"))
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS lesson_type VARCHAR(32) DEFAULT 'dialogue_core'"))
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 12"))
        conn.execute(text("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS unlock_rule VARCHAR(32) DEFAULT 'sequential'"))
        conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS completed_step_keys JSON DEFAULT '[]'"))
        conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS item_results JSON"))
        conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ"))
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)"))
        except Exception:
            pass
        conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
        conn.execute(text("UPDATE users SET plan = 'free' WHERE plan IS NULL"))

    # Bootstrap Super Admin from env (once)
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
                print(f"Created Super Admin: {email}")
            elif (existing.role or "") != "super_admin":
                existing.role = "super_admin"
                existing.plan = existing.plan or "unlimit"
                db.add(existing)
                db.commit()
                print(f"Promoted Super Admin: {email}")
        finally:
            db.close()

    db = SessionLocal()
    try:
        count = db.query(Vocabulary).count()
        print(f"Vocab rows: {count}")
        if count == 0:
            print("Empty DB — auto-seeding...")
            from app.routers.admin import _run_seed

            print("Auto-seed OK:", _run_seed())
        else:
            print(f"Scenarios: {db.query(Scenario).count()}")
    finally:
        db.close()
except Exception:
    traceback.print_exc()
    print("Auto-seed failed — call POST /api/admin/bootstrap after deploy")
PY
) &

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
