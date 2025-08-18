"""Pytest configuration and fixtures for VectorBid tests."""

import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402

# Import the SQLAlchemy instance from the core extensions
from main import app  # noqa: E402


@pytest.fixture
def test_app():
    """Create and configure a test Flask application."""
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["ADMIN_BEARER_TOKEN"] = "test-admin-token"

    with app.app_context():
        yield app


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    """Create a test CLI runner for the Flask application."""
    return test_app.test_cli_runner()
