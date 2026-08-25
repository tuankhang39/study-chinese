#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pkill -f "cloudflared tunnel --url" 2>/dev/null || true
rm -f "$ROOT/.tunnel-urls"
echo "Tunnels stopped."
