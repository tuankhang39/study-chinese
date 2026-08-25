# Deploy test nội bộ (miễn phí ~$0)

Mục tiêu: team/friends truy cập qua URL, không cần AWS, không tốn phí (free tier).

```
Vercel (free)     →  apps/web
Railway (free)    →  apps/api + PostgreSQL
```

Thời gian setup: ~30 phút.

---

## Bước 1 — Đẩy code lên GitHub

```bash
git init
git add .
git commit -m "MVP tieng trung di lam"
# Tạo repo private trên GitHub, rồi:
git remote add origin https://github.com/YOUR_USER/hoctiengtrung.git
git push -u origin main
```

Repo **private** là đủ cho test nội bộ.

---

## Bước 2 — Railway: API + Database

1. Vào [railway.app](https://railway.app) → New Project → **Deploy from GitHub**
2. Chọn repo `hoctiengtrung`
3. **Add service → Database → PostgreSQL**
4. **Add service → GitHub repo** → Settings:
   - **Root Directory:** `apps/api`
   - **Dockerfile Path:** `Dockerfile`
5. Variables (service API):

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET=doi-sang-chuoi-ngau-nhien-dai-32-ky-tu
CORS_ORIGINS=https://YOUR-APP.vercel.app,http://localhost:3000,http://localhost:3001
OPENAI_API_KEY=sk-...   # optional, không có thì roleplay chạy demo
```

6. Railway Postgres dùng URL dạng `postgresql://...` — app tự convert sang `postgresql+psycopg2://` nếu cần (xem note bên dưới).

7. **Generate Domain** cho API service → copy URL, vd: `https://hoctiengtrung-api.up.railway.app`

8. Chạy migration + seed (Railway CLI hoặc one-off):

```bash
npm i -g @railway/cli
railway login
railway link
railway run --service api alembic upgrade head
# Seed (từ máy local, trỏ DATABASE_URL public của Railway):
DATABASE_URL="postgresql+psycopg2://..." PYTHONPATH=apps/api python scripts/seed_db.py
```

Kiểm tra: `curl https://YOUR-API.up.railway.app/health` → `{"status":"ok"}`

---

## Bước 3 — Vercel: Frontend

1. [vercel.com](https://vercel.com) → Add New Project → Import GitHub repo
2. **Root Directory:** `apps/web`
3. Environment Variable:

```
NEXT_PUBLIC_API_URL=https://YOUR-API.up.railway.app
```

4. Deploy → URL dạng `https://hoctiengtrung.vercel.app`

5. Quay lại Railway → cập nhật `CORS_ORIGINS` thêm URL Vercel thật → redeploy API.

---

## Bước 4 — Test nội bộ

Gửi team 2 link:

- **App:** `https://hoctiengtrung.vercel.app`
- **API docs:** `https://YOUR-API.up.railway.app/docs`

Checklist:

- [ ] Đăng ký tài khoản mới
- [ ] Home hiện streak / nhiệm vụ
- [ ] Flashcard ôn được
- [ ] Roleplay chạy (demo hoặc OpenAI)

---

## Giới hạn free tier (đủ test nội bộ)

| Service | Free | Lưu ý |
|---|---|---|
| Vercel | Hobby $0 | Preview deploy mỗi PR |
| Railway | ~$5 credit/tháng | Sleep khi idle, đủ vài người test |
| Neon (thay Railway DB) | 0.5GB free | Alternative nếu Railway hết credit |

---

## Plan B — Tunnel share local (nhanh nhất, $0)

Dung khi chua muon push GitHub. Can **may ban bat** + docker + next dev.

### Yeu cau truoc

```bash
docker compose up -d          # API :8001
cd apps/web && npm run dev -- --port 3001
```

### Cach 1 — Script tu dong

Terminal **1** (git bash):

```bash
bash scripts/tunnel-start.sh
```

Script se:
1. Mo tunnel API (8001) va Web (3001)
2. Cap nhat CORS + `apps/web/.env.local`
3. In **link share** ra man hinh

Sau do **restart Next.js** (bat buoc):

```bash
# Terminal 2 — Ctrl+C roi chay lai
cd apps/web && npm run dev -- --port 3001
```

Gui team link dang `https://xxxx.loca.lt`

Dung tunnel:

```bash
bash scripts/tunnel-stop.sh
```

**Luu y:** Lan dau vao link localtunnel co the hoi "Click to continue" — binh thuong.

### Cach 2 — Thu cong (2 terminal)

**Terminal A — API:**

```bash
npx localtunnel --port 8001
# Copy URL, vd: https://abc123.loca.lt
```

**Terminal B — Web:**

```bash
npx localtunnel --port 3001
# Copy URL share cho team, vd: https://xyz789.loca.lt
```

**Cap nhat env:**

```bash
# apps/web/.env.local
NEXT_PUBLIC_API_URL=https://abc123.loca.lt

# Restart next dev, roi:
CORS_ORIGINS=https://xyz789.loca.lt,http://localhost:3001 docker compose up -d api --force-recreate
```

### Cach 3 — Cloudflare Tunnel (on dinh hon)

```bash
winget install Cloudflare.cloudflared
# Terminal A
cloudflared tunnel --url http://127.0.0.1:8001
# Terminal B
cloudflared tunnel --url http://127.0.0.1:3001
```

Lam tuong tu: API URL → `.env.local`, Web URL → `CORS_ORIGINS`, restart next dev.

---

## Plan C — 1 VPS / EC2 noi bo cong ty

```bash
docker compose -f docker-compose.yml up -d --build
# Mở port nội bộ VPN hoặc IP private
```

Phí ~0 nếu dùng máy công ty; không public internet.
