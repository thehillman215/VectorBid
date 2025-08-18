from pathlib import Path

from app.ingestion.packet import parse_bid_packet
from app.models import ContextSnapshot, FeatureBundle, PreferenceSchema
from app.rules.engine import load_rule_pack, validate_feasibility
from app.services.optimizer import select_topk


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_parse_validate_optimize_vslice():
    # Parse
    sample_path = _repo_root() / "fastapi_tests" / "testdata" / "pairings_small.json"
    parsed = parse_bid_packet(str(sample_path))
    assert "pairings" in parsed and isinstance(parsed["pairings"], list)

    # Build bundle
    ctx = ContextSnapshot(
        ctx_id="ctx-1",
        pilot_id="p-1",
        airline="UAL",
        base="SFO",
        seat="FO",
        equip=["B737"],
        seniority_percentile=0.5,
        commuting_profile={},
        default_weights={},
    )
    pref = PreferenceSchema(
        pilot_id="p-1",
        airline="UAL",
        base="SFO",
        seat="FO",
        equip=["B737"],
    )
    bundle = FeatureBundle(
        context=ctx,
        preference_schema=pref,
        analytics_features={
            "base_stats": {
                "SAN": {"award_rate": 0.8},
                "SJU": {"award_rate": 0.7},
                "XXX": {"award_rate": 0.1},
            }
        },
        compliance_flags={},
        pairing_features=parsed,
    )

    # Validate
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml")
    result = validate_feasibility(bundle, rules)
    violations = result["violations"]
    feasible = result["feasible_pairings"]

    assert any(v.get("pairing_id") == "P3" and v.get("rule") == "FAR117_MIN_REST" for v in violations)
    feasible_ids = {p.get("id") for p in feasible}
    assert feasible_ids == {"P1", "P2"}

    # Optimize
    topk = select_topk(bundle, K=2)
    assert len(topk) == 2
    top_ids = {c.candidate_id for c in topk}
    assert top_ids == {"P1", "P2"}


