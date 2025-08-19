import pytest

from app.models import CandidateSchedule
from app.services.optimizer import retune_candidates


def _toy_candidates():
    return [
        CandidateSchedule(
            candidate_id="A",
            score=0.6,
            hard_ok=True,
            soft_breakdown={"award_rate": 0.4, "layovers": 0.2},
            pairings=["A"],
        ),
        CandidateSchedule(
            candidate_id="B",
            score=0.5,
            hard_ok=True,
            soft_breakdown={"award_rate": 0.1, "layovers": 0.4},
            pairings=["B"],
        ),
    ]


def test_retune_idempotent():
    cands = _toy_candidates()
    retuned = retune_candidates(cands, {})
    assert [c.candidate_id for c in retuned] == ["A", "B"]
    assert retuned[0].score == pytest.approx(0.6)
    assert retuned[1].score == pytest.approx(0.5)


def test_retune_monotonic():
    cands = _toy_candidates()
    retuned = retune_candidates(cands, {"layovers": 1.0})
    assert [c.candidate_id for c in retuned] == ["B", "A"]
    assert retuned[0].score > retuned[1].score
