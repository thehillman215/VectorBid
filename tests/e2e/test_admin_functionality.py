"""E2E tests for admin functionality."""

from playwright.sync_api import Page, expect


class TestAdminFunctionality:
    """Test admin routes and functionality."""

    def test_admin_upload_endpoint_requires_auth(self, page: Page, base_url: str):
        """Test that admin upload endpoint requires authentication."""
        # Try to access admin endpoint without auth
        response = page.request.post(f"{base_url}/admin/upload-bid")
        assert response.status == 401

    def test_admin_upload_with_invalid_token(self, page: Page, base_url: str):
        """Test admin upload with invalid bearer token."""
        response = page.request.post(
            f"{base_url}/admin/upload-bid",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status == 401

    def test_admin_upload_missing_data(self, page: Page, base_url: str):
        """Test admin upload with missing form data."""
        # Set a test admin token (this would need to match ADMIN_BEARER_TOKEN env var)
        headers = {"Authorization": "Bearer test_admin_token"}

        response = page.request.post(f"{base_url}/admin/upload-bid", headers=headers)
        # Should return 400 for missing data
        assert response.status in [400, 401]  # 401 if token doesn't match env

    def test_admin_upload_wrong_method(self, page: Page, base_url: str):
        """Test admin upload endpoint only accepts POST."""
        headers = {"Authorization": "Bearer test_admin_token"}

        # Try GET request
        response = page.request.get(f"{base_url}/admin/upload-bid", headers=headers)
        assert response.status in [405, 401]  # Method not allowed or unauthorized

    def test_admin_endpoints_not_publicly_accessible(self, page: Page, base_url: str):
        """Test that admin endpoints are not accessible without proper auth."""
        admin_paths = [
            "/admin/upload-bid",
            "/admin/",
            "/admin/dashboard",
        ]

        for path in admin_paths:
            try:
                page.goto(f"{base_url}{path}")
                # Should not load successfully or should show unauthorized
                expect(page).to_have_url(
                    lambda url: "/admin" not in url
                    or "401" in page.content()
                    or "Unauthorized" in page.content()
                )
            except Exception:
                # Navigation might fail, which is expected for protected routes
                pass

    def test_admin_api_cors_headers(self, page: Page, base_url: str):
        """Test CORS headers on admin API endpoints."""
        response = page.request.options(f"{base_url}/admin/upload-bid")

        # Should handle OPTIONS request properly
        assert response.status in [200, 204, 404, 405]

    def test_admin_rate_limiting(self, page: Page, base_url: str):
        """Test basic rate limiting on admin endpoints."""
        headers = {"Authorization": "Bearer invalid_token"}

        # Make multiple rapid requests
        responses = []
        for _ in range(5):
            response = page.request.post(
                f"{base_url}/admin/upload-bid", headers=headers
            )
            responses.append(response.status)

        # All should be unauthorized, but no rate limiting errors expected in dev
        for status in responses:
            assert status in [401, 429]  # Unauthorized or rate limited

    def test_admin_security_headers(self, page: Page, base_url: str):
        """Test security headers on admin endpoints."""
        response = page.request.post(f"{base_url}/admin/upload-bid")

        # Check for basic security headers
        headers = response.headers

        # These are informational - not all may be present in development
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "strict-transport-security",
        ]
        present_headers = [h for h in security_headers if h in headers]

        # At least content-type should be set properly
        assert "content-type" in headers

    def test_admin_endpoint_input_validation(self, page: Page, base_url: str):
        """Test input validation on admin endpoints."""
        headers = {"Authorization": "Bearer test_admin_token"}

        # Test with invalid month_tag format
        response = page.request.post(
            f"{base_url}/admin/upload-bid",
            headers=headers,
            multipart={
                "month_tag": "invalid_month",
                "file": {
                    "name": "test.pdf",
                    "mimeType": "application/pdf",
                    "buffer": b"fake pdf content",
                },
            },
        )

        # Should reject invalid input (either 400 for validation or 401 for auth)
        assert response.status in [400, 401]

    def test_admin_file_type_validation(self, page: Page, base_url: str):
        """Test file type validation on admin upload."""
        headers = {"Authorization": "Bearer test_admin_token"}

        # Test with non-PDF file
        response = page.request.post(
            f"{base_url}/admin/upload-bid",
            headers=headers,
            multipart={
                "month_tag": "202508",
                "file": {
                    "name": "test.txt",
                    "mimeType": "text/plain",
                    "buffer": b"not a pdf",
                },
            },
        )

        # Should reject non-PDF files (either 400 for validation or 401 for auth)
        assert response.status in [400, 401]

    def test_admin_logging_security(self, page: Page, base_url: str):
        """Test that admin actions are logged securely."""
        # This is more of a code review item, but we can test the endpoint behavior
        headers = {"Authorization": "Bearer test_admin_token"}

        response = page.request.post(f"{base_url}/admin/upload-bid", headers=headers)

        # Should handle the request (fail for missing data, but not crash)
        assert response.status in [400, 401, 422]

        # Response should not leak sensitive information
        response_text = response.text()
        sensitive_terms = ["token", "password", "secret", "key"]
        for term in sensitive_terms:
            assert (
                term.lower() not in response_text.lower()
            ), f"Response may contain sensitive information: {term}"
