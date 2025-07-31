"""Pytest configuration and fixtures for VectorBid tests."""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

# Import the main app instance and database
from main import app
from app import db


@pytest.fixture
def test_app():
    """Create and configure a test Flask application."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["ADMIN_BEARER_TOKEN"] = "test-admin-token"
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    """Create a test CLI runner for the Flask application."""
    return test_app.test_cli_runner()