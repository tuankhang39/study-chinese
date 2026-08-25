# Tiếng Trung đi làm

MVP: học tiếng Trung cho người Việt — **từ vựng HSK** + **tình huống đi làm** (AI roleplay).

## Stack

- `apps/web` — Next.js 15 + TypeScript + Tailwind
- `apps/api` — FastAPI + SQLAlchemy + Alembic + FSRS
- PostgreSQL 16 (Docker)

## Chạy local

```bash
# 1) Database
docker compose up -d db

# 2) API
cd apps/api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=.
alembic upgrade head
cd ../..
PYTHONPATH=apps/api apps/api/.venv/Scripts/python scripts/seed_db.py
cd apps/api
.venv\Scripts\uvicorn app.main:app --reload --port 8001

# 3) Web
cd apps/web
npm install
npm run dev
```

Mở http://localhost:3000 — API http://localhost:8001/docs

Postgres map ra host **5433** (tránh conflict 5432). API mặc định **8001**.

## Biến môi trường

`apps/api/.env`:

- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`
- `OPENAI_API_KEY` (optional — không có thì roleplay chạy demo mock)

`apps/web/.env.local`:

- `NEXT_PUBLIC_API_URL=http://localhost:8001`

## Dữ liệu từ vựng

Seed từ [Complete HSK Vocabulary](https://github.com/drkameleon/complete-hsk-vocabulary) (MIT) — HSK 2.0 levels 1–3 (~600 từ) + từ nghề nghiệp. Nghĩa tiếng Việt trong `data/vi_meanings.json` (bổ sung dần).

## Deploy staging

- Frontend: Vercel (`apps/web`), set `NEXT_PUBLIC_API_URL`
- API + DB: `docker compose up -d` trên VPS / Railway / Fly

Xem `DEPLOY.md`.
