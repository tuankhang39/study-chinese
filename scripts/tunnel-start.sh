#!/usr/bin/env bash
# Share local app via localtunnel (internal test, no install)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_PORT="${API_PORT:-8001}"
WEB_PORT="${WEB_PORT:-3001}"
LOG_DIR="$ROOT/.tunnel-logs"
mkdir -p "$LOG_DIR"

echo "Checking local services..."
curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null || { echo "API not running on :${API_PORT}. Run: docker compose up -d"; exit 1; }
curl -sf "http://127.0.0.1:${WEB_PORT}/" >/dev/null || { echo "Web not running on :${WEB_PORT}. Run: cd apps/web && npm run dev -- --port ${WEB_PORT}"; exit 1; }

pkill -f "localtunnel --port ${API_PORT}" 2>/dev/null || true
pkill -f "localtunnel --port ${WEB_PORT}" 2>/dev/null || true
pkill -f "lt --port ${API_PORT}" 2>/dev/null || true
pkill -f "lt --port ${WEB_PORT}" 2>/dev/null || true
sleep 1

pick_url() {
  local log="$1"
  grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$log" | head -1
}

echo "Starting API tunnel :${API_PORT}..."
npx --yes localtunnel --port "$API_PORT" >"$LOG_DIR/api.log" 2>&1 &
sleep 8
API_URL=$(pick_url "$LOG_DIR/api.log" || true)
if [ -z "$API_URL" ]; then
  echo "Failed API tunnel. Log:"
  tail -15 "$LOG_DIR/api.log"
  exit 1
fi
echo "API tunnel: $API_URL"

echo "Starting Web tunnel :${WEB_PORT}..."
npx --yes localtunnel --port "$WEB_PORT" >"$LOG_DIR/web.log" 2>&1 &
sleep 8
WEB_URL=$(pick_url "$LOG_DIR/web.log" || true)
if [ -z "$WEB_URL" ]; then
  echo "Failed Web tunnel. Log:"
  tail -15 "$LOG_DIR/web.log"
  exit 1
fi
echo "Web tunnel: $WEB_URL"

echo "Updating API CORS..."
export CORS_ORIGINS="${WEB_URL},http://localhost:${WEB_PORT},http://127.0.0.1:${WEB_PORT}"
docker compose up -d api --force-recreate >/dev/null

echo "NEXT_PUBLIC_API_URL=${API_URL}" >"$ROOT/apps/web/.env.local"

cat >"$ROOT/.tunnel-urls" <<EOF
WEB_URL=${WEB_URL}
API_URL=${API_URL}
EOF

echo ""
echo "============================================"
echo "  SHARE LINK:"
echo "  ${WEB_URL}"
echo "============================================"
echo ""
echo "Lan dau vao co the hoi password tunnel — bam Continue."
echo "API: ${API_URL}"
echo ""
echo "BUOC CUOI: Restart Next.js (bat buoc):"
echo "  cd apps/web && npm run dev -- --port ${WEB_PORT}"
echo ""
echo "Dung tunnel: bash scripts/tunnel-stop.sh"
