import json
import subprocess
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ping_text_and_request_id():
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.text == "pong"
    assert r.headers["content-type"].startswith("text/plain")
    assert "X-Request-ID" in r.headers


def test_health_fields():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"db", "storage", "rulepack_version"}
    assert data["db"] == "ok"
    assert data["storage"] == "ok"
    assert data["rulepack_version"]
    assert "X-Request-ID" in r.headers


def test_request_id_echo():
    rid = "abc-123"
    r = client.get("/ping", headers={"X-Request-ID": rid})
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == rid


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


def test_metrics_endpoint():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "# HELP" in r.text


def test_curl_smoke():
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(10):
            try:
                ping_out = (
                    subprocess.check_output(
                        ["curl", "-s", "http://127.0.0.1:8001/ping"],
                        stderr=subprocess.DEVNULL,
                    )
                    .decode()
                    .strip()
                )
                break
            except subprocess.CalledProcessError:
                time.sleep(0.5)
        else:
            raise AssertionError("server did not start")
        assert ping_out == "pong"
        health_out = subprocess.check_output(
            ["curl", "-s", "http://127.0.0.1:8001/health"]
        ).decode()
        data = json.loads(health_out)
        assert set(data) == {"db", "storage", "rulepack_version"}
    finally:
        proc.terminate()
        proc.wait()
