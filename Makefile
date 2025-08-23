# VectorBid Development Automation - Enforces Testing Discipline
.PHONY: dev.setup lint test smoke.api run.api functional-test status reality-check install-hooks enforce

PY=python3
VENV=.venv

# Original targets
dev.setup:
	$(PY) -m venv $(VENV) && . $(VENV)/bin/activate && pip -q install -r requirements.txt

lint:
	. $(VENV)/bin/activate && ruff check . && mypy app || true

test:
	. $(VENV)/bin/activate && PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

smoke.api:
	. $(VENV)/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run.api: smoke.api

# NEW: Functional testing enforcement
functional-test:
	@echo "🧪 Running VectorBid functional tests..."
	@echo "🚨 REQUIRED before any completion claims"
	@if ! curl -s http://localhost:8001/health > /dev/null; then \
		echo "❌ Server not running. Start with: uvicorn app.main:app --reload --port 8001"; \
		exit 1; \
	fi
	$(PY) scripts/test-before-claim.py
	@echo "📋 Results saved to TEST_RESULTS.md - use for honest status updates"

# Generate realistic status based on functional tests
status: functional-test
	@echo "📊 VectorBid Reality Check Status:"
	@if [ -f TEST_RESULTS.md ]; then \
		grep -A 5 "## Status Assessment" TEST_RESULTS.md; \
	else \
		echo "❌ Run 'make functional-test' first"; \
	fi

# Full development environment with reality check
dev-reality:
	@echo "🚀 Starting VectorBid with reality check..."
	uvicorn app.main:app --reload --port 8001 &
	sleep 5
	$(MAKE) functional-test
	@echo "✅ Environment ready - check TEST_RESULTS.md for honest status"

# Install git hooks to prevent optimistic commits
install-hooks:
	@echo "🔧 Installing testing enforcement hooks..."
	chmod +x scripts/test-before-claim.py
	chmod +x scripts/pre-commit-test.py
	cp scripts/pre-commit-test.py .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "✅ Hooks installed - commits will be blocked if they contain unsubstantiated completion claims"

# Complete reality check audit
reality-check:
	@echo "🔎 VectorBid Complete Reality Check"
	@echo "==================================="
	@echo "Git status:"
	@git status --short
	@echo ""
	@echo "Recent commits:"
	@git log --oneline -3
	@echo ""
	@if curl -s http://localhost:8001/health > /dev/null; then \
		echo "✅ Server running - running functional tests..."; \
		$(MAKE) functional-test; \
	else \
		echo "❌ Server not running - start with 'make smoke.api' first"; \
	fi

# Show enforcement rules
enforce:
	@echo "⚖️  VectorBid Development Rules - ENFORCED BY AUTOMATION"
	@echo "========================================================"
	@echo ""
	@echo "🚨 BEFORE claiming features work:"
	@echo "   1. Start server: make smoke.api (port 8001)"
	@echo "   2. Run tests: make functional-test"
	@echo "   3. Use TEST_RESULTS.md for status updates"
	@echo ""
	@echo "🔍 Git hooks will block commits with:"
	@echo "   - '99% complete' without test evidence"
	@echo "   - '✅ working' without API test results"
	@echo "   - Status files missing test dates/evidence"
	@echo ""
	@echo "📋 Override only with: git commit --no-verify"
	@echo "   (But you shouldn't need to if you test first)"

# Show help
help:
	@echo "VectorBid Development Commands:"
	@echo "=============================="
	@echo "make functional-test  - 🧪 Test actual functionality (REQUIRED)"
	@echo "make status          - 📊 Show realistic completion status"
	@echo "make reality-check   - 🔎 Full system audit"
	@echo "make install-hooks   - 🔧 Install git enforcement hooks"
	@echo "make dev-reality     - 🚀 Start dev with reality check"
	@echo "make enforce         - ⚖️  Show enforcement rules"
	@echo ""
	@echo "Original commands:"
	@echo "make smoke.api       - Start development server"
	@echo "make test           - Unit tests"
	@echo "make lint           - Code quality checks"
