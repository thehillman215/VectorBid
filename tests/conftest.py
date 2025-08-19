"""
Pytest configuration and fixtures for VectorBid tests.

This file provides common fixtures and utilities for all tests,
enabling Test-Driven Development (TDD) approach.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import yaml
import json

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_rule_pack():
    """Sample rule pack data for testing."""
    return {
        "version": "2025.08",
        "airline": "UAL",
        "id": "UAL-2025-08",
        "far117": {
            "min_rest_hours": 10,
            "hard": [
                {
                    "id": "FAR117_MIN_REST",
                    "desc": "Rest >= 10h",
                    "check": "pairing.rest_hours >= 10"
                }
            ],
            "soft": [
                {
                    "id": "FAR117_SOFT_DUTY_LIMIT",
                    "desc": "Prefer duty time under 14h",
                    "weight": 0.3,
                    "score": "pairing.duty_hours <= 14 ? 1.0 : 0.7"
                }
            ]
        },
        "union": {
            "max_duty_hours_per_day": 16,
            "hard": [
                {
                    "id": "NO_REDEYE_IF_SET",
                    "when": "pref.hard_constraints.no_red_eyes",
                    "check": "pairing.redeye == false"
                }
            ],
            "soft": [
                {
                    "id": "PREFER_LAYOVER_CITY",
                    "weight": "pref.soft_prefs.layovers.weight",
                    "score": "city in pref.soft_prefs.layovers.prefer ? 1.0 : (city in pref.soft_prefs.layovers.avoid ? 0.0 : 0.5)"
                }
            ]
        },
        "rules": []
    }


@pytest.fixture
def temp_rule_pack_file(sample_rule_pack):
    """Create a temporary rule pack file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_rule_pack, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def sample_preference_schema():
    """Sample pilot preference schema for testing."""
    return {
        "rest_preferences": ["10h min rest", "prefer layovers"],
        "pairing_preferences": ["commutable trips", "no red eyes"],
        "days_off": ["weekends", "Mondays"],
        "aircraft_type": "B737",
        "base": "ORD",
        "seniority": 15
    }


@pytest.fixture
def mock_health_response():
    """Expected health endpoint response structure."""
    return {
        "status": "ok",
        "service": "VectorBid FastAPI",
        "version": "1.0.0",
        "timestamp": "2025-01-27T00:00:00Z"
    }


@pytest.fixture
def mock_ping_response():
    """Expected ping endpoint response structure."""
    return {
        "ping": "pong",
        "timestamp": "2025-01-27T00:00:00Z"
    }


@pytest.fixture
def rule_packs_directory():
    """Get the rule packs directory path."""
    return Path("rule_packs")


@pytest.fixture
def test_data_directory():
    """Get the test data directory path."""
    return Path("tests/fixtures")


@pytest.fixture
def sample_bid_layer():
    """Sample bid layer data for testing."""
    return {
        "id": "test-layer-001",
        "name": "Weekend Preference Layer",
        "description": "Prioritize weekends off",
        "rules": [
            {
                "id": "WEEKEND_OFF",
                "type": "hard",
                "condition": "day_of_week in ['Saturday', 'Sunday']",
                "action": "exclude"
            }
        ],
        "priority": 1,
        "active": True
    }


class RulePackValidator:
    """Utility class for validating rule pack structures."""
    
    @staticmethod
    def validate_required_fields(rule_pack: dict) -> list:
        """Validate required fields in rule pack."""
        required_fields = ["version", "airline", "id"]
        missing_fields = []
        
        for field in required_fields:
            if field not in rule_pack:
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def validate_version_format(version: str) -> bool:
        """Validate version string format (YYYY.MM)."""
        import re
        pattern = r'^\d{4}\.\d{2}$'
        return bool(re.match(pattern, version))
    
    @staticmethod
    def validate_airline_code(airline: str) -> bool:
        """Validate airline code format (3 letters)."""
        import re
        pattern = r'^[A-Z]{3}$'
        return bool(re.match(pattern, airline))


@pytest.fixture
def rule_pack_validator():
    """Rule pack validator utility fixture."""
    return RulePackValidator()


class HealthChecker:
    """Utility class for health endpoint testing."""
    
    @staticmethod
    def check_response_structure(response: dict, expected_keys: list) -> bool:
        """Check if response has expected structure."""
        return all(key in response for key in expected_keys)
    
    @staticmethod
    def check_response_types(response: dict, type_spec: dict) -> bool:
        """Check if response values have expected types."""
        for key, expected_type in type_spec.items():
            if key in response:
                if not isinstance(response[key], expected_type):
                    return False
        return True


@pytest.fixture
def health_checker():
    """Health checker utility fixture."""
    return HealthChecker()


# Test markers for different test categories
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "health: marks tests as health endpoint tests"
    )
    config.addinivalue_line(
        "markers", "rulepacks: marks tests as rule pack tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "rules_engine: marks tests as rules engine tests"
    )
    config.addinivalue_line(
        "markers", "dsl: marks tests as DSL parser tests"
    )
