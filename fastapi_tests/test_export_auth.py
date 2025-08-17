import pathlib

from fastapi.testclient import TestClient

from app.main import app


def _build_artifact(client: TestClient):
    # Freeze month for deterministic output (not strictly needed here, but tidy)
    # NOTE: We do not monkeypatch here to avoid conflicting with other tests
    DATA = {
        "pairings": [
            {"id": "P1", "layover_city": "SAN", "redeye": False, "rest_hours": 12},
            {"id": "P2", "layover_city": "SJU", "redeye": False, "rest_hours": 11},
            {"id": "P3", "layover_city": "XXX", "redeye": True, "rest_hours": 9},
        ]
    }
    pref = {
        "pilot_id": "u1",
        "airline": "UAL",
        "base": "EWR",
        "seat": "FO",
        "equip": ["73G"],
        "hard_constraints": {"no_red_eyes": True},
        "soft_prefs": {"layovers": {"prefer": ["SAN", "SJU"], "weight": 1.0}},
    }
    ctx = {
        "ctx_id": "ctx-u1",
        "pilot_id": "u1",
        "airline": "UAL",
        "base": "EWR",
        "seat": "FO",
        "equip": ["73G"],
        "seniority_percentile": 0.5,
        "commuting_profile": {},
        "default_weights": {"layovers": 1.0},
    }
    fb = {
        "feature_bundle": {
            "context": ctx,
            "preference_schema": pref,
            "analytics_features": {
                "base_stats": {"SAN": {"award_rate": 0.65}, "SJU": {"award_rate": 0.55}}
            },
            "compliance_flags": {},
            "pairing_features": DATA,
        },
        "K": 5,
    }
    topk = client.post("/optimize", json=fb).json()["candidates"]
    artifact = client.post(
        "/generate_layers",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    ).json()["artifact"]
    return artifact


def test_export_requires_api_key_when_enabled(tmp_path, monkeypatch):
    # Enable auth & set export dir
    monkeypatch.setenv("VECTORBID_API_KEY", "secret")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))

    client = TestClient(app)
    artifact = _build_artifact(client)

    # Without key -> 401
    r = client.post("/export", json={"artifact": artifact})
    assert r.status_code == 401

    # With wrong key -> 401
    r = client.post(
        "/export", headers={"x-api-key": "nope"}, json={"artifact": artifact}
    )
    assert r.status_code == 401

    # With correct header key -> 200 and path exists
    r = client.post(
        "/export", headers={"x-api-key": "secret"}, json={"artifact": artifact}
    )
    assert r.status_code == 200
    out = r.json()
    assert "export_path" in out
    assert pathlib.Path(out["export_path"]).exists()

    # Also allow via query param
    r = client.post("/export?api_key=secret", json={"artifact": artifact})
    assert r.status_code == 200
