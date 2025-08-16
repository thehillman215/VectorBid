#!/usr/bin/env bash
set -euo pipefail
pats='uvicorn|app\.main:app|watchfiles|watchgod|StatReload|python.*uvicorn'

# Find candidate PIDs
mapfile -t pids < <(ps -ef | grep -E "$pats" | grep -v grep | awk '{print $2}')

if [ ${#pids[@]} -gt 0 ]; then
  echo "Killing: ${pids[*]}"
  kill -9 "${pids[@]}" || true
else
  echo "No matching uvicorn/reloader processes."
fi

# Show listeners for common ports (if ss is available)
if command -v ss >/dev/null 2>&1; then
  echo "Listeners:"
  ss -ltnp | grep -E ':8050|:8077' || true
fi
