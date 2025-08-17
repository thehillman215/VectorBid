from __future__ import annotations

from typing import Any, Dict, Callable

from app.models import CandidateSchedule, FeatureBundle


# ---------------------------------------------------------------------------
# Individual scoring helpers
# ---------------------------------------------------------------------------
def _score_days_off(pairing: Dict[str, Any]) -> float:
    """Score based on consecutive days off after the trip.

    Missing information results in a neutral score of 0.5.
    """
    days = float(pairing.get("days_off", 0))
    # cap at 7 days for normalization
    return max(0.0, min(days / 7.0, 1.0)) if days else 0.5


def _score_block_hours(pairing: Dict[str, Any]) -> float:
    hours = float(pairing.get("block_hours", 0))
    # more block hours are generally better up to 30
    return max(0.0, min(hours / 30.0, 1.0)) if hours else 0.5


def _score_duty_hours(pairing: Dict[str, Any]) -> float:
    hours = float(pairing.get("duty_hours", 0))
    # fewer duty hours are preferred; 40h or more is worst
    return 1.0 - max(0.0, min(hours / 40.0, 1.0)) if hours else 0.5


def _score_layover_quality(pairing: Dict[str, Any]) -> float:
    # Assume layover quality already normalized 0-1
    score = pairing.get("layover_quality")
    return float(score) if isinstance(score, (int, float)) else 0.5


def _score_report_time(pairing: Dict[str, Any]) -> float:
    rt = pairing.get("report_time")  # hour of day 0-23
    if isinstance(rt, (int, float)):
        # prefer mid-morning reports around 10:00
        return max(0.0, min(1.0 - abs(rt - 10) / 10.0, 1.0))
    return 0.5


def _score_commutability(pairing: Dict[str, Any]) -> float:
    commutable = pairing.get("commutable")
    if commutable is True:
        return 1.0
    if commutable is False:
        return 0.0
    return 0.5


def _score_trip_length(pairing: Dict[str, Any]) -> float:
    length = pairing.get("trip_length")  # number of days
    if isinstance(length, (int, float)):
        # best between 2 and 4 days
        if 2 <= length <= 4:
            return 1.0
        return max(0.0, min(length / 7.0, 1.0))
    return 0.5


def _score_equipment(pairing: Dict[str, Any], equip_pref: list[str]) -> float:
    equip = pairing.get("equipment")
    if equip and equip_pref:
        return 1.0 if equip in equip_pref else 0.0
    return 0.5


# Default persona weight configuration.  Missing personas or weights fall back
# to these neutral values.  These weights can be overridden by context
# ``default_weights`` supplied at runtime.
FEATURES = [
    "days_off",
    "block_hours",
    "duty_hours",
    "layover_quality",
    "report_time",
    "commutability",
    "trip_length",
    "equipment",
]

DEFAULT_WEIGHTS: Dict[str, float] = {f: 1.0 for f in FEATURES}

PERSONA_WEIGHTS: Dict[str, Dict[str, float]] = {
    "family_first": {
        "days_off": 2.0,
        "commutability": 1.5,
        "trip_length": 1.2,
    },
    "money_maker": {
        "block_hours": 2.0,
        "duty_hours": 1.5,
    },
    "commuter_friendly": {
        "commutability": 2.0,
        "report_time": 1.5,
    },
    "quality_of_life": {
        "layover_quality": 1.5,
    },
    "reserve_avoider": {},
    "adventure_seeker": {
        "layover_quality": 1.2,
        "equipment": 1.2,
    },
}


def _combine_scores(
    breakdown: Dict[str, float],
    weights: Dict[str, float],
    seniority: float,
) -> float:
    total_weight = 0.0
    total_score = 0.0
    for key, score in breakdown.items():
        w = weights.get(key, 1.0)
        total_weight += w
        total_score += w * score
    if total_weight == 0:
        combined = 0.0
    else:
        combined = total_score / total_weight
    # Adjust for seniority (0-1) in a gentle way
    seniority_factor = 0.9 + 0.2 * max(0.0, min(seniority, 1.0))
    return max(0.0, min(combined * seniority_factor, 1.0))


def rank_candidates(
    bundle: FeatureBundle, feasible_pairings: list[Any], K: int = 50
) -> list[CandidateSchedule]:
    persona = (
        bundle.preference_schema.source.get("persona")
        if isinstance(bundle.preference_schema.source, dict)
        else None
    )
    ctx_weights = bundle.context.default_weights or {}
    weights = DEFAULT_WEIGHTS.copy()
    if persona in PERSONA_WEIGHTS:
        weights.update(PERSONA_WEIGHTS[persona])
    weights.update(ctx_weights)

    equip_pref = bundle.preference_schema.equip or []
    candidates: list[CandidateSchedule] = []

    scoring_funcs: Dict[str, Callable[[Dict[str, Any]], float]] = {
        "days_off": _score_days_off,
        "block_hours": _score_block_hours,
        "duty_hours": _score_duty_hours,
        "layover_quality": _score_layover_quality,
        "report_time": _score_report_time,
        "commutability": _score_commutability,
        "trip_length": _score_trip_length,
        # equipment needs access to prefs; handled separately below
    }

    for p in feasible_pairings:
        breakdown: Dict[str, float] = {}
        for key, func in scoring_funcs.items():
            breakdown[key] = func(p)
        breakdown["equipment"] = _score_equipment(p, equip_pref)

        total = _combine_scores(
            breakdown, weights, bundle.context.seniority_percentile
        )

        rationale = []
        for key, score in breakdown.items():
            if score >= 0.75:
                rationale.append(f"Strong {key.replace('_', ' ')}")
            elif score <= 0.25:
                rationale.append(f"Weak {key.replace('_', ' ')}")

        candidates.append(
            CandidateSchedule(
                candidate_id=p.get("id"),
                score=round(float(total), 6),
                hard_ok=True,
                soft_breakdown=breakdown,
                pairings=[p.get("id")],
                rationale=rationale,
            )
        )

    candidates.sort(key=lambda c: (-c.score, str(c.candidate_id)))
    return candidates[:K]
