# Developer Quickstart

This guide will get you up and running with VectorBid development in under 10 minutes.

> 💡 **Cost-Effective AI Development**: See [AI_DEVELOPMENT_STRATEGY.md](AI_DEVELOPMENT_STRATEGY.md) for the hybrid Claude Code + Cursor AI approach that maximizes your existing subscriptions.

## Prerequisites

- **Python 3.11+** (recommended: use pyenv or conda)
- **Git** (latest version)
- **Cursor IDE** (recommended) or VS Code
- **Docker** (optional, for containerized development)

## 1. Clone the Repository

```bash
git clone https://github.com/thehillman215/VectorBid-codex.git
cd VectorBid-codex
```

## 2. Set Up Python Environment

### Option A: Virtual Environment (Recommended)
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Option B: Conda
```bash
conda create -n vectorbid python=3.11
conda activate vectorbid
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 3. Install Development Tools

```bash
# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# Install additional dev tools
pip install ruff pytest pytest-cov bandit
```

## 4. Run the FastAPI Application

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the convenience script
python start_server.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Ping**: http://localhost:8000/ping

## 5. Run the Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/ -v
pytest tests/e2e/ -v
pytest tests/legacy/ -v

# Run linting
ruff check .
ruff format --check .

# Run security scan
bandit -r app/
```

## 6. Development Workflow

### Code Quality
```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Testing
```bash
# Run tests in watch mode (requires pytest-watch)
ptw

# Run specific test file
pytest tests/test_health.py -v

# Run tests with specific markers
pytest -m "not slow" -v
```

## 7. Project Structure

```
VectorBid-codex/
├── app/                    # Main FastAPI application
│   ├── api/               # API routes and endpoints
│   ├── models.py          # Pydantic data models
│   └── main.py            # FastAPI app entry point
├── docs/                  # Documentation
├── tests/                 # Test suite
│   ├── e2e/              # End-to-end tests
│   ├── legacy/            # Legacy test compatibility
│   └── fixtures/          # Test data and fixtures
├── rule_packs/            # YAML rule definitions
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

## 8. Key Endpoints

### Health & Monitoring
- `GET /health` - Application health status
- `GET /ping` - Simple ping response
- `GET /api/meta/health` - API health check

### Core API
- `POST /api/parse` - Parse pilot preferences
- `POST /api/validate` - Validate bid layers
- `POST /api/optimize` - Optimize bid strategies
- `POST /api/generate` - Generate PBS layers

## 9. Configuration

### Environment Variables
Create a `.env` file in the root directory:

```bash
# API Configuration
API_KEY=your_api_key_here
DEBUG=true
LOG_LEVEL=INFO

# Database (if using)
DATABASE_URL=sqlite:///./vectorbid.db

# External Services
OPENAI_API_KEY=your_openai_key_here
```

### IDE Setup (Cursor/VS Code)

#### Extensions
- Python
- Pylance
- Ruff
- Pytest
- GitLens

#### Settings
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

## 10. Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the virtual environment
which python
# Should show: /path/to/VectorBid-codex/venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

#### Test Failures
```bash
# Clear pytest cache
pytest --cache-clear

# Run tests with verbose output
pytest -v -s

# Check test dependencies
pip install pytest-cov pytest-mock
```

## 11. Next Steps

1. **Read the Architecture**: Review `docs/ARCHITECTURE.md`
2. **Understand the Workflow**: Check `docs/GIT_WORKFLOW.md`
3. **Explore the API**: Visit http://localhost:8000/docs
4. **Run Tests**: Ensure all tests pass
5. **Make Changes**: Start developing!

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: `/docs` directory
- **Code**: Follow the patterns in existing files

Happy coding! 🚀

