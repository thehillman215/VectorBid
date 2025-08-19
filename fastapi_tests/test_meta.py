from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "web"}


def test_ping_ok():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True, "service": "web"}


def test_schemas_present():
    r = client.get("/schemas")
    assert r.status_code == 200
    data = r.json()
    # Must include the key models
    for name in [
        "PreferenceSchema",
        "ContextSnapshot",
        "FeatureBundle",
        "CandidateSchedule",
        "StrategyDirectives",
        "BidLayerArtifact",
    ]:
        assert name in data
        assert isinstance(data[name], dict)
