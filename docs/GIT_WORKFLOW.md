# Git Workflow

## Branching
- `main` — stable production branch.
- `staging` — integration branch (merged feature work).
- `codex/baseline`, `repl/baseline` — AI-assisted experiment branches.

## Flow
1. Feature branch off `staging`.
2. Run CI (ruff lint/format, pytest, bandit, Docker build).
3. Merge into `staging` after checks pass.
4. Periodically fast-forward `main`.

## CI Checks
- `ruff check` + `ruff format`.
- `pytest -q` (fast suite).
- `bandit -r .` security scan.
- Docker build & push to GHCR.