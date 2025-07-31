"""E2E test configuration and fixtures."""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application during testing."""
    return "http://localhost:5000"

@pytest.fixture(scope="session") 
def mock_user_headers():
    """Mock user headers for Replit authentication."""
    return {"X-Replit-User-Id": "test_user_e2e"}

@pytest.fixture(scope="session")
def mock_admin_headers():
    """Mock admin headers with bearer token."""
    return {
        "Authorization": "Bearer test_admin_token",
        "Content-Type": "application/json"
    }

@pytest.fixture(autouse=True)
def clear_user_profile():
    """Clear test user profile before each test."""
    try:
        from services.db import save_profile
        # Reset test user profile
        save_profile("test_user_e2e", {
            "onboard_complete": False,
            "profile_completed": False,
            "airline": None,
            "base": None,
            "seat": None,
            "fleet": [],
            "seniority": None
        })
    except Exception:
        # Ignore if database is not available
        pass