# VectorBid

## VectorBid FastAPI (v0.3) — Quickstart

Run (dev):
  pip install -r requirements-dev.txt
  scripts/dev_run.sh
  # http://localhost:8000/health
  # http://localhost:8000/docs

Endpoints:
  GET /health, GET /schemas
  POST /parse_preferences, /validate, /optimize, /strategy, /generate_layers, /lint

Tests:
  PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -c pytest.ini

Legacy:
  Mounted at /legacy if WSGI app importable; else shim at /legacy/health

Benchmark helper:
  PYTHONPATH=. python scripts/bench_10k.py
