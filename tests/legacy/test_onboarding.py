"""Test onboarding workflow."""

from unittest.mock import patch

import pytest
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_onboarding_redirect_for_new_user(client):
    """Test that new users are redirected to onboarding."""
    # Simulate fresh user without profile
    with patch("auth_helpers.get_current_user_id", return_value="test_user_123"):
        with patch("services.db.get_profile", return_value={"onboard_complete": False}):
            response = client.get("/")
            assert response.status_code == 302
            assert "/onboarding" in response.headers["Location"]


def test_onboarding_completion_flow(client):
    """Test complete onboarding wizard flow."""
    user_id = "test_user_456"

    with patch("auth_helpers.get_current_user_id", return_value=user_id):
        with patch("services.db.get_profile", return_value={"onboard_complete": False}):
            # Step 1: Basic info
            with patch("services.db.save_profile") as mock_save:
                response = client.post(
                    "/onboarding",
                    data={
                        "step": "1",
                        "airline": "United",
                        "base": "IAH",
                        "seat": "FO",
                    },
                    headers={"X-Replit-User-Id": user_id},
                )
                assert response.status_code == 302
                assert "/onboarding/2" in response.headers["Location"]
                mock_save.assert_called_once()

        # Step 2: Fleet and seniority
        response = client.post(
            "/onboarding",
            data={
                "step": "2",
                "fleet": "737,320",
                "seniority": "1250",
            },
        )
        assert response.status_code == 302
        assert "/onboarding/3" in response.headers["Location"]

        # Step 3: Complete
        response = client.post(
            "/onboarding",
            data={
                "step": "3",
            },
        )
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")


def test_onboarded_user_access(client):
    """Test that onboarded users can access dashboard directly."""
    user_id = "test_user_789"

    # Mock completed profile
    completed_profile = {
        "airline": "United",
        "base": "IAH",
        "seat": "FO",
        "fleet": ["737"],
        "seniority": 1250,
        "onboard_complete": True,
        "profile_completed": True,
    }

    with patch("auth_helpers.get_current_user_id", return_value=user_id):
        with patch("services.db.get_profile", return_value=completed_profile):
            with patch("services.bids.get_matching_bid_packet", return_value=None):
                response = client.get("/")
                assert response.status_code == 200
                assert b"Welcome to VectorBid" in response.data


if __name__ == "__main__":
    pytest.main([__file__])
