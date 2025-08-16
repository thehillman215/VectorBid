from fastapi.testclient import TestClient
from app.main import app
from app.generate import layers as gen_layers

def test_export_hash_golden(monkeypatch):
    # Freeze the month tag so the hash is time-stable
    monkeypatch.setattr(gen_layers, "_next_month_tag", lambda dt: "2025-09")
    client = TestClient(app)

    DATA = {"pairings":[
      {"id":"P1","layover_city":"SAN","redeye":False,"rest_hours":12},
      {"id":"P2","layover_city":"SJU","redeye":False,"rest_hours":11},
      {"id":"P3","layover_city":"XXX","redeye":True,"rest_hours":9}
    ]}
    pref = {
      "pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO","equip":["73G"],
      "hard_constraints":{"no_red_eyes": True},
      "soft_prefs":{"layovers":{"prefer":["SAN","SJU"],"weight":1.0}}
    }
    ctx = {"ctx_id":"ctx-u1","pilot_id":"u1","airline":"UAL","base":"EWR","seat":"FO",
           "equip":["73G"],"seniority_percentile":0.5,"commuting_profile":{},
           "default_weights":{"layovers":1.0}}

    # Optimize → TopK
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

    # Generate → artifact with deterministic export_hash
    artifact = client.post(
        "/generate_layers",
        json={"feature_bundle": fb["feature_bundle"], "candidates": topk},
    ).json()["artifact"]

    # Known-good hash for this frozen month + payload
    assert artifact["month"] == "2025-09"
    assert artifact["export_hash"] == "84bc797693de6955fb1029c46ef21ae669e221771a87ed06bfdcf223cd76cd56"
