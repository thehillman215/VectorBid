# VectorBid

AI-powered PBS 2.0 bidding assistant for airline pilots.

## Current Status
- **Main branches**: `main` (stable), `staging` (integration)
- **Work baselines**: `cursor/baseline` (primary), `codex/baseline` (parallel)
- **Replit**: paused. Use Cursor + Line for primary dev.

## Workflow (solo)
1) Branch from `cursor/baseline` for features.
2) Open PR → `staging`. CI must be green (ruff, pytest, bandit, Docker build).
3) Periodically PR `staging` → `main` (protected).

## CI
- Lint/Format: `ruff check`, `ruff format --check`
- Tests: `pytest -q`
- Security: `bandit -r .`
- Docker: GHCR tags `build-<branch>-<sha7>`

Docs live in `docs/`:
- ARCHITECTURE.md, DATA_CONTRACTS.md, UI_FLOWS.md
- GIT_WORKFLOW.md, RULE_PACKS.md, LEGACY.md

## E2E Demo with Fixtures
1. Seed sample data: `python scripts/load_fixture.py`
2. Start the server: `python start_server.py`
3. Visit `http://localhost:<port>` and explore the demo pilot profile.

_Last updated: 2025-08-18_
