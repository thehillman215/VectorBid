from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_preview_red_eye() -> None:
    resp = client.post("/api/parse_preview", json={"text": "no red-eye flights"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["preference_schema"]["hard_constraints"]["no_red_eyes"] is True
