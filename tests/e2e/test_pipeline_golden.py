import json, os
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

# Adjust if your entrypoint differs
from app.main import app

GOLDENS_DIR = Path(__file__).parent / "goldens"
GOLDENS_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

SCENARIOS = [
    {
        "name": "ual_ewr_73n_weekends_home",
        "persona": {"airline": "UAL", "base": "EWR", "seat": "FO", "fleet": "73N"},
        "free_text": "Protect 3-day weekends at home. Avoid redeyes. Prefer ORD and DEN layovers.",
        "weights": {"weekend_protection": 1.0, "layover_pref": 0.7, "avoid_redeye": 1.0, "diversity": 0.2},
    },
    {
        "name": "ual_iah_family_days",
        "persona": {"airline": "UAL", "base": "IAH", "seat": "CA", "fleet": "7M8"},
        "free_text": "Maximize days off around the 15th. No deadheads. Prefer 2-3 day trips.",
        "weights": {"days_off_midmonth": 1.0, "no_deadhead": 1.0, "trip_length_2_3": 0.6},
    },
]

def _golden_path(name: str) -> Path:
    return GOLDENS_DIR / f"{name}.json"

def _approve_mode() -> bool:
    return os.getenv("GOLDEN_APPROVE") == "1"

@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_full_pipeline_golden(client, scenario):
    # quick sanity: health should pass
    h = client.get("/health")
    assert h.status_code == 200, h.text

    # 1) parse
    parse_payload = {
        "persona": scenario["persona"],
        "free_text": scenario["free_text"],
        "weights": scenario["weights"],
    }
    r = client.post("/parse_preferences", json=parse_payload)
    assert r.status_code == 200, r.text
    parsed = r.json()

    # 2) validate
    r = client.post("/validate", json={"preferences": parsed})
    assert r.status_code == 200, r.text
    validation = r.json()

    # 3) optimize
    r = client.post("/optimize", json={"preferences": parsed, "validation": validation, "top_k": 20})
    assert r.status_code == 200, r.text
    optimized = r.json()

    # 4) strategy
    r = client.post("/strategy", json={"preferences": parsed, "optimized": optimized})
    assert r.status_code == 200, r.text
    strategy = r.json()

    # 5) generate layers
    r = client.post("/generate_layers", json={"strategy": strategy})
    assert r.status_code == 200, r.text
    layers = r.json()

    # 6) lint
    r = client.post("/lint", json={"layers": layers})
    assert r.status_code == 200, r.text
    lint = r.json()
    assert lint.get("errors", []) == [], f"Layer lint errors: {lint}"

    # 7) export hash (use field if provided; else synthesize)
    export_hash = layers.get("export_hash") or str(uuid4())
    out = {
        "parsed": parsed,
        "validation": validation,
        "optimized": optimized,
        "strategy": strategy,
        "layers": layers,
        "export_hash": export_hash,
    }

    golden = _golden_path(scenario["name"])
    if _approve_mode() or not golden.exists():
        golden.write_text(json.dumps(out, indent=2, sort_keys=True))
    else:
        expect = json.loads(golden.read_text())
        assert out == expect, (
            f"Golden drift for {scenario['name']}. "
            f"Set GOLDEN_APPROVE=1 to update after intentional changes."
        )
