# Deploy staging

## Option A — Docker Compose (API + DB)

```bash
export OPENAI_API_KEY=sk-...
docker compose up -d --build db api
docker compose exec api sh -c "pip install -q alembic && alembic upgrade head"  # if image has alembic
```

Seed từ máy host (DB publish `5433`):

```bash
DATABASE_URL=postgresql+psycopg2://hoctiengtrung:hoctiengtrung@localhost:5433/hoctiengtrung \
  PYTHONPATH=apps/api apps/api/.venv/Scripts/python scripts/seed_db.py
```

## Option B — Frontend on Vercel

1. Import repo, root directory `apps/web`
2. Env: `NEXT_PUBLIC_API_URL=https://your-api.example.com`
3. Deploy

## Smoke checklist

- [ ] `GET /health` → ok
- [ ] Register → Home shows streak/XP/missions
- [ ] Flashcard review awards XP
- [ ] Listening TTS + quiz
- [ ] Work scenario roleplay returns scores (or demo scores without API key)
