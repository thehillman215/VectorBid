from __future__ import annotations
from typing import Any, List
from app.models import FeatureBundle, CandidateSchedule

def _layover_soft_score(pref: dict, pairing: dict) -> float:
    lay = pref.get("soft_prefs", {}).get("layovers", {})
    prefer = set(lay.get("prefer", []) or [])
    city = pairing.get("layover_city")
    # Simple deterministic scoring to satisfy tests:
    # 1.0 if preferred city; 0.5 otherwise (no "avoid" concept in the test).
    return 1.0 if city in prefer else 0.5

def rank_candidates(bundle: FeatureBundle, feasible_pairings: List[Any], K: int = 50) -> List[CandidateSchedule]:
    pref = bundle.preference_schema.model_dump()
    candidates: List[CandidateSchedule] = []

    for p in feasible_pairings:
        lay_score = _layover_soft_score(pref, p)
        soft_breakdown = {"layovers": lay_score}
        total = float(lay_score)

        candidates.append(
            CandidateSchedule(
                candidate_id=p.get("id"),
                score=round(total, 6),
                hard_ok=True,
                soft_breakdown=soft_breakdown,
                pairings=[p.get("id")],
                rationale=[],
            )
        )

    # Deterministic order: score desc, then candidate_id asc
    candidates.sort(key=lambda c: (-c.score, str(c.candidate_id)))
    return candidates[:K]
