# VectorBid

🚀 **World's First AI-Powered Pilot Bidding System** - Transform pilot scheduling from complex form-filling to intelligent conversation.

AI-powered pilot bidding assistant for airline pilots. A FastAPI-based application with intelligent rule processing, schedule optimization, and natural language preference parsing.

## ✨ Latest Features
- 🎨 **Professional Marketing Pages** - Complete landing page with interactive demo
- 🔐 **Authentication System** - Signup/login with demo accounts  
- 📊 **Data Flow Visualization** - Interactive D3.js architecture diagram
- 🤖 **Live API Integration** - Real backend connectivity for demos
- 📱 **Mobile-First Design** - Responsive across all devices (via Cursor AI)
- ⚡ **Performance Optimized** - Fast loading with intelligent caching (via Cursor AI)
- ♿ **Fully Accessible** - WCAG 2.1 AA compliant (via Cursor AI)
- 🧪 **Comprehensive Testing** - Automated CI/CD pipeline (via Cursor AI)

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
