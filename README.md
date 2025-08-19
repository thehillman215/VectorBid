# VectorBid

AI-powered PBS 2.0 bidding assistant for airline pilots. A FastAPI-based application with intelligent rule processing and schedule optimization.

## Quick Start

### Development Setup
```bash
# Clone and setup environment
git clone https://github.com/thehillman215/VectorBid-codex.git
cd VectorBid-codex
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt requirements-dev.txt

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure
```
VectorBid-codex/
├── app/                    # 🚀 FastAPI application (PRIMARY)
│   ├── main.py            # Application entry point
│   ├── api/               # API routes and endpoints
│   ├── rules_engine/      # Rules engine implementation
│   ├── services/          # Business logic services
│   └── models.py          # Data models
├── tests/                  # 🧪 Test suite
├── fastapi_tests/          # FastAPI-specific tests
├── rule_packs/            # Rule pack definitions (YAML)
├── tools/                  # CLI tools and utilities
├── docs/                   # 📚 Documentation
└── pyproject.toml         # Project configuration
```

## Development

### Workflow
1) Branch from `cursor/baseline` for features
2) Open PR → `staging`. CI must be green (ruff, pytest, bandit, Docker build)
3) Periodically PR `staging` → `main` (protected)

### Commands
```bash
# Development
uvicorn app.main:app --reload

# Testing
pytest tests/ -v
pytest fastapi_tests/ -v

# Code Quality
ruff check app/ --fix
ruff format app/
bandit -r app/

# Build
docker build -t vectorbid .
```

### API Endpoints
- **Health**: `GET /health` - Service health check
- **API Docs**: `GET /docs` - Interactive Swagger UI
- **Rule Validation**: `POST /api/validate` - Validate preferences
- **Schedule Optimization**: `POST /api/optimize` - Optimize schedule

## Architecture

- **FastAPI Backend**: Modern Python web framework with automatic OpenAPI docs
- **Rules Engine**: YAML-based rule packs with DSL parser for safety
- **Schedule Optimization**: AI-powered preference matching and scoring
- **Export System**: Multiple output formats for various PBS systems

## Documentation

See `docs/` directory:
- `DEVELOPER_QUICKSTART.md` - Getting started guide
- `ARCHITECTURE.md` - Technical architecture
- `RULE_PACKS.md` - Rule pack documentation  
- `GIT_WORKFLOW.md` - Development workflow

_Last updated: 2025-08-19_
