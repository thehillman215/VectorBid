"""Tests for the ingestion route."""

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestIngestRoute:
    """Test cases for POST /api/ingest endpoint."""

    def test_ingest_basic_functionality(self):
        """Test basic ingestion functionality without mocking."""
        files = {"file": ("test.csv", io.BytesIO(b"test"), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Should work and return a successful response
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result
        assert "package_id" in result["summary"]

    def test_ingest_csv_success(self):
        """Test successful CSV ingestion with golden data."""
        # Create a mock CSV file content
        csv_content = """pairing_id,base,fleet,month
EWR-73N-001,EWR,73N,2025-09-01"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "EWR",
            "fleet": "73N",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        # Test without mocking first to see if it works
        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result
        assert "package_id" in result["summary"]

    def test_ingest_jsonl_success(self):
        """Test successful JSONL ingestion."""
        jsonl_content = """{"pairing_id": "SFO-737-001", "base": "SFO", "fleet": "737", "month": "2025-09-01", "trips": []}"""

        files = {"file": ("test.jsonl", io.BytesIO(jsonl_content.encode()), "application/jsonl")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "CA",
            "pilot_id": "pilot_002"
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result

    def test_ingest_pdf_success(self):
        """Test successful PDF ingestion."""
        pdf_content = b"%PDF-1.4\n%Mock PDF content"

        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "DEN",
            "fleet": "787",
            "seat": "FO",
            "pilot_id": "pilot_003"
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result

    def test_ingest_missing_file(self):
        """Test ingestion with missing file."""
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        response = client.post("/api/ingest", data=data)

        assert response.status_code == 422  # Validation error

    def test_ingest_empty_file(self):
        """Test ingestion with empty file."""
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Should fail with empty file
        assert response.status_code == 400
        result = response.json()
        assert "Empty file" in result["detail"]

    def test_ingest_unsupported_format(self):
        """Test ingestion with unsupported file format."""
        files = {"file": ("test.doc", io.BytesIO(b"Mock Word document"), "application/msword")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Should fail with unsupported format
        assert response.status_code == 400
        result = response.json()
        assert "Unsupported file format" in result["detail"]

    def test_ingest_missing_required_fields(self):
        """Test ingestion with missing required fields."""
        files = {"file": ("test.csv", io.BytesIO(b"test"), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            # Missing base, fleet, seat, pilot_id
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 422  # Validation error

    def test_ingest_large_file(self):
        """Test ingestion with a large file."""
        # Create a 1MB file
        large_content = b"x" * (1024 * 1024)

        files = {"file": ("large.csv", io.BytesIO(large_content), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001"
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result
