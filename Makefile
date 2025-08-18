SHELL := /bin/bash

PY      ?= python3.11
VENV    ?= .venv
PYBIN   := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
PYTEST  := $(VENV)/bin/pytest
RUFF    := $(VENV)/bin/ruff
MYPY    := $(VENV)/bin/mypy
UVICORN := $(VENV)/bin/uvicorn

.PHONY: dev.setup lint format typecheck test test.all smoke.api gen.synth

dev.setup:
	@$(PY) -m venv $(VENV)
	@$(PIP) -q install -U pip setuptools wheel
	@test -f requirements.txt && $(PIP) -q install -r requirements.txt || true
	@test -f pre-commit-config.yaml && $(VENV)/bin/pre-commit install || true
	@echo "venv ready: $(VENV)"

lint:
	@$(RUFF) check .

format:
	@$(RUFF) format

typecheck:
	@$(MYPY) app || true

test:
	@PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTEST) -q

test.all:
	@PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTEST)

smoke.api:
	@set -euo pipefail; \
	$(UVICORN) app.main:app --port 8000 --log-level warning & pid=$$!; \
	sleep 1; \
	curl -fsS http://127.0.0.1:8000/api/meta/health || { kill $$pid; exit 1; }; \
	kill $$pid; wait $$pid 2>/dev/null || true; \
	echo "smoke OK"

# Requires Codex generator in tools/pbs_synth
MONTH ?= 2025-09
BASE  ?= EWR
FLEET ?= 73N
SEED  ?= 7
gen.synth:
	@$(PYBIN) -m tools.pbs_synth --month $(MONTH) --base $(BASE) --fleet $(FLEET) --seed $(SEED) --out data/synth/$(MONTH)/
