# Testing Guide

This document outlines VectorBid's testing strategy, tools, and best practices.

## Spec-Driven vs Test-Driven Development

We adopt a hybrid approach:

**Spec-Driven Development (SDD)**
- Pros: Locks scope; enables parallel work; stable APIs and JSON/Pydantic schemas; easier mocks and docs; fewer integration surprises.
- Cons: Specs can drift from reality; up-front effort; risk of over-design if requirements are fuzzy.

**Test-Driven Development (TDD)**
- Pros: Forces small, verifiable steps; fast feedback; prevents regressions; improves design via testability; useful for bug fixes and tricky logic.
- Cons: Slower at start; fragile if tests target internals; hard without a clear contract.

**VectorBid recommendation**
- Use SDD for contracts and interfaces (PreferenceSchema, CandidateSchedule, BidLayerArtifact, REST endpoints, rule-pack inputs/outputs, error codes).
- Use TDD for complex or brittle behavior (PDF/parser, rules engine legality checks, optimizer scoring/weights, linter auto-fixes, export pipeline, bug reproduction).

**Minimal Workflow**
1. Write or update the spec (JSON Schema/Pydantic + example fixtures).
2. Add contract tests (round-trip validate → serialize) and golden/approval examples.
3. For each change inside a module, write failing unit test → implement → refactor.
4. Gate with CI: schema validation, unit tests, and a small smoke test that boots FastAPI.

This hybrid keeps interfaces stable while letting us iterate safely on core logic.

## Test Suite Overview

### Test Structure
```
tests/
├── e2e/           # End-to-end tests
├── legacy/        # Legacy test compatibility
├── fixtures/      # Test data and fixtures
└── parsers/       # Parser-specific tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/ -v
pytest tests/e2e/ -v
pytest tests/legacy/ -v

# Run tests in watch mode (requires pytest-watch)
pytest-watch

# Run specific test file
pytest tests/test_health.py -v

# Run tests with specific markers
pytest -m "not slow" -v
```

### Test Quality

```bash
# Linting
ruff check .
ruff format --check .

# Security scan
bandit -r app/

# Clear pytest cache
pytest --cache-clear

# Run tests with verbose output
pytest -v -s
```

## Test Categories

### Unit Tests
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Focus on edge cases and error conditions

### Integration Tests
- Test interactions between components
- Use real database connections and external services
- Validate end-to-end workflows

### Contract Tests
- Validate JSON Schema and Pydantic models
- Ensure round-trip serialization works
- Test API endpoint contracts

### Golden Tests
- Use known good data fixtures
- Validate against expected outputs
- Prevent regressions in data processing

## Best Practices

1. **Test Naming**: Use descriptive test names that explain the scenario
2. **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and verification
3. **Fixtures**: Use pytest fixtures for common test data and setup
4. **Mocks**: Mock external dependencies to isolate the code under test
5. **Coverage**: Aim for high test coverage, especially for critical paths
6. **Fast Tests**: Keep tests fast to enable quick feedback loops
