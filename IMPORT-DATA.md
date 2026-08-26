# Mang data lên máy deploy (không push Git)

## Đã seed trong DB local

| Bảng | Số lượng |
|------|----------|
| courses | 6 (HSK1 published + HSK2–6 coming_soon) |
| lessons | 15 (HSK1) |
| lesson_steps | ~106 |
| lesson_items | 976 (đã có pinyin) |
| vocabulary | 603 |
| scenarios | 5 |
| lesson_vocab | 188 |

File dump: `backups/hoctiengtrung_seed.dump` (~182KB)

Ảnh cover / “xem sách” còn lại: `data/curriculum/hsk1/pages/page_*.jpg` (87 trang, đã xóa OCR/PDF/draft).

## Trên máy deploy

### 1) Import Postgres

```bash
# Docker compose trong repo
docker compose up -d db
docker compose exec -T db pg_restore -U hoctiengtrung -d hoctiengtrung --clean --if-exists --no-owner --no-acl < backups/hoctiengtrung_seed.dump
```

Hoặc copy file vào container rồi restore:

```bash
docker cp backups/hoctiengtrung_seed.dump hoctiengtrung-db-1:/tmp/seed.dump
docker compose exec db pg_restore -U hoctiengtrung -d hoctiengtrung --clean --if-exists --no-owner --no-acl /tmp/seed.dump
```

### 2) Copy media (ảnh trang)

```bash
# Giữ đúng path API đang mount
# docker-compose: ./data/curriculum → /app/data/curriculum
rsync -av data/curriculum/ deploy-host:/path/to/hoctiengtrung/data/curriculum/
```

### 3) Không cần seed lại từ PDF/OCR

PDF + OCR + `lessons_draft.json` đã xóa sau khi seed. Nội dung học nằm trong DB dump.
