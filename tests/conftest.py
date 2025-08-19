"""Pytest configuration and fixtures for VectorBid tests."""

import pytest
from src.core.app import create_app
from src.core.extensions import db


@pytest.fixture(scope="session")
def app():
    """Create a test app instance."""
    app = create_app('testing')
    return app


@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the Flask app."""
    with app.app_context():
        with app.test_client() as client:
            # Set up database
            db.create_all()
            yield client
            # Clean up database
            db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.drop_all()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    from src.core.models import User
    
    user = User(
        id="test_user_123",
        email="test@example.com",
        name="Test User",
        airline="UAL",
        base="SFO",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_security_settings(db_session, sample_user):
    """Create sample security settings for testing."""
    from src.core.models import SecuritySettings
    
    settings = SecuritySettings(
        user_id=sample_user.id,
        two_factor_enabled=False
    )
    db_session.add(settings)
    db_session.commit()
    return settings
