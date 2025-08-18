.PHONY: dev.setup gen.synth test test.all

dev.setup:
	pip install -e .[dev]
	pre-commit install

gen.synth:
	python -m tools.pbs_synth.cli --month $(MONTH) --base $(BASE) --fleet $(FLEET) --seed $(SEED) --out data/synth/$(MONTH)/

test:
	pytest -q fastapi_tests

test.all:
	pytest -q
