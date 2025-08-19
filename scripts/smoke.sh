#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"
HOST="127.0.0.1"
APP="app.main:app"
LOG="uvicorn.log"

start_uvicorn() {
  python3.11 -m uvicorn "${APP}" --host "${HOST}" --port "${PORT}" --log-level warning > "${LOG}" 2>&1 &
  echo $! > uvicorn.pid
}

wait_ready() {
  python3.11 - <<'PY'
import os, time, urllib.request, sys, json
host="127.0.0.1"; port=int(os.getenv("PORT","8080"))
url=f"http://{host}:{port}/api/meta/health"
for i in range(60):
    try:
        with urllib.request.urlopen(url, timeout=1) as r:
            if r.status == 200:
                data=json.load(r)
                if isinstance(data, dict) and data.get("ok") is True:
                    print("READY")
                    sys.exit(0)
    except Exception:
        pass
    time.sleep(1)
print("FAILED TO START"); sys.exit(1)
PY
}

stop_uvicorn() {
  if [[ -f uvicorn.pid ]]; then
    kill -TERM "$(cat uvicorn.pid)" 2>/dev/null || true
    sleep 1
    pkill -f "uvicorn ${APP}" 2>/dev/null || true
    rm -f uvicorn.pid
  fi
}

trap 'echo "[trap] stopping"; stop_uvicorn' EXIT

start_uvicorn
wait_ready

# smoke probe
curl -fsS "http://${HOST}:${PORT}/api/meta/health" | tee /dev/stderr > /tmp/health.json

echo "[ok] smoke passed"
