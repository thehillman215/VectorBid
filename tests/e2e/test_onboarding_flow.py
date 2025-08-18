"""E2E tests for the onboarding flow."""

from axe_playwright_python import get_violations, inject_axe, run_axe
from playwright.sync_api import Page, expect


class TestOnboardingFlow:
    """Test the complete onboarding user journey."""

    def test_new_user_redirected_to_onboarding(self, page: Page, base_url: str):
        """Test that new users are redirected to onboarding wizard."""
        # Set mock user header
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_new_redirect"})

        # Visit home page
        page.goto(base_url)

        # Should be redirected to onboarding
        expect(page).to_have_url(f"{base_url}/onboarding")

        # Should see step 1 content
        expect(page.locator("h2")).to_contain_text("Welcome to VectorBid")
        expect(page.locator(".progress-bar")).to_be_visible()
        expect(page.locator("text=Step 1 of 3")).to_be_visible()

    def test_onboarding_step1_airline_selection(self, page: Page, base_url: str):
        """Test step 1: airline and basic info selection."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_step1"})
        page.goto(f"{base_url}/onboarding")

        # Should see airline dropdown
        airline_select = page.locator('select[name="airline"]')
        expect(airline_select).to_be_visible()

        # Should see base input
        base_input = page.locator('input[name="base"]')
        expect(base_input).to_be_visible()

        # Should see position selection cards
        expect(page.locator(".seat-option")).to_have_count(2)

        # Fill form with valid data
        airline_select.select_option("United")
        base_input.fill("IAH")
        page.locator(".seat-option").first.click()  # Select Captain

        # Submit step 1
        page.locator('button[type="submit"]').click()

        # Should advance to step 2
        expect(page).to_have_url(f"{base_url}/onboarding/2")
        expect(page.locator("text=Step 2 of 3")).to_be_visible()

    def test_onboarding_step1_validation(self, page: Page, base_url: str):
        """Test step 1 form validation."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_validation1"})
        page.goto(f"{base_url}/onboarding")

        # Try to submit without required fields
        page.locator('button[type="submit"]').click()

        # Should show HTML5 validation or stay on same page
        expect(page).to_have_url(f"{base_url}/onboarding")

    def test_onboarding_step2_fleet_selection(self, page: Page, base_url: str):
        """Test step 2: fleet and seniority input."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_step2"})
        page.goto(f"{base_url}/onboarding/2")

        # Should see fleet chips
        fleet_chips = page.locator(".fleet-chip")
        expect(fleet_chips).to_have_count_greater_than(3)

        # Should see seniority input
        seniority_input = page.locator('input[name="seniority"]')
        expect(seniority_input).to_be_visible()

        # Select fleet types
        page.locator('.fleet-chip:has-text("737")').click()
        page.locator('.fleet-chip:has-text("320")').click()

        # Fill seniority
        seniority_input.fill("1250")

        # Submit step 2
        page.locator('button[type="submit"]').click()

        # Should advance to step 3
        expect(page).to_have_url(f"{base_url}/onboarding/3")
        expect(page.locator("text=Step 3 of 3")).to_be_visible()

    def test_onboarding_step3_completion(self, page: Page, base_url: str):
        """Test step 3: completion and redirect to dashboard."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_step3"})
        page.goto(f"{base_url}/onboarding/3")

        # Should see completion content
        expect(page.locator("text=You're All Set!")).to_be_visible()
        expect(page.locator("text=AI-Powered Rankings")).to_be_visible()

        # Submit final step
        page.locator('button[type="submit"]').click()

        # Should redirect to main dashboard
        expect(page).to_have_url(base_url + "/")
        expect(page.locator("text=Welcome to VectorBid")).to_be_visible()

    def test_complete_onboarding_flow(self, page: Page, base_url: str):
        """Test the complete onboarding flow from start to finish."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_complete_flow"})

        # Start at home - should redirect to onboarding
        page.goto(base_url)
        expect(page).to_have_url(f"{base_url}/onboarding")

        # Step 1: Fill basic info
        page.locator('select[name="airline"]').select_option("Delta")
        page.locator('input[name="base"]').fill("ATL")
        page.locator('.seat-option:has-text("First Officer")').click()
        page.locator('button[type="submit"]').click()

        # Step 2: Select fleet and seniority
        expect(page).to_have_url(f"{base_url}/onboarding/2")
        page.locator('.fleet-chip:has-text("737")').click()
        page.locator('input[name="seniority"]').fill("2500")
        page.locator('button[type="submit"]').click()

        # Step 3: Complete onboarding
        expect(page).to_have_url(f"{base_url}/onboarding/3")
        page.locator('button[type="submit"]').click()

        # Should be on main dashboard
        expect(page).to_have_url(base_url + "/")

        # Future visits should go directly to dashboard (no redirect)
        page.goto(base_url)
        expect(page).to_have_url(base_url + "/")

    def test_onboarding_accessibility(self, page: Page, base_url: str):
        """Test onboarding wizard accessibility compliance."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_a11y"})

        # Test each step for accessibility violations
        for step in range(1, 4):
            page.goto(
                f"{base_url}/onboarding/{step}"
                if step > 1
                else f"{base_url}/onboarding"
            )

            # Inject axe-core
            inject_axe(page)

            # Run accessibility scan
            results = run_axe(page)
            violations = get_violations(results)

            # Check for critical violations
            critical_violations = [
                v for v in violations if v["impact"] in ["critical", "serious"]
            ]

            assert len(critical_violations) == 0, (
                f"Step {step} has {len(critical_violations)} critical accessibility violations: {critical_violations}"
            )

    def test_onboarding_navigation_back_forward(self, page: Page, base_url: str):
        """Test navigation between onboarding steps."""
        page.set_extra_http_headers({"X-Replit-User-Id": "test_user_navigation"})

        # Complete step 1
        page.goto(f"{base_url}/onboarding")
        page.locator('select[name="airline"]').select_option("Southwest")
        page.locator('input[name="base"]').fill("BWI")
        page.locator(".seat-option").first.click()
        page.locator('button[type="submit"]').click()

        # Should be on step 2
        expect(page).to_have_url(f"{base_url}/onboarding/2")

        # Click back button
        page.locator('a:has-text("Back")').click()
        expect(page).to_have_url(f"{base_url}/onboarding/1")

        # Should preserve previously entered data
        expect(page.locator('select[name="airline"]')).to_have_value("Southwest")
        expect(page.locator('input[name="base"]')).to_have_value("BWI")
