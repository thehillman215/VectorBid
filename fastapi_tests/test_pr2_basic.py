import json
import pathlib

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
DATA = json.loads(
    (pathlib.Path(__file__).parent / "testdata" / "pairings_small.json").read_text()
)


def _bundle(pref_overrides=None):
    pref = {
        "pilot_id": "u1",
        "airline": "UAL",
        "base": "EWR",
        "seat": "FO",
        "equip": ["73G"],
        "hard_constraints": {"no_red_eyes": True},
        "soft_prefs": {"layovers": {"prefer": ["SAN", "SJU"], "weight": 1.0}},
    }
    if pref_overrides:
        pref.update(pref_overrides)
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
    return {
        "context": ctx,
        "preference_schema": pref,
        "analytics": {
            "base_stats": {"SAN": {"award_rate": 0.65}, "SJU": {"award_rate": 0.55}}
        },
        "precheck": {},
        "pairings": DATA,
    }


def test_validate_and_optimize_generate_lint_and_hash():
    # validate
    bundle = _bundle()
    r = client.post(
        "/api/validate",
        json={
            "preference_schema": bundle["preference_schema"],
            "context": bundle["context"],
            "pairings": DATA,
        },
    )
    assert r.status_code == 200
    v = r.json()
    # P3 violates hard rules (redeye + rest < 10)
    assert any(x["pairing_id"] == "P3" for x in v["violations"])

    # feature bundle for optimize
    fb = {
        "feature_bundle": {
            "context": bundle["context"],
            "preference_schema": bundle["preference_schema"],
            "analytics_features": bundle["analytics"],
            "compliance_flags": {},
            "pairing_features": DATA,
        },
        "K": 5,
    }
    r = client.post("/api/optimize", json=fb)
    assert r.status_code == 200
    topk = r.json()["candidates"]
    assert topk and topk[0]["candidate_id"] == "P1"  # SAN preferred

    # strategy
    r = client.post(
        "/api/strategy",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    )
    assert r.status_code == 200
    directives = r.json()["directives"]
    # bounded delta or no-op
    assert "weight_deltas" in directives
    for v in directives["weight_deltas"].values():
        assert -0.15 <= v <= 0.15

    # generate layers
    r = client.post(
        "/api/generate_layers",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    )
    assert r.status_code == 200
    artifact = r.json()["artifact"]
    assert artifact["airline"] == "UAL"
    assert artifact["format"] == "PBS2"
    assert artifact["export_hash"]  # hash present
    # lint happy path
    r = client.post("/api/lint", json={"artifact": artifact})
    assert r.status_code == 200
    lint = r.json()
    assert lint["errors"] == []
