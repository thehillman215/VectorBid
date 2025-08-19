import hashlib
import hmac
import pathlib

import jwt
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
    topk = client.post("/api/optimize", json=fb).json()["candidates"]
    artifact = client.post(
        "/api/generate_layers",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    ).json()["artifact"]
    return artifact


def test_export_requires_jwt_and_produces_signature(tmp_path, monkeypatch):
    # Enable JWT auth & set export dir and signing key
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.delenv("VECTORBID_API_KEY", raising=False)
    monkeypatch.setenv("EXPORT_SIGNING_KEY", "sign")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))

    client = TestClient(app)
    artifact = _build_artifact(client)

    # Without token -> 401
    r = client.post("/api/export", json={"artifact": artifact})
    assert r.status_code == 401

    # With invalid token -> 401
    bad = jwt.encode({"sub": "u1"}, "wrong", algorithm="HS256")
    r = client.post(
        "/api/export",
        headers={"Authorization": f"Bearer {bad}"},
        json={"artifact": artifact},
    )
    assert r.status_code == 401

    # With valid token -> 200 and signed output
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
    r = client.post(
        "/api/export",
        headers={"Authorization": f"Bearer {token}"},
        json={"artifact": artifact},
    )
    assert r.status_code == 200
    out = r.json()
    assert "export_path" in out and "signature" in out
    path = pathlib.Path(out["export_path"])
    assert path.exists()
    sig_path = pathlib.Path(str(path) + ".sig")
    assert sig_path.exists()
    data = path.read_bytes()
    expected = hmac.new(b"sign", data, hashlib.sha256).hexdigest()
    assert sig_path.read_text() == expected
    assert out["signature"] == expected


def test_export_requires_api_key_and_produces_signature(tmp_path, monkeypatch):
    # Enable API key auth & set export dir and signing key
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("VECTORBID_API_KEY", "secret")
    monkeypatch.setenv("EXPORT_SIGNING_KEY", "sign")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))

    client = TestClient(app)
    artifact = _build_artifact(client)

    # Without key -> 401
    r = client.post("/api/export", json={"artifact": artifact})
    assert r.status_code == 401

    # With wrong key -> 401
    r = client.post(
        "/api/export",
        headers={"x-api-key": "wrong"},
        json={"artifact": artifact},
    )
    assert r.status_code == 401

    # With valid key -> 200 and signed output
    r = client.post(
        "/api/export",
        headers={"x-api-key": "secret"},
        json={"artifact": artifact},
    )
    assert r.status_code == 200
    out = r.json()
    assert "export_path" in out and "signature" in out
    path = pathlib.Path(out["export_path"])
    assert path.exists()
    sig_path = pathlib.Path(str(path) + ".sig")
    assert sig_path.exists()
    data = path.read_bytes()
    expected = hmac.new(b"sign", data, hashlib.sha256).hexdigest()
    assert sig_path.read_text() == expected
    assert out["signature"] == expected
