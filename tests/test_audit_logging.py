from pathlib import Path

from app.db import Audit, SessionLocal
from app.ingestion.packet import parse_bid_packet
from app.models import ContextSnapshot, FeatureBundle, PreferenceSchema
from app.rules.engine import load_rule_pack, validate_feasibility
from app.services.optimizer import select_topk


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_audit_trail_created():
    ctx = ContextSnapshot(
        ctx_id="audit-1",
        pilot_id="p-99",
        airline="UAL",
        base="SFO",
        seat="FO",
        equip=["B737"],
        seniority_percentile=0.5,
        commuting_profile={},
        default_weights={},
    )
    sample_path = _repo_root() / "fastapi_tests" / "testdata" / "pairings_small.json"
    parsed = parse_bid_packet(str(sample_path), ctx_id=ctx.ctx_id)
    pref = PreferenceSchema(
        pilot_id="p-99",
        airline="UAL",
        base="SFO",
        seat="FO",
        equip=["B737"],
    )
    bundle = FeatureBundle(
        context=ctx,
        preference_schema=pref,
        analytics_features={},
        compliance_flags={},
        pairing_features=parsed,
    )
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml")
    validate_feasibility(bundle, rules)
    select_topk(bundle, K=1)

    with SessionLocal() as db:
        rows = db.query(Audit).filter_by(ctx_id=ctx.ctx_id).all()
    stages = {r.stage for r in rows}
    assert {"ingest", "validate", "optimize"}.issubset(stages)
