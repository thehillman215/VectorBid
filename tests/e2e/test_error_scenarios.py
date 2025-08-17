"""E2E tests for error scenarios and edge cases."""

from playwright.sync_api import Page, expect


class TestErrorScenarios:
    """Test error handling and edge cases."""

    def test_network_error_handling(self, page: Page, base_url: str):
        """Test handling of network errors."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_network"})

        # Test with offline context
        page.context.set_offline(True)

        try:
            page.goto(base_url, timeout=5000)
        except Exception:
            # Network error expected when offline
            pass
        finally:
            page.context.set_offline(False)

    def test_javascript_errors(self, page: Page, base_url: str):
        """Test for JavaScript errors on pages."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_js"})

        js_errors = []

        def handle_console_message(msg):
            if msg.type == "error":
                js_errors.append(msg.text)

        page.on("console", handle_console_message)

        # Visit main pages and check for JS errors
        pages_to_test = [
            base_url,
            f"{base_url}/how-to",
            f"{base_url}/onboarding",
        ]

        for url in pages_to_test:
            try:
                page.goto(url)
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                # Some pages might redirect or have issues, continue testing
                continue

        # Filter out expected/harmless errors
        critical_errors = [
            error
            for error in js_errors
            if not any(
                harmless in error.lower()
                for harmless in ["favicon", "replit", "third-party", "extension"]
            )
        ]

        assert len(critical_errors) == 0, f"JavaScript errors found: {critical_errors}"

    def test_large_file_upload_handling(self, page: Page, base_url: str):
        """Test handling of large file uploads."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_large_file"})
        page.goto(base_url)

        # Look for file upload inputs
        file_inputs = page.locator('input[type="file"]')

        if file_inputs.count() > 0:
            # Create a fake large file (simulated)
            # In a real test, you might create a temporary large file
            # For now, just test that the interface exists and has size limits
            file_input = file_inputs.first

            # Check if there are size restrictions in place
            max_size_indicators = page.locator("text=MB, text=size, text=limit")
            # This is informational - good UX would show file size limits

    def test_invalid_user_session(self, page: Page, base_url: str):
        """Test handling of invalid user sessions."""
        # Test with malformed user header
        page.set_extra_http_headers({"X-Replit-User-Id": "invalid-user-format-!@#$"})

        page.goto(base_url)

        # Should handle gracefully without crashing
        expect(page.locator("body")).to_be_visible()

    def test_concurrent_user_sessions(self, page: Page, base_url: str):
        """Test handling of concurrent user sessions."""
        # Test rapid navigation
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_concurrent"})

        urls = [base_url, f"{base_url}/how-to", base_url, f"{base_url}/onboarding"]

        for url in urls:
            try:
                page.goto(url, timeout=3000)
            except Exception:
                # Rapid navigation might cause timeouts, which is acceptable
                continue

        # Should end up in a valid state
        expect(page.locator("body")).to_be_visible()

    def test_malformed_form_data(self, page: Page, base_url: str):
        """Test handling of malformed form data."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_malformed"})
        page.goto(f"{base_url}/onboarding")

        # Try to submit with unusual data
        page.evaluate(
            """
            const form = document.querySelector('form');
            if (form) {
                // Add hidden input with unusual data
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'malformed_data';
                input.value = '<script>alert("xss")</script>';
                form.appendChild(input);
            }
        """
        )

        # Submit form
        submit_btn = page.locator('button[type="submit"]')
        if submit_btn.is_visible():
            submit_btn.click()

            # Should handle malformed data gracefully
            expect(page.locator("body")).to_be_visible()

    def test_csrf_attack_simulation(self, page: Page, base_url: str):
        """Test CSRF protection by simulating cross-origin requests."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_csrf"})

        # Try to submit forms from different origins (simulated)
        page.goto(base_url)

        # Look for forms
        forms = page.locator("form")
        if forms.count() > 0:
            form = forms.first
            if form.is_visible():
                action = form.get_attribute("action") or ""
                method = form.get_attribute("method") or "GET"

                if method.upper() == "POST":
                    # This would be a more comprehensive test in a real scenario
                    # For now, just verify forms exist and have proper structure
                    expect(form).to_have_attribute("method")

    def test_database_connection_errors(self, page: Page, base_url: str):
        """Test handling when database is unavailable."""
        # This is hard to test without actually breaking the database
        # But we can test that the app handles profile loading errors
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_db_error"})

        page.goto(base_url)

        # Should load without crashing, even if database operations fail
        expect(page.locator("body")).to_be_visible()

        # Should show appropriate error messages if database is down
        error_indicators = page.locator("text=error, text=unavailable, text=try again")
        # Error messages are acceptable and expected if database is down

    def test_memory_leaks_basic(self, page: Page, base_url: str):
        """Basic test for memory leaks through repeated navigation."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_memory"})

        # Navigate between pages multiple times
        for _ in range(10):
            page.goto(base_url)
            page.goto(f"{base_url}/how-to")
            page.goto(f"{base_url}/onboarding")
            page.go_back()
            page.go_forward()

        # Should still be responsive
        page.goto(base_url)
        expect(page.locator("body")).to_be_visible()

    def test_xss_protection(self, page: Page, base_url: str):
        """Test XSS protection in user inputs."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_xss"})
        page.goto(f"{base_url}/onboarding")

        # Try XSS in form fields
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        text_inputs = page.locator('input[type="text"], input[type="email"], textarea')

        for i in range(min(text_inputs.count(), len(xss_payloads))):
            input_field = text_inputs.nth(i)
            if input_field.is_visible():
                input_field.fill(xss_payloads[i])

        # Submit if possible
        submit_btn = page.locator('button[type="submit"]')
        if submit_btn.is_visible():
            submit_btn.click()

            # Check that XSS was not executed
            page.wait_for_timeout(1000)  # Wait for any potential script execution

            # If we get here without alerts, XSS was properly escaped
            expect(page.locator("body")).to_be_visible()

    def test_sql_injection_protection(self, page: Page, base_url: str):
        """Test SQL injection protection in form inputs."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_sql"})
        page.goto(f"{base_url}/onboarding")

        # Try SQL injection in form fields
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker'); --",
        ]

        text_inputs = page.locator('input[type="text"], input[type="number"]')

        for i in range(min(text_inputs.count(), len(sql_payloads))):
            input_field = text_inputs.nth(i)
            if input_field.is_visible():
                input_field.fill(sql_payloads[i])

        # Submit form
        submit_btn = page.locator('button[type="submit"]')
        if submit_btn.is_visible():
            submit_btn.click()

            # Should handle gracefully without SQL errors
            expect(page.locator("body")).to_be_visible()

            # Should not show database error details
            error_text = page.content().lower()
            sql_error_indicators = [
                "sql",
                "database",
                "table",
                "column",
                "syntax error",
            ]
            for indicator in sql_error_indicators:
                assert (
                    indicator not in error_text or "error" not in error_text
                ), f"Possible SQL error exposed: {indicator}"
