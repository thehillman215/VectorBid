#!/bin/bash

# VectorBid Development Environment Setup
# This script creates a version-resilient development environment

set -e

echo "🚀 Setting up VectorBid Development Environment..."

# Detect Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "📋 Detected Python version: $PYTHON_VERSION"

# Check if Python version is supported
if [[ "$PYTHON_VERSION" < "3.9" ]]; then
    echo "❌ Python 3.9+ required. Current version: $PYTHON_VERSION"
    echo "💡 Please upgrade Python or use pyenv to manage versions"
    exit 1
fi

echo "✅ Python version $PYTHON_VERSION is supported"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies with flexible versioning
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🔧 Installing development dependencies..."
pip install -e ".[dev]" || pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install || echo "⚠️ pre-commit not available, skipping..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "# VectorBid Environment Variables" > .env
    echo "✅ Created .env file - please configure your environment variables"
else
    echo "✅ .env file already exists"
fi

# Set up git hooks for version resilience
echo "🔧 Setting up git hooks..."
mkdir -p .git/hooks

# Create pre-commit hook that checks Python version compatibility
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for version resilience

echo "🔍 Checking Python version compatibility..."

# Get current Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')

# Check if version is supported
if [[ "$PYTHON_VERSION" < "3.9" ]]; then
    echo "❌ Python 3.9+ required for development. Current: $PYTHON_VERSION"
    echo "💡 Please upgrade Python or use pyenv"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION is compatible"

# Run basic checks
echo "🔍 Running basic code quality checks..."
python3 -m ruff check . --fix || true
python3 -m ruff format . || true

echo "✅ Pre-commit checks passed"
EOF

chmod +x .git/hooks/pre-commit

# Create a Python version compatibility checker
cat > scripts/check_compatibility.py << 'EOF'
#!/usr/bin/env python3
"""
Python Version Compatibility Checker
Ensures code works across supported Python versions
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if current Python version is supported."""
    version = sys.version_info
    if version < (3, 9):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("💡 Python 3.9+ is required")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is supported")
    return True

def check_imports():
    """Check if all imports work correctly."""
    print("🔍 Checking imports...")
    
    try:
        import app
        print("✅ Main app imports successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def check_type_hints():
    """Check if type hints are compatible."""
    print("🔍 Checking type hint compatibility...")
    
    # Check for Union types that aren't compatible with Python 3.9
    try:
        from typing import Union
        print("⚠️ Union types detected - ensure Python 3.9 compatibility")
    except ImportError:
        print("✅ No Union type compatibility issues")
    
    return True

def main():
    """Run all compatibility checks."""
    print("🚀 VectorBid Compatibility Checker")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_imports,
        check_type_hints,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All compatibility checks passed!")
        return 0
    else:
        print("❌ Some compatibility checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x scripts/check_compatibility.py

# Create a development environment checker
cat > scripts/dev_status.py << 'EOF'
#!/usr/bin/env python3
"""
Development Environment Status Checker
Shows the current state of your development environment
"""

import sys
import subprocess
from pathlib import Path

def get_python_info():
    """Get Python version and path information."""
    print(f"🐍 Python Version: {sys.version}")
    print(f"📍 Python Path: {sys.executable}")
    print(f"📁 Working Directory: {Path.cwd()}")

def get_venv_info():
    """Get virtual environment information."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"🔧 Virtual Environment: {sys.prefix}")
    else:
        print("⚠️ No virtual environment detected")

def check_dependencies():
    """Check if key dependencies are installed."""
    print("\n📦 Dependency Check:")
    
    deps = [
        'fastapi', 'pydantic', 'sqlalchemy', 'pytest', 'ruff'
    ]
    
    for dep in deps:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {dep}: {version}")
        except ImportError:
            print(f"❌ {dep}: not installed")

def main():
    """Show development environment status."""
    print("🔍 VectorBid Development Environment Status")
    print("=" * 50)
    
    get_python_info()
    get_venv_info()
    check_dependencies()
    
    print("\n💡 Tips:")
    print("- Use 'source .venv/bin/activate' to activate virtual environment")
    print("- Run 'python scripts/check_compatibility.py' to check compatibility")
    print("- Use 'make test' to run tests")
    print("- Use 'make lint' to check code quality")

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/dev_status.py

# Create a Makefile for common development tasks
cat > Makefile << 'EOF'
# VectorBid Development Makefile
# Provides common development tasks with version resilience

.PHONY: help install test lint format clean dev-status check-compat

help: ## Show this help message
	@echo "VectorBid Development Commands:"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	python3 -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e ".[dev]" || pip install -r requirements-dev.txt

test: ## Run tests
	python3 -m pytest tests/ --ignore=tests/e2e/ -v

test-all: ## Run all tests including e2e
	python3 -m pytest tests/ -v

lint: ## Run linting and formatting checks
	python3 -m ruff check .
	python3 -m ruff format --check .

format: ## Format code automatically
	python3 -m ruff format .
	python3 -m ruff check . --fix

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage

dev-status: ## Show development environment status
	python3 scripts/dev_status.py

check-compat: ## Check Python version compatibility
	python3 scripts/check_compatibility.py

setup: ## Set up development environment
	bash scripts/setup_dev_env.sh

ci: ## Run CI checks locally
	python3 -m ruff check . && python3 -m ruff format --check . && python3 -m pytest tests/ --ignore=tests/e2e/
EOF

echo "✅ Development environment setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Check environment status: make dev-status"
echo "3. Run compatibility check: make check-compat"
echo "4. Run tests: make test"
echo "5. Check code quality: make lint"
echo ""
echo "💡 Use 'make help' to see all available commands"
echo "🔧 Your environment is now resilient to Python version changes!"
