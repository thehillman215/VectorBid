#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
try:
    import uvicorn  # noqa: F401
except Exception:
    import sys, subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "uvicorn>=0.29"])
PY
PORT="${PORT:-3000}"

# ensure no stale server
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true

python -m uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!
trap "kill $PID" EXIT
sleep 3

curl -fsS "http://localhost:$PORT/ping" >/dev/null
curl -fsS "http://localhost:$PORT/health" >/dev/null
echo "smoke OK on $PORT"
