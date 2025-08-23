"""Tests for the ingestion route."""

import io

import pytest
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
            "pilot_id": "pilot_001",
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
            "pilot_id": "pilot_001",
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

        files = {
            "file": (
                "test.jsonl",
                io.BytesIO(jsonl_content.encode()),
                "application/jsonl",
            )
        }
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "CA",
            "pilot_id": "pilot_002",
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result

    def test_ingest_pdf_mock_content(self):
        """Test PDF ingestion with mock content (expected to fail gracefully)."""
        pdf_content = b"%PDF-1.4\n%Mock PDF content"

        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "DEN",
            "fleet": "787",
            "seat": "FO",
            "pilot_id": "pilot_003",
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Mock PDF content should fail with graceful error handling
        assert response.status_code == 400
        result = response.json()
        assert "Failed to parse PDF" in result["detail"]

    def test_ingest_missing_file(self):
        """Test ingestion with missing file."""
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001",
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
            "pilot_id": "pilot_001",
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Should fail with empty file
        assert response.status_code == 400
        result = response.json()
        assert "Empty file" in result["detail"]

    def test_ingest_unsupported_format(self):
        """Test ingestion with unsupported file format."""
        files = {
            "file": (
                "test.doc",
                io.BytesIO(b"Mock Word document"),
                "application/msword",
            )
        }
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "SFO",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_001",
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
            "pilot_id": "pilot_001",
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "summary" in result

    def test_ingest_golden_csv_data(self):
        """Test ingestion with actual golden CSV data."""
        # Create a simple CSV file that matches our parser expectations
        combined_csv = b"pairing_id,base,fleet,month\n"
        combined_csv += b"EWR-73N-001,EWR,73N,2025-09-01\n"
        combined_csv += b"trip_id,pairing_id,day,origin,destination\n"
        combined_csv += b"EWR-73N-001-T1,EWR-73N-001,5,DEN,EWR\n"
        combined_csv += b"EWR-73N-001-T2,EWR-73N-001,3,LAX,EWR\n"

        files = {"file": ("golden_combined.csv", io.BytesIO(combined_csv), "text/csv")}
        data = {
            "airline": "UAL",
            "month": "2025-09",
            "base": "EWR",
            "fleet": "73N",
            "seat": "FO",
            "pilot_id": "pilot_golden",
        }

        response = client.post("/api/ingest", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["summary"]["trips"] == 2
        assert result["summary"]["pairings"] == 1
        assert "EWR" in result["summary"]["bases"]
        assert result["summary"]["fleet"] == "73N"

    def test_ingest_pdf_real_file(self):
        """Test ingestion with actual PDF from bids/ directory."""
        from pathlib import Path

        # Use the bid_202513.pdf file if it exists
        pdf_path = Path(__file__).parent.parent / "bids" / "bid_202513.pdf"

        if not pdf_path.exists():
            pytest.skip("bid_202513.pdf not found for integration testing")

        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        files = {"file": ("bid_202513.pdf", pdf_content, "application/pdf")}
        data = {
            "airline": "UAL",
            "month": "2025-02",
            "base": "DEN",
            "fleet": "737",
            "seat": "FO",
            "pilot_id": "pilot_pdf_test",
        }

        response = client.post("/api/ingest", files=files, data=data)

        # Should handle gracefully (either success or well-formatted error)
        assert response.status_code in [200, 400]
        result = response.json()

        if response.status_code == 200:
            # If successful, verify response structure
            assert result["success"] is True
            assert "summary" in result
            assert "trips" in result["summary"]
            assert "pairings" in result["summary"]
            assert "package_id" in result["summary"]
        else:
            # If parsing failed (status 400), should have proper error message
            assert "detail" in result
            assert (
                "Failed to parse PDF" in result["detail"]
                or "No trips found" in result["detail"]
                or "extract text" in result["detail"]
            )
