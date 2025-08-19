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

## Conventional Commits
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `docs:` - Documentation changes (README, architecture, etc.)
- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks, dependencies, etc.
- `style:` - Code style changes (formatting, etc.)
- `perf:` - Performance improvements

### Examples:
```
docs: expand architecture with data flow diagram
feat: add /ping and /health endpoints
test: create rule pack loading test scaffold
fix: resolve linting errors in admin dashboard
```

## Development Workflow

### 1. Feature Development
```bash
# Start from cursor/baseline
git checkout cursor/baseline
git pull origin cursor/baseline

# Create feature branch
git checkout -b feature/docs-architecture

# Make changes and commit
git add .
git commit -m "docs: expand architecture documentation"

# Push and create PR
git push origin feature/docs-architecture
```

### 2. Code Quality Standards
- **Formatting**: Use `ruff format .` for consistent code style
- **Linting**: Run `ruff check .` to catch issues
- **Type Checking**: Ensure mypy compliance where applicable
- **Testing**: Maintain >90% test coverage

### 3. PR Requirements
- **Title**: Follow conventional commit format
- **Description**: Clear explanation of changes and rationale
- **Tests**: All tests must pass
- **Linting**: No ruff or bandit violations
- **Dependencies**: Update requirements.txt if needed

## CI Rules
- Formatting enforced (`ruff format --check .`)
- Security scan (`bandit -r .`)
- Docker images pushed to GHCR with sanitized tags:
  - `ghcr.io/thehillman215/vectorbid:build-<branch>-<sha7>`

## Branch Naming Convention
- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `docs/<description>` - Documentation updates
- `test/<description>` - Test-related changes
- `refactor/<description>` - Code refactoring

## Release Process
1. **Feature Freeze**: All features merged to `staging`
2. **Testing**: Comprehensive testing on staging environment
3. **Release Branch**: Create `release/vX.Y.Z` from `staging`
4. **Final Testing**: Validate release candidate
5. **Merge to Main**: PR `release/vX.Y.Z` → `main`
6. **Tag Release**: Create git tag `vX.Y.Z`

## Notes
- Replit paused. Use Cursor. Keep both baselines aligned with `main`.
- Always rebase feature branches before merging to avoid merge conflicts
- Use squash merges for feature PRs to maintain clean history
- Keep commit messages clear and descriptive
