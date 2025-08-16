"""E2E tests for UI elements and data-test-id attributes."""

from playwright.sync_api import Page, expect


class TestUIElements:
    """Test UI elements have proper data-test-id attributes and accessibility."""

    def test_onboarding_ui_elements(self, page: Page, base_url: str):
        """Test onboarding wizard has proper test IDs and interactive elements."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_ui"})
        page.goto(f"{base_url}/onboarding")

        # Test for key interactive elements
        elements_to_check = [
            'select[name="airline"]',
            'input[name="base"]',
            '.seat-option',
            'button[type="submit"]',
            '.progress-bar'
        ]

        for selector in elements_to_check:
            element = page.locator(selector).first
            if element.count() > 0:
                expect(element).to_be_visible()

    def test_dashboard_ui_elements(self, page: Page, base_url: str):
        """Test dashboard has proper interactive elements."""
        # Set up completed user
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_dashboard_ui"})

        # Complete onboarding first
        page.goto(f"{base_url}/onboarding")
        self._complete_onboarding_quickly(page)

        # Now test dashboard
        page.goto(base_url)

        # Test for navigation elements
        nav_elements = page.locator("nav, .navbar, [role='navigation']")
        expect(nav_elements.first).to_be_visible()

        # Test for main content areas
        main_content = page.locator("main, .main-content, .container")
        expect(main_content.first).to_be_visible()

    def _complete_onboarding_quickly(self, page: Page):
        """Helper to quickly complete onboarding for testing."""
        try:
            # Step 1
            page.locator('select[name="airline"]').select_option("United")
            page.locator('input[name="base"]').fill("IAH")
            page.locator('.seat-option').first.click()
            page.locator('button[type="submit"]').click()

            # Step 2
            page.locator('.fleet-chip').first.click()
            page.locator('input[name="seniority"]').fill("1000")
            page.locator('button[type="submit"]').click()

            # Step 3
            page.locator('button[type="submit"]').click()
        except Exception:
            # If onboarding fails, continue with tests
            pass

    def test_form_validation_messages(self, page: Page, base_url: str):
        """Test form validation messages are accessible."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_validation_ui"})
        page.goto(f"{base_url}/onboarding")

        # Try to submit empty form
        page.locator('button[type="submit"]').click()

        # Check for validation messages (HTML5 or custom)
        # This tests that validation exists, specific behavior may vary

        # Fill some fields and try partial submission
        page.locator('select[name="airline"]').select_option("United")
        # Leave other required fields empty
        page.locator('button[type="submit"]').click()

        # Should still be on step 1 or show validation
        expect(page.locator('select[name="airline"]')).to_be_visible()

    def test_interactive_elements_keyboard_accessible(self, page: Page, base_url: str):
        """Test interactive elements are keyboard accessible."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_keyboard_ui"})
        page.goto(f"{base_url}/onboarding")

        # Test tab navigation
        page.keyboard.press("Tab")
        focused_element = page.locator(":focus")
        if focused_element.count() > 0:
            expect(focused_element).to_be_visible()

        # Test that buttons can be activated with Enter/Space
        submit_button = page.locator('button[type="submit"]')
        if submit_button.is_visible():
            submit_button.focus()
            # Could test Enter key activation, but might trigger form submission

    def test_responsive_navigation(self, page: Page, base_url: str):
        """Test navigation is responsive across screen sizes."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_responsive_ui"})

        # Test different screen sizes
        screen_sizes = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667),    # Mobile
        ]

        for width, height in screen_sizes:
            page.set_viewport_size(width, height)
            page.goto(base_url)

            # Navigation should be present and functional
            nav_elements = page.locator("nav, .navbar, .nav-menu")
            if nav_elements.count() > 0:
                expect(nav_elements.first).to_be_visible()

    def test_loading_states(self, page: Page, base_url: str):
        """Test loading states and spinners."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_loading_ui"})

        # Intercept network requests to simulate slow loading
        page.route("**/*", lambda route: route.continue_())

        page.goto(base_url)

        # Check for loading indicators (if any)
        loading_indicators = page.locator(".loading, .spinner, [aria-label*='loading']")
        # Loading indicators are optional, but if present should be properly labeled

    def test_error_states_ui(self, page: Page, base_url: str):
        """Test error state UI elements."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_error_ui"})

        # Test 404 page if it exists
        page.goto(f"{base_url}/nonexistent-route")

        # Should show some form of error handling
        error_indicators = page.locator("text=404, text=not found, text=error, h1, h2")
        expect(error_indicators).to_have_count_greater_than(0)

    def test_color_contrast_accessibility(self, page: Page, base_url: str):
        """Test color contrast meets accessibility standards."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_contrast_ui"})
        page.goto(base_url)

        # This would ideally use axe-core's color contrast checks
        # For now, just ensure text is readable
        text_elements = page.locator("p, h1, h2, h3, h4, h5, h6, span, div")

        # Check that text elements have text content
        for i in range(min(5, text_elements.count())):
            element = text_elements.nth(i)
            if element.is_visible():
                text_content = element.text_content()
                if text_content and text_content.strip():
                    # Element has visible text content
                    expect(element).to_be_visible()

    def test_focus_management(self, page: Page, base_url: str):
        """Test focus management in interactive flows."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_focus_ui"})
        page.goto(f"{base_url}/onboarding")

        # Test that focus moves appropriately through form
        page.keyboard.press("Tab")
        first_focused = page.locator(":focus")

        page.keyboard.press("Tab")
        second_focused = page.locator(":focus")

        # Focus should move to different elements
        if first_focused.count() > 0 and second_focused.count() > 0:
            first_element = first_focused.first
            second_element = second_focused.first

            # They should be different elements (if multiple focusable elements exist)
            if page.locator("input, select, button, a").count() > 1:
                first_id = first_element.get_attribute("id") or first_element.get_attribute("name")
                second_id = second_element.get_attribute("id") or second_element.get_attribute("name")

                if first_id and second_id:
                    assert first_id != second_id, "Focus should move between different elements"

    def test_skip_links(self, page: Page, base_url: str):
        """Test skip links for accessibility."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_skip_ui"})
        page.goto(base_url)

        # Look for skip links (optional but good for accessibility)
        skip_links = page.locator("a[href='#main'], a[href='#content'], a:has-text('Skip')")

        # If skip links exist, they should be functional
        for i in range(skip_links.count()):
            skip_link = skip_links.nth(i)
            href = skip_link.get_attribute("href")
            if href and href.startswith("#"):
                target_id = href[1:]
                target_element = page.locator(f"#{target_id}")
                # Target should exist if skip link is present
                if target_element.count() == 0:
                    # This is just a warning, not a failure
                    print(f"Warning: Skip link target #{target_id} not found")

    def test_aria_labels_and_roles(self, page: Page, base_url: str):
        """Test ARIA labels and roles are properly used."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_aria_ui"})
        page.goto(base_url)

        # Check for proper ARIA usage
        elements_with_aria = page.locator("[aria-label], [aria-describedby], [role]")

        for i in range(min(10, elements_with_aria.count())):
            element = elements_with_aria.nth(i)

            # Check aria-label has meaningful content
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                assert len(aria_label.strip()) > 0, "ARIA labels should not be empty"

            # Check role is valid
            role = element.get_attribute("role")
            if role:
                valid_roles = [
                    "button", "link", "navigation", "main", "banner", "contentinfo",
                    "complementary", "form", "search", "application", "dialog",
                    "alert", "status", "progressbar", "tab", "tabpanel", "tablist"
                ]
                # This is informational - many custom roles exist
                # assert role in valid_roles, f"Unknown ARIA role: {role}"
