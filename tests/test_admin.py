"""Tests for admin blueprint endpoints."""

import pytest
import json
import os
from pathlib import Path
from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def dummy_pdf():
    """Load dummy PDF file for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    pdf_path = fixtures_dir / "dummy_bid.pdf"
    with open(pdf_path, "rb") as f:
        return f.read()


def test_upload_bid_happy_path(client, dummy_pdf):
    """Test successful bid upload with correct token."""
    from io import BytesIO
    from models import BidPacket
    from extensions import db

    # Clean up any existing test data
    existing = BidPacket.query.filter_by(month_tag="202508").first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    # Get admin token from environment
    admin_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")

    response = client.post(
        "/admin/upload-bid",
        data={"month_tag": "202508", "file": (BytesIO(dummy_pdf), "test_bid.pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert data["stored"] == "202508"

    # Verify file was saved to database
    bid_packet = BidPacket.query.filter_by(month_tag="202508").first()
    assert bid_packet is not None
    assert bid_packet.filename == "test_bid.pdf"
    assert bid_packet.file_size == len(dummy_pdf)
    assert bid_packet.pdf_data == dummy_pdf

    # Clean up
    db.session.delete(bid_packet)
    db.session.commit()


def test_upload_bid_bad_token(client, dummy_pdf):
    """Test upload with incorrect Bearer token returns 401."""
    from io import BytesIO

    response = client.post(
        "/admin/upload-bid",
        data={"month_tag": "202508", "file": (BytesIO(dummy_pdf), "test_bid.pdf")},
        headers={"Authorization": "Bearer wrongtoken"},
    )

    assert response.status_code == 401


def test_upload_bid_no_token(client, dummy_pdf):
    """Test upload without Authorization header returns 401."""
    from io import BytesIO

    response = client.post(
        "/admin/upload-bid",
        data={"month_tag": "202508", "file": (BytesIO(dummy_pdf), "test_bid.pdf")},
    )

    assert response.status_code == 401


def test_upload_bid_missing_month_tag(client, dummy_pdf):
    """Test upload without month_tag returns 400."""
    from io import BytesIO

    admin_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")

    response = client.post(
        "/admin/upload-bid",
        data={"file": (BytesIO(dummy_pdf), "test_bid.pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


def test_upload_bid_missing_file(client):
    """Test upload without file returns 400."""
    admin_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")

    response = client.post(
        "/admin/upload-bid",
        data={"month_tag": "202508"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400


def test_upload_bid_invalid_month_tag(client, dummy_pdf):
    """Test upload with invalid month_tag format returns 400."""
    from io import BytesIO

    admin_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")
    invalid_tags = ["2025", "20251", "2025123", "abc123", "202513"]

    for invalid_tag in invalid_tags:
        response = client.post(
            "/admin/upload-bid",
            data={
                "month_tag": invalid_tag,
                "file": (BytesIO(dummy_pdf), "test_bid.pdf"),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400, f"Failed for month_tag: {invalid_tag}"


def test_upload_bid_invalid_auth_format(client, dummy_pdf):
    """Test upload with invalid Authorization header format returns 401."""
    from io import BytesIO

    # Test various invalid formats
    invalid_headers = [
        "Basic dGVzdDp0ZXN0",  # Basic auth instead of Bearer
        "bearer test-token",  # lowercase 'bearer'
        "Bearer",  # Missing token
        "test-token",  # Missing 'Bearer' prefix
    ]

    for header in invalid_headers:
        response = client.post(
            "/admin/upload-bid",
            data={"month_tag": "202508", "file": (BytesIO(dummy_pdf), "test_bid.pdf")},
            headers={"Authorization": header},
        )

        assert response.status_code == 401, f"Failed for header: {header}"


def test_upload_bid_get_method_not_allowed(client):
    """Test GET request to upload endpoint returns 405."""
    admin_token = os.environ.get("ADMIN_BEARER_TOKEN", "test-token")

    response = client.get(
        "/admin/upload-bid", headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 405
