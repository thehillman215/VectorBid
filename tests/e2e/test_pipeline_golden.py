import json, os, glob
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app

# --- Path resolver (handles /api or /v0 prefixes) ----------------------------
_OPENAPI_PATHS = set(app.openapi().get("paths", {}).keys())

def _pick(endpoint: str) -> str:
    endpoint = "/" + endpoint.lstrip("/")
    if endpoint in _OPENAPI_PATHS:
        return endpoint
    for p in _OPENAPI_PATHS:
        if p.endswith(endpoint):
            return p
    raise AssertionError(f"Could not find path for {endpoint}. Have: {sorted(_OPENAPI_PATHS)[:10]}...")

def _maybe_parse(client: TestClient, payload: dict) -> dict:
    """Use /parse_preferences if present, otherwise pass-through."""
    try:
        path = _pick("parse_preferences")
    except AssertionError:
        return {
            "persona": payload.get("persona", {}),
            "weights": payload.get("weights", {}),
            "free_text": payload.get("free_text", ""),
        }
    r = client.post(path, json=payload)
    assert r.status_code == 200, r.text
    return r.json()

def _find_rule_pack() -> str:
    """Find a UAL rule-pack (e.g., rule_packs/UAL/2025.08.yml)."""
    root = Path(__file__).resolve().parents[2]
    candidates = sorted(glob.glob(str(root / "rule_packs" / "UAL" / "*.yml")))
    if not candidates:
        # fallback to a common default; your engine patch resolves from repo root
        return "rule_packs/UAL/2025.08.yml"
    # pick the latest-looking file
    return str(Path(candidates[-1]).relative_to(root))

def _build_context(persona: dict) -> dict:
    """Minimal context most handlers expect."""
    return {
        "airline": persona.get("airline"),
        "base": persona.get("base"),
        "seat": persona.get("seat"),
        "fleet": persona.get("fleet"),
        "rule_pack_path": _find_rule_pack(),
        "bid_period": "2025-09",
        "pbs_version": "2.x",
    }

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
    # health
    h = client.get(_pick("health"))
    assert h.status_code == 200, h.text

    # build context
    ctx = _build_context(scenario["persona"])

    # 1) parse (or fallback pass-through)
    parsed = _maybe_parse(client, {
        "persona": scenario["persona"],
        "free_text": scenario["free_text"],
        "weights": scenario["weights"],
    })

    # 2) validate (expects top-level 'context')
    r = client.post(_pick("validate"), json={"preferences": parsed, "context": ctx})
    assert r.status_code == 200, r.text
    validation = r.json()

    # 3) optimize (pass context along)
    r = client.post(_pick("optimize"), json={"preferences": parsed, "validation": validation, "context": ctx, "top_k": 20})
    assert r.status_code == 200, r.text
    optimized = r.json()

    # 4) strategy
    r = client.post(_pick("strategy"), json={"preferences": parsed, "optimized": optimized, "context": ctx})
    assert r.status_code == 200, r.text
    strategy = r.json()

    # 5) generate layers
    r = client.post(_pick("generate_layers"), json={"strategy": strategy, "context": ctx})
    assert r.status_code == 200, r.text
    layers = r.json()

    # 6) lint
    r = client.post(_pick("lint"), json={"layers": layers})
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
