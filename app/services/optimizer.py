from __future__ import annotations

import heapq
from operator import itemgetter
from typing import Any, Dict

from app.models import CandidateSchedule, FeatureBundle


def _generate_rationale(pairing: Any, breakdown: dict[str, float]) -> list[str]:
    """Create human readable rationale strings for the top scoring factors.

    Parameters
    ----------
    pairing: Any
        Pairing data that may contain attributes such as layover city. The
        current implementation only relies on the breakdown values but the
        argument is kept for future enrichment.
    breakdown: dict[str, float]
        Mapping of scoring category to its contribution toward the total
        score.

    Returns
    -------
    list[str]
        Up to three messages describing the largest contributions in
        descending order.
    """

    # Sort breakdown by contribution (descending) and take top three entries
    top_items = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)[:3]

    messages: list[str] = []
    for key, val in top_items:
        messages.append(f"{key} contributed {val:.2f}")

    return messages


def _to_dict(x: Any) -> dict[str, Any]:
    if x is None:
        return {}
    if isinstance(x, dict):
        return x
    if hasattr(x, "model_dump"):
        return x.model_dump()
    return {}

def _get(obj: Any, name: str, default=None):
    if obj is None:
        return default
    try:
        if hasattr(obj, name):
            return getattr(obj, name)
    except Exception:
        pass
    return _to_dict(obj).get(name, default)


DEFAULT_WEIGHTS: Dict[str, float] = {"award_rate": 1.0, "layovers": 1.0}

PERSONA_WEIGHTS: Dict[str, Dict[str, float]] = {
    "family_first": {"layovers": 1.2},
    "money_maker": {"award_rate": 1.2},
    "commuter_friendly": {"layovers": 1.1},
    "quality_of_life": {"layovers": 1.1},
    "reserve_avoider": {},
    "adventure_seeker": {"layovers": 1.2},
}


def _get_scoring_weights(bundle: FeatureBundle) -> Dict[str, float]:
    """Return normalized scoring weights for available factors."""

    source_d = _to_dict(_get(bundle.preference_schema, "source", {}))
    persona = source_d.get("persona")

    weights = DEFAULT_WEIGHTS.copy()
    if persona in PERSONA_WEIGHTS:
        weights.update(PERSONA_WEIGHTS[persona])

    ctx_weights = _to_dict(_get(bundle.context, "default_weights", {}))
    weights.update(ctx_weights)

    total = sum(weights.values()) or 1.0
    for k in list(weights.keys()):
        weights[k] = weights[k] / total
    return weights


def _get_seniority_adjustment(bundle: FeatureBundle) -> float:
    """Return multiplier based on pilot seniority."""

    seniority = float(_get(bundle.context, "seniority_percentile", 0.0) or 0.0)
    seniority = max(0.0, min(seniority, 1.0))
    return 0.9 + 0.2 * seniority

def select_topk(bundle: FeatureBundle, K: int) -> list[CandidateSchedule]:
    """
    Legacy-compatible Top-K selection:
    - DO NOT hard-filter here (legacy scored all pairings; later stages enforce rules)
    - Score = award_rate(city) + weight * pref(city) where pref∈{1.0, 0.5, 0.0}
    - Stable ties by earlier input order
    - O(N log K)
    """
    weights = _get_scoring_weights(bundle)
    seniority_factor = _get_seniority_adjustment(bundle)

    # soft prefs / weights
    prefs_d = _to_dict(_get(bundle.preference_schema, "soft_prefs", {}))
    layovers_d = _to_dict(prefs_d.get("layovers"))
    prefer = set(layovers_d.get("prefer") or [])
    avoid = set(layovers_d.get("avoid") or [])
    pref_w = layovers_d.get("weight", 1.0)

    # award rates
    base_stats_d = _to_dict(_get(bundle.analytics_features, "base_stats", {}))

    items: list[tuple[float, int, str, dict[str, float], Any]] = []
    pairings = _get(bundle.pairing_features, "pairings", []) or []
    for i, p in enumerate(pairings):
        pid = _get(p, "id", "")
        city = _get(p, "layover_city", None)

        award = _to_dict(base_stats_d.get(city, {})).get("award_rate", 0.5)

        if city in prefer:
            pref_score = 1.0
        elif city in avoid:
            pref_score = 0.0
        else:
            pref_score = 0.5

        breakdown = {
            "award_rate": weights.get("award_rate", 0.0) * award,
            "layovers": weights.get("layovers", 0.0) * pref_w * pref_score,
        }
        score = sum(breakdown.values()) * seniority_factor
        items.append((score, -i, pid, breakdown, p))  # stable: earlier wins ties

    winners = heapq.nlargest(K, items, key=itemgetter(0, 1))

    # Keep pairings empty (legacy hashing behavior)
    result: list[CandidateSchedule] = []
    for winner_score, _neg_i, pid, breakdown, pairing in winners:
        result.append(
            CandidateSchedule(
                candidate_id=pid,
                score=winner_score,
                hard_ok=True,
                soft_breakdown=breakdown,
                pairings=[],
                rationale=_generate_rationale(pairing, breakdown),
            )
        )
    return result
