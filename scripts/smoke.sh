#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-3000}"

# ensure no stale server
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

python -m uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!
trap "kill $PID" EXIT
sleep 3

if curl -fsS "http://localhost:$PORT/api/meta/health" >/dev/null; then
  echo "smoke OK (meta/health) on $PORT"
  exit 0
fi

curl -fsS "http://localhost:$PORT/" >/dev/null
echo "smoke OK (/) on $PORT"
