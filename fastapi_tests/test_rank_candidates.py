import pytest

from app.services.optimizer import select_topk
from app.models import FeatureBundle, PreferenceSchema, ContextSnapshot, SoftPrefs


def _bundle() -> FeatureBundle:
    ctx = ContextSnapshot(
        ctx_id="ctx",
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        seniority_percentile=0.6,
        default_weights={"layovers": 1.0},
    )
    prefs = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        soft_prefs=SoftPrefs(layovers={"prefer": ["A"], "weight": 1.0}),
    )
    analytics = {
        "base_stats": {
            "A": {"award_rate": 0.8},
            "B": {"award_rate": 0.7},
        }
    }
    pairings = {
        "pairings": [
            {"id": "A", "layover_city": "A"},
            {"id": "B", "layover_city": "B"},
        ]
    }
    return FeatureBundle(
        context=ctx,
        preference_schema=prefs,
        analytics_features=analytics,
        compliance_flags={},
        pairing_features=pairings,
    )


def test_select_topk_deterministic():
    bundle = _bundle()
    first = select_topk(bundle, 2)
    second = select_topk(bundle, 2)

    assert [c.score for c in first] == [c.score for c in second]
    assert first[0].score >= first[1].score
    assert [c.candidate_id for c in first] == ["A", "B"]
    assert first[0].pairings == ["A"]
    assert "award_rate" in first[0].soft_breakdown
    assert 0.0 <= first[0].score <= 2.0
    assert first[0].rationale


def test_select_topk_handles_missing_data():
    ctx = ContextSnapshot(
        ctx_id="ctx",
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        seniority_percentile=0.6,
        default_weights={"layovers": 1.0},
    )
    prefs = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        soft_prefs=SoftPrefs(),
    )
    bundle = FeatureBundle(
        context=ctx,
        preference_schema=prefs,
        analytics_features={},
        compliance_flags={},
        pairing_features={"pairings": [{"id": "X"}]},
    )
    ranked = select_topk(bundle, 1)
    assert ranked[0].soft_breakdown["award_rate"] == pytest.approx(0.25)
    assert ranked[0].soft_breakdown["layovers"] == pytest.approx(0.25)
    assert ranked[0].pairings == ["X"]
    assert ranked[0].score == pytest.approx(0.51, rel=1e-2)
