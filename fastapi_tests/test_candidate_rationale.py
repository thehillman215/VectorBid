import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import CandidateSchedule

client = TestClient(app)
CATALOG = json.loads((Path("app/static/rules_catalog.json")).read_text())


def _bundle():
    return {
        "context": {
            "ctx_id": "ctx-u1",
            "pilot_id": "u1",
            "airline": "UAL",
            "base": "EWR",
            "seat": "FO",
            "equip": ["73G"],
            "seniority_percentile": 0.5,
            "commuting_profile": {},
            "default_weights": {"layovers": 1.0},
        },
        "preference_schema": {
            "pilot_id": "u1",
            "airline": "UAL",
            "base": "EWR",
            "seat": "FO",
            "equip": ["73G"],
            "hard_constraints": {"no_red_eyes": True},
            "soft_prefs": {"layovers": {"prefer": ["SAN"], "weight": 1.0}},
        },
        "analytics_features": {"base_stats": {"SAN": {"award_rate": 0.8}}},
        "compliance_flags": {},
        "pairing_features": {
            "pairings": [
                {"id": "P1", "layover_city": "SAN", "redeye": False, "rest_hours": 12},
                {"id": "P3", "layover_city": "XXX", "redeye": True, "rest_hours": 9},
            ]
        },
    }


def test_candidate_schema_has_rationale():
    schema = CandidateSchedule.model_json_schema()
    ref = schema["properties"]["rationale"]["$ref"]
    key = ref.split("/")[-1]
    rat = schema["$defs"][key]["properties"]
    assert {"hard_hits", "hard_misses", "notes"} <= set(rat)


def test_get_candidate_rationale_and_labels():
    payload = {"feature_bundle": _bundle(), "K": 3}
    r = client.post("/api/optimize", json=payload)
    assert r.status_code == 200
    # ensure candidates stored
    r = client.get("/api/candidates/P1")
    data = r.json()["candidate"]
    assert data["rationale"]["hard_misses"] == []
    assert "FAR117_MIN_REST" in data["rationale"]["hard_hits"]

    r = client.get("/api/candidates/P3")
    cand = r.json()["candidate"]
    misses = cand["rationale"]["hard_misses"]
    assert "FAR117_MIN_REST" in misses and "NO_REDEYE_IF_SET" in misses
    # mapping via catalog
    labels = [CATALOG[m] for m in misses]
    assert "Rest >= 10h" in labels
