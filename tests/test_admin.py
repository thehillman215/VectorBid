"""Tests for admin blueprint endpoints."""
import pytest
import json
import os
from pathlib import Path
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def dummy_pdf():
    """Load dummy PDF file for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    pdf_path = fixtures_dir / "dummy_bid.pdf"
    with open(pdf_path, 'rb') as f:
        return f.read()


def test_upload_bid_happy_path(client, dummy_pdf, tmp_path):
    """Test successful bid upload with correct token."""
    # Create temporary bids directory for this test
    bids_dir = tmp_path / "bids"
    bids_dir.mkdir()
    
    # Mock the bids directory by changing working directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        from io import BytesIO
        response = client.post(
            '/admin/upload-bid?token=letmein',
            data={
                'month_tag': '202508',
                'file': (BytesIO(dummy_pdf), 'test_bid.pdf')
            }
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert data['stored'] == '202508'
        
        # Verify file was saved
        saved_file = bids_dir / "bid_202508.pdf"
        assert saved_file.exists()
        assert len(saved_file.read_bytes()) > 0
        
    finally:
        os.chdir(original_cwd)


def test_upload_bid_bad_token(client, dummy_pdf):
    """Test upload with incorrect token returns 403."""
    from io import BytesIO
    response = client.post(
        '/admin/upload-bid?token=wrongtoken',
        data={
            'month_tag': '202508',
            'file': (BytesIO(dummy_pdf), 'test_bid.pdf')
        }
    )
    
    assert response.status_code == 403


def test_upload_bid_no_token(client, dummy_pdf):
    """Test upload without token returns 403."""
    from io import BytesIO
    response = client.post(
        '/admin/upload-bid',
        data={
            'month_tag': '202508',
            'file': (BytesIO(dummy_pdf), 'test_bid.pdf')
        }
    )
    
    assert response.status_code == 403


def test_upload_bid_missing_month_tag(client, dummy_pdf):
    """Test upload without month_tag returns 400."""
    from io import BytesIO
    response = client.post(
        '/admin/upload-bid?token=letmein',
        data={
            'file': (BytesIO(dummy_pdf), 'test_bid.pdf')
        }
    )
    
    assert response.status_code == 400


def test_upload_bid_missing_file(client):
    """Test upload without file returns 400."""
    response = client.post(
        '/admin/upload-bid?token=letmein',
        data={
            'month_tag': '202508'
        }
    )
    
    assert response.status_code == 400


def test_upload_bid_invalid_month_tag(client, dummy_pdf):
    """Test upload with invalid month_tag format returns 400."""
    from io import BytesIO
    invalid_tags = ['2025', '20251', '2025123', 'abc123', '202513']
    
    for invalid_tag in invalid_tags:
        response = client.post(
            '/admin/upload-bid?token=letmein',
            data={
                'month_tag': invalid_tag,
                'file': (BytesIO(dummy_pdf), 'test_bid.pdf')
            }
        )
        
        assert response.status_code == 400, f"Failed for month_tag: {invalid_tag}"


def test_upload_bid_get_method_not_allowed(client):
    """Test GET request to upload endpoint returns 405."""
    response = client.get('/admin/upload-bid?token=letmein')
    
    assert response.status_code == 405