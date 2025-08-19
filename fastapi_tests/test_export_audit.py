import sqlite3
from pathlib import Path

import jwt
from fastapi.testclient import TestClient

from app.main import app


def _build_artifact(client: TestClient):
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


def _export(client: TestClient, token: str, artifact: dict):
    payload = {"artifact": artifact, "ctx_id": "ctx-u1"}
    headers = {"Authorization": f"Bearer {token}"}
    return client.post("/api/export", headers=headers, json=payload)


def test_signature_determinism(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    monkeypatch.setenv("EXPORT_DB_PATH", str(tmp_path / "audit.db"))
    client = TestClient(app)
    artifact = _build_artifact(client)
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")

    r1 = _export(client, token, artifact)
    r2 = _export(client, token, artifact)
    assert r1.status_code == 200 and r2.status_code == 200
    sig1 = r1.json()["sha256"]
    sig2 = r2.json()["sha256"]
    assert sig1 == sig2
    sig_path = Path(r1.json()["path"] + ".sig")
    assert sig_path.read_text() == sig1


def test_db_insert(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path))
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("EXPORT_DB_PATH", str(db_path))
    client = TestClient(app)
    artifact = _build_artifact(client)
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")

    r = _export(client, token, artifact)
    assert r.status_code == 200
    out = r.json()

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT id, ctx_id, path, sha256 FROM exports WHERE id = ?",
        (out["id"],),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == out["id"]
    assert row[1] == "ctx-u1"
    assert row[2] == out["path"]
    assert row[3] == out["sha256"]
