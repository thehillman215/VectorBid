from fastapi.testclient import TestClient
from app.main import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert ("ok" in j and j["ok"] is True) or (j.get("status") == "ok")
