#!/usr/bin/env bash
set -euo pipefail
# auto-load .env if present
set -a; [ -f ./.env ] && source ./.env; set +a
export PYTHONPATH=.
exec uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000} --reload-dir app --reload-exclude uploads --reload-exclude exports
