#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-3000}"

# start FastAPI
python -m uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!
trap "kill $PID" EXIT

# give it a moment to boot
sleep 3

# probe endpoints (meta/health first; ping second if present)
curl -fsS "http://localhost:$PORT/api/meta/health" >/dev/null
# optional: curl -fsS "http://localhost:$PORT/api/ping" >/dev/null

echo "smoke OK on port $PORT"
