# Git Workflow

## Branches
- `main`: stable, protected
- `staging`: integration, target for feature PRs
- `cursor/baseline`: primary dev baseline (Cursor + Line)
- `codex/baseline`: parallel AI-assisted baseline

## Flow
1. Create feature branches from `cursor/baseline`.
2. PR → `staging` (CI: ruff, pytest, bandit, Docker).
3. When ready, PR `staging` → `main` (merge commit).

## CI Rules
- Formatting enforced (`ruff format --check .`)
- Security scan (`bandit -r .`)
- Docker images pushed to GHCR with sanitized tags:
  - `ghcr.io/thehillman215/vectorbid:build-<branch>-<sha7>`

## Notes
- Replit paused. Use Cursor. Keep both baselines aligned with `main`.
