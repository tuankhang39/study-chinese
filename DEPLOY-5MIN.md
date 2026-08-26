# Deploy free ~5 phút

## Cách nhanh nhất (khuyên dùng)

```
Vercel (web)  +  Render (API + Postgres free/starter)
```

### Phút 1–2: Push GitHub

1. Tạo repo trống trên github.com (private OK)
2. Trong thư mục project:

```bash
git init
git add .
git commit -m "MVP deploy free"
git branch -M main
git remote add origin https://github.com/YOUR_USER/hoctiengtrung.git
git push -u origin main
```

### Phút 3: Render API

1. Vào https://dashboard.render.com → **New** → **Blueprint**
2. Connect repo → chọn `render.yaml`
3. Điền env khi hỏi:
   - `CORS_ORIGINS` = tạm `*` hoặc để sau
   - `OPENAI_API_KEY` = để trống nếu chưa có
   - `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` = tài khoản Super Admin (tạo lúc boot)
   - Google (tuỳ chọn): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI=https://YOUR-API.onrender.com/api/auth/google/callback`, `WEB_APP_URL=https://xxx.vercel.app`
4. Deploy → copy URL API, vd `https://hoctiengtrung-api.onrender.com`

5. Seed dữ liệu (1 lần):

```bash
curl -X POST https://YOUR-API.onrender.com/api/admin/bootstrap \
  -H "X-Bootstrap-Secret: GIÁ_TRỊ_BOOTSTRAP_SECRET_TRONG_RENDER"
```

Admin UI: `https://xxx.vercel.app/admin` (đăng nhập Super Admin).

(Lấy `BOOTSTRAP_SECRET` trong Render → Environment)

Kiểm tra: `https://YOUR-API.onrender.com/health`

> Free Render **spin down** khi idle ~15 phút — request đầu có thể chậm 30–60s.

### Phút 4–5: Vercel Web

1. https://vercel.com/new → Import GitHub repo
2. **Root Directory** = `apps/web`
3. Env:

```
NEXT_PUBLIC_API_URL=https://YOUR-API.onrender.com
```

4. Deploy → nhận URL `https://xxx.vercel.app`

5. Quay Render → sửa `CORS_ORIGINS`:

```
https://xxx.vercel.app,http://localhost:3001
```

Redeploy API.

### Xong

Gửi team: `https://xxx.vercel.app`

---

## Chỉ deploy Web trước (2 phút) — API vẫn tunnel local

Nếu muốn có link Vercel ngay, API vẫn máy bạn:

```bash
cd apps/web
# .env.local đã có NEXT_PUBLIC_API_URL=https://...loca.lt
npx vercel login
npx vercel --yes
npx vercel --prod --yes
```

Team vào Vercel URL; API chỉ sống khi máy bạn bật tunnel.

---

## Checklist

- [ ] GitHub pushed
- [ ] Render API `/health` = ok
- [ ] Bootstrap seed xong
- [ ] Vercel `NEXT_PUBLIC_API_URL` đúng
- [ ] CORS có domain Vercel
- [ ] Đăng ký user trên bản deploy
