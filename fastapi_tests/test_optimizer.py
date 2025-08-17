import pytest

from app.services.optimizer import select_topk, SCORING_CATEGORIES, _get_scoring_weights
from app.models import FeatureBundle, PreferenceSchema, SoftPrefs, ContextSnapshot


def _build_bundle() -> FeatureBundle:
    dw = {k: 1.0 for k in SCORING_CATEGORIES}
    context = ContextSnapshot(
        ctx_id="1",
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        seniority_percentile=0.5,
        default_weights=dw,
    )
    prefs = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        soft_prefs=SoftPrefs(
            layovers={"prefer": ["B"], "weight": 1.0},
            pairing_length={"prefer": ["short"], "weight": 1.0},
            report_time={"prefer": ["early"], "weight": 1.0},
            release_time={"prefer": ["early"], "weight": 1.0},
            credit={"prefer": ["high"], "weight": 1.0},
            weekend_priority={"prefer": ["weekend"], "weight": 1.0},
            commutable={"prefer": ["yes"], "weight": 1.0},
        ),
    )
    analytics = {
        "base_stats": {
            "A": {"award_rate": 0.8},
            "B": {"award_rate": 0.7},
        }
    }
    pairings = {
        "pairings": [
            {
                "id": "A_id",
                "layover_city": "A",
                "pairing_length": "long",
                "report_time": "late",
                "release_time": "late",
                "credit": "low",
                "weekend_priority": "weekday",
                "commutable": "no",
            },
            {
                "id": "B_id",
                "layover_city": "B",
                "pairing_length": "short",
                "report_time": "early",
                "release_time": "early",
                "credit": "high",
                "weekend_priority": "weekend",
                "commutable": "yes",
            },
        ]
    }
    return FeatureBundle(
        context=context,
        preference_schema=prefs,
        analytics_features=analytics,
        compliance_flags={},
        pairing_features=pairings,
    )


def test_select_topk_scoring_and_rationale():
    bundle = _build_bundle()
    topk = select_topk(bundle)

    assert [c.candidate_id for c in topk] == ["B_id", "A_id"]
    assert topk[0].pairings == ["B_id"]
    assert topk[1].pairings == ["A_id"]

    assert set(topk[0].soft_breakdown.keys()) == set(SCORING_CATEGORIES)
    assert topk[0].score == pytest.approx(0.9625)
    assert topk[1].score == pytest.approx(0.5375)

    max_val = max(topk[0].soft_breakdown.values())
    top_cats = {k for k, v in topk[0].soft_breakdown.items() if v == max_val}
    assert len(topk[0].rationale) == 3
    for msg in topk[0].rationale:
        factor = msg.split()[0]
        assert factor in top_cats

    assert topk[1].rationale[0].startswith("award_rate")


def test_persona_weighting_behavior():
    bundle = _build_bundle()
    bundle.context.default_weights = {k: 0.0 for k in SCORING_CATEGORIES if k != "layovers"}
    bundle.context.default_weights.update({"award_rate": 1.0})
    bundle.preference_schema.source = {"persona": "family_first"}
    weights = _get_scoring_weights(bundle)
    assert weights["layovers"] > weights["award_rate"]


def test_seniority_adjustment():
    bundle = _build_bundle()
    dw = {k: 0.0 for k in SCORING_CATEGORIES}
    dw.update({"award_rate": 2.0, "layovers": 1.0})
    bundle.context.default_weights = dw
    bundle.context.seniority_percentile = 1.0

    topk = select_topk(bundle, 1)
    expected = (0.7 * (2 / 3) + 1.0 * (1 / 3)) * 1.1
    assert topk[0].score == pytest.approx(expected)
    assert topk[0].pairings == ["B_id"]
