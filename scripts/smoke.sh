#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
UVICORN_CMD="uvicorn app.main:app --host 127.0.0.1 --port ${PORT} --log-level warning"

# start API
$UVICORN_CMD > uvicorn.log 2>&1 &
PID=$!

# wait for health
python - <<'PY'
import time, urllib.request, sys, os
port = int(os.getenv("PORT","8080"))
for _ in range(60):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/meta/health", timeout=1) as r:
            if r.status == 200:
                print("READY"); sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit("Server did not start")
PY

# smoke
curl -fsS "http://127.0.0.1:${PORT}/api/meta/health" | tee /dev/stderr

# stop API
kill -TERM "$PID" || true
sleep 1
pkill -f "uvicorn app.main:app" || true
