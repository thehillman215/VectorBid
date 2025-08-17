import pytest

from app.optimize.optimizer import rank_candidates
from app.models import FeatureBundle, PreferenceSchema, ContextSnapshot, SoftPrefs


def _bundle(persona: str = "family_first") -> FeatureBundle:
    ctx = ContextSnapshot(
        ctx_id="ctx",
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        seniority_percentile=0.6,
        default_weights={},
    )
    prefs = PreferenceSchema(
        pilot_id="p1",
        airline="UAL",
        base="DEN",
        seat="FO",
        equip=["7M8"],
        soft_prefs=SoftPrefs(),
        source={"persona": persona},
    )
    return FeatureBundle(
        context=ctx,
        preference_schema=prefs,
        analytics_features={},
        compliance_flags={},
        pairing_features={},
    )


def test_rank_candidates_scoring_deterministic():
    bundle = _bundle()
    pairings = [
        {
            "id": "A",
            "days_off": 4,
            "block_hours": 20,
            "duty_hours": 30,
            "layover_quality": 0.9,
            "report_time": 12,
            "commutable": True,
            "trip_length": 3,
            "equipment": "7M8",
        },
        {
            "id": "B",
            "days_off": 1,
            "block_hours": 10,
            "duty_hours": 40,
            "layover_quality": 0.2,
            "report_time": 6,
            "commutable": False,
            "trip_length": 5,
            "equipment": "320",
        },
    ]

    first = rank_candidates(bundle, pairings, K=2)
    second = rank_candidates(bundle, pairings, K=2)

    assert [c.score for c in first] == [c.score for c in second]
    assert first[0].score >= first[1].score
    assert first[0].pairings == ["A"]
    assert "days_off" in first[0].soft_breakdown
    assert 0.0 <= first[0].score <= 1.0
    assert first[0].rationale


def test_rank_candidates_handles_missing_data():
    bundle = _bundle()
    pairings = [{"id": "X"}]
    ranked = rank_candidates(bundle, pairings)
    assert ranked[0].soft_breakdown["days_off"] == 0.5
    assert ranked[0].pairings == ["X"]
    assert 0.0 <= ranked[0].score <= 1.0
