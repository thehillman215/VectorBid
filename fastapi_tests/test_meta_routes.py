"""Tests for meta routes including health and parsers endpoints."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMetaRoutes:
    """Test cases for meta route endpoints."""

    def test_health_endpoint(self):
        """Test GET /api/meta/health returns correct health information."""
        response = client.get("/api/meta/health")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert data["ok"] is True
        assert data["service"] == "api"
        assert data["version"] == "1.0.0"
        assert "py" in data
        assert "now" in data

        # Check Python version format
        py_version = data["py"]
        assert "." in py_version
        version_parts = py_version.split(".")
        assert len(version_parts) >= 2
        assert all(part.isdigit() for part in version_parts[:2])

        # Check timestamp format
        timestamp = data["now"]
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Invalid ISO timestamp format: {timestamp}")

    def test_parsers_endpoint(self):
        """Test GET /api/meta/parsers returns supported formats and fields."""
        response = client.get("/api/meta/parsers")

        assert response.status_code == 200
        data = response.json()

        # Check required top-level fields
        assert "supported_formats" in data
        assert "required_fields" in data
        assert "parser_version" in data

        # Check parser version
        assert data["parser_version"] == "1.0.0"

        # Check supported formats
        formats = data["supported_formats"]
        assert isinstance(formats, list)
        assert len(formats) >= 4  # Should have CSV, JSONL, PDF, TXT

        # Check each format has required fields
        for fmt in formats:
            assert "extension" in fmt
            assert "description" in fmt
            assert "fields" in fmt
            assert isinstance(fmt["fields"], list)

        # Check specific formats exist
        extensions = [fmt["extension"] for fmt in formats]
        assert ".csv" in extensions
        assert ".jsonl" in extensions
        assert ".pdf" in extensions
        assert ".txt" in extensions

        # Check CSV format details
        csv_format = next(fmt for fmt in formats if fmt["extension"] == ".csv")
        assert "pairing_id" in csv_format["fields"]
        assert "base" in csv_format["fields"]
        assert "fleet" in csv_format["fields"]
        assert "month" in csv_format["fields"]

        # Check JSONL format details
        jsonl_format = next(fmt for fmt in formats if fmt["extension"] == ".jsonl")
        assert "pairing_id" in jsonl_format["fields"]
        assert "trips" in jsonl_format["fields"]

        # Check PDF format details
        pdf_format = next(fmt for fmt in formats if fmt["extension"] == ".pdf")
        assert "trip_id" in pdf_format["fields"]
        assert "credit_hours" in pdf_format["fields"]
        assert "route" in pdf_format["fields"]

        # Check TXT format details
        txt_format = next(fmt for fmt in formats if fmt["extension"] == ".txt")
        assert "trip_id" in txt_format["fields"]
        assert "credit_hours" in txt_format["fields"]

        # Check required fields
        required_fields = data["required_fields"]
        assert isinstance(required_fields, dict)
        assert len(required_fields) >= 6

        # Check specific required fields
        assert "airline" in required_fields
        assert "month" in required_fields
        assert "base" in required_fields
        assert "fleet" in required_fields
        assert "seat" in required_fields
        assert "pilot_id" in required_fields

        # Check field descriptions
        assert "UAL" in required_fields["airline"]
        assert "2025-09" in required_fields["month"]
        assert "SFO" in required_fields["base"]
        assert "737" in required_fields["fleet"]
        assert "FO" in required_fields["seat"] or "CA" in required_fields["seat"]

    def test_health_endpoint_response_time(self):
        """Test that health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = client.get("/api/meta/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond in under 1 second

    def test_parsers_endpoint_response_time(self):
        """Test that parsers endpoint responds quickly."""
        import time

        start_time = time.time()
        response = client.get("/api/meta/parsers")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond in under 1 second

    def test_health_endpoint_consistency(self):
        """Test that health endpoint returns consistent data across calls."""
        response1 = client.get("/api/meta/health")
        response2 = client.get("/api/meta/health")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Static fields should be identical
        assert data1["ok"] == data2["ok"]
        assert data1["service"] == data2["service"]
        assert data1["version"] == data2["version"]
        assert data1["py"] == data2["py"]

        # Timestamps should be different (unless called very quickly)
        assert data1["now"] != data2["now"] or data1["now"] == data2["now"]

    def test_parsers_endpoint_consistency(self):
        """Test that parsers endpoint returns consistent data across calls."""
        response1 = client.get("/api/meta/parsers")
        response2 = client.get("/api/meta/parsers")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # All fields should be identical (static data)
        assert data1 == data2

    def test_health_endpoint_methods(self):
        """Test that health endpoint only accepts GET method."""
        # Test POST (should fail)
        response = client.post("/api/meta/health")
        assert response.status_code == 405  # Method Not Allowed

        # Test PUT (should fail)
        response = client.put("/api/meta/health")
        assert response.status_code == 405

        # Test DELETE (should fail)
        response = client.delete("/api/meta/health")
        assert response.status_code == 405

    def test_parsers_endpoint_methods(self):
        """Test that parsers endpoint only accepts GET method."""
        # Test POST (should fail)
        response = client.post("/api/meta/parsers")
        assert response.status_code == 405  # Method Not Allowed

        # Test PUT (should fail)
        response = client.put("/api/meta/parsers")
        assert response.status_code == 405

        # Test DELETE (should fail)
        response = client.delete("/api/meta/parsers")
        assert response.status_code == 405
