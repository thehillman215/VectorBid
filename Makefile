.PHONY: dev.setup lint test smoke.api run.api
PY=python3
VENV=.venv

dev.setup:
	$(PY) -m venv $(VENV) && . $(VENV)/bin/activate && pip -q install -r requirements.txt

lint:
	. $(VENV)/bin/activate && ruff check . && mypy app || true

test:
	. $(VENV)/bin/activate && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

smoke.api:
	. $(VENV)/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run.api: smoke.api
