#!/usr/bin/env python3
"""
API test script for VectorBid endpoints.

This script tests the various API endpoints to verify they work correctly
according to the OpenAPI specification.
"""

import os
import sys

import requests


def test_home_page(base_url):
    """Test the home page endpoint."""
    print("🏠 Testing home page...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Home page accessible")
            return True
        else:
            print(f"❌ Home page returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Home page error: {e}")
        return False


def test_admin_upload_auth(base_url):
    """Test admin upload endpoint authentication."""
    print("🔒 Testing admin authentication...")

    # Test without auth
    try:
        response = requests.post(f"{base_url}/admin/upload-bid", timeout=10)
        if response.status_code == 401:
            print("✅ Correctly rejects requests without auth")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth test error: {e}")
        return False

    # Test with wrong auth
    try:
        headers = {"Authorization": "Bearer wrongtoken"}
        response = requests.post(f"{base_url}/admin/upload-bid", headers=headers, timeout=10)
        if response.status_code == 401:
            print("✅ Correctly rejects invalid tokens")
            return True
        else:
            print(f"❌ Expected 401 for invalid token, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")
        return False


def test_admin_upload_with_valid_token(base_url):
    """Test admin upload with valid token (if available)."""
    print("📤 Testing admin upload with valid token...")

    admin_token = os.environ.get("ADMIN_BEARER_TOKEN")
    if not admin_token:
        print("⚠️  ADMIN_BEARER_TOKEN not available, skipping upload test")
        return True

    # Create a dummy PDF file for testing
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n%EOF"

    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        files = {"file": ("test.pdf", dummy_pdf, "application/pdf")}
        data = {"month_tag": "202512"}  # Use December 2025 as test month

        response = requests.post(
            f"{base_url}/admin/upload-bid",
            headers=headers,
            files=files,
            data=data,
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok" and result.get("stored") == "202512":
                print("✅ Admin upload successful")
                return True
            else:
                print(f"❌ Unexpected response: {result}")
                return False
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False


def test_invalid_endpoints(base_url):
    """Test endpoints that should return errors."""
    print("🚫 Testing invalid endpoints...")

    # Test non-existent endpoint
    try:
        response = requests.get(f"{base_url}/nonexistent", timeout=10)
        if response.status_code == 404:
            print("✅ Correctly returns 404 for non-existent endpoint")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 404 test error: {e}")
        return False

    # Test wrong method on admin endpoint
    try:
        response = requests.get(f"{base_url}/admin/upload-bid", timeout=10)
        if response.status_code == 405:
            print("✅ Correctly returns 405 for wrong HTTP method")
            return True
        else:
            print(f"❌ Expected 405, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Method test error: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 VectorBid API Testing Suite")
    print("=" * 40)

    # Determine base URL
    base_url = os.environ.get("TEST_BASE_URL", "http://localhost:5000")
    print(f"🌐 Testing against: {base_url}")

    # Run tests
    tests = [
        test_home_page,
        test_admin_upload_auth,
        test_admin_upload_with_valid_token,
        test_invalid_endpoints,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func(base_url):
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
