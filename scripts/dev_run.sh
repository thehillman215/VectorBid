#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=.
exec uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000} --reload-dir app --reload-exclude uploads --reload-exclude exports
