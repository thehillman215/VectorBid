from __future__ import annotations

import heapq
import time
from operator import itemgetter
from typing import Any

from app.models import CandidateSchedule, FeatureBundle
from app.rules.engine import DEFAULT_RULES, validate_feasibility
from app.services.optimizer import (
    _generate_rationale,
    _get_scoring_weights,
    _get_seniority_adjustment,
    _score_block_hours,
    _score_commutability,
    _score_days_off,
    _score_duty_hours,
    _score_equipment,
    _score_layover_quality,
    _score_report_time,
    _score_trip_length,
)


def search(
    bundle: FeatureBundle,
    k: int,
    time_budget_ms: int,
    max_nodes: int = 1000,
) -> list[CandidateSchedule]:
    """Beam search over pairings with time and node limits.

    Parameters
    ----------
    bundle: FeatureBundle
        Input features including context, prefs, analytics and pairings.
    k: int
        Number of candidates to return.
    time_budget_ms: int
        Stop processing after this many milliseconds.
    max_nodes: int
        Maximum pairings to evaluate.

    Returns
    -------
    list[CandidateSchedule]
        Top ``k`` candidate schedules scored individually.
    """

    start = time.perf_counter()
    # Fetch feasible pairings with memoization via rules engine
    feas = validate_feasibility(bundle, DEFAULT_RULES)["feasible_pairings"]

    weights = _get_scoring_weights(bundle)
    seniority_factor = _get_seniority_adjustment(bundle)

    items: list[tuple[float, int, str, dict[str, float], Any]] = []
    for i, p in enumerate(feas):
        if i >= max_nodes:
            break
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms >= time_budget_ms:
            break
        pid = p.get("id", "")
        city = p.get("layover_city")
        award = (
            bundle.analytics_features.get("base_stats", {})
            .get(city, {})
            .get("award_rate", 0.5)
        )
        prefs_d = bundle.preference_schema.soft_prefs.model_dump()
        layover_pref = prefs_d.get("layovers") or {}
        prefer = set(layover_pref.get("prefer") or [])
        avoid = set(layover_pref.get("avoid") or [])
        pref_w = layover_pref.get("weight", 1.0)
        if city in prefer:
            pref_score = 1.0
        elif city in avoid:
            pref_score = 0.0
        else:
            pref_score = 0.5
        breakdown: dict[str, float] = {
            "award_rate": weights.get("award_rate", 0.0) * award,
            "layovers": weights.get("layovers", 0.0) * pref_w * pref_score,
            "days_off": _score_days_off(bundle, p, weights),
            "block_hours": _score_block_hours(p, weights),
            "duty_hours": _score_duty_hours(p, weights),
            "layover_quality": _score_layover_quality(p, weights),
            "report_time": _score_report_time(bundle, p, weights),
            "commutability": _score_commutability(p, weights),
            "trip_length": _score_trip_length(bundle, p, weights),
            "equipment": _score_equipment(bundle, p, weights),
        }
        score = sum(breakdown.values()) * seniority_factor
        items.append((score, -i, pid, breakdown, p))

    winners = heapq.nlargest(k, items, key=itemgetter(0, 1))
    result: list[CandidateSchedule] = []
    for winner_score, _neg_i, pid, breakdown, pairing in winners:
        result.append(
            CandidateSchedule(
                candidate_id=pid,
                score=winner_score,
                hard_ok=True,
                soft_breakdown=breakdown,
                pairings=[pid],
                rationale=_generate_rationale(pairing, breakdown),
            )
        )
    return result
