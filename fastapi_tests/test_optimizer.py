import pytest

from app.services.optimizer import select_topk
from app.models import (
    FeatureBundle,
    PreferenceSchema,
    SoftPrefs,
    ContextSnapshot,
)


def _build_bundle():
    context = ContextSnapshot(
        ctx_id="1",
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        seniority_percentile=0.5,
        default_weights={"layovers": 1.0},
    )

    prefs = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        soft_prefs=SoftPrefs(layovers={"prefer": ["B"], "weight": 1.0}),
    )

    analytics = {
        "base_stats": {
            "A": {"award_rate": 0.8},
            "B": {"award_rate": 0.7},
        }
    }

    pairings = {
        "pairings": [
            {"id": "A_id", "layover_city": "A"},
            {"id": "B_id", "layover_city": "B"},
        ]
    }

    return FeatureBundle(
        context=context,
        preference_schema=prefs,
        analytics_features=analytics,
        compliance_flags={},
        pairing_features=pairings,
    )


def test_select_topk_pref_weighting():
    bundle = _build_bundle()
    topk = select_topk(bundle, 2)

    assert [c.candidate_id for c in topk] == ["B_id", "A_id"]
    assert topk[0].score == pytest.approx(1.7)
    assert topk[1].score == pytest.approx(1.3)
    assert topk[0].pairings == ["B_id"]
    assert topk[1].pairings == ["A_id"]

    # rationale should reflect top scoring factors
    assert len(topk[0].rationale) >= 2
    assert "layovers" in topk[0].rationale[0]
    assert "award_rate" in topk[0].rationale[1]

    assert len(topk[1].rationale) >= 2
    assert "award_rate" in topk[1].rationale[0]
    assert "layovers" in topk[1].rationale[1]
