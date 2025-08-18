# VectorBid

## State of the repo
- Minimal FastAPI service exposing /ping and /health.
- UAL rule packs live in `rule_packs/` and validate via Pydantic.
- Tiny rule engine checks FAR117_MIN_REST and NO_REDEYE_IF_SET.
- CLI `vb` handles rule utilities.
- Tests reside in `fastapi_tests/` and drive CI.

## Quickstart
1. `pip install -e .[dev]`
2. `ruff check .` && `ruff format --check .`
3. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -c pytest.ini`
4. `scripts/smoke.sh`
5. `vb rules validate rule_packs/UAL/2025.08.yml`

