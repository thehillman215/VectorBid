from __future__ import annotations
from typing import Any, Dict, List, Tuple
from operator import itemgetter
import heapq

from app.models import FeatureBundle, CandidateSchedule

def _to_dict(x: Any) -> Dict[str, Any]:
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

def select_topk(bundle: FeatureBundle, K: int) -> List[CandidateSchedule]:
    """
    Legacy-compatible Top-K selection:
    - DO NOT hard-filter here (legacy scored all pairings; later stages enforce rules)
    - Score = award_rate(city) + weight * pref(city) where pref∈{1.0, 0.5, 0.0}
    - Stable ties by earlier input order
    - O(N log K)
    """
    # soft prefs / weights
    prefs_d = _to_dict(_get(bundle.preference_schema, "soft_prefs", {}))
    layovers_d = _to_dict(prefs_d.get("layovers"))
    prefer = set(layovers_d.get("prefer") or [])
    avoid  = set(layovers_d.get("avoid") or [])

    default_weights_d = _to_dict(_get(bundle.context, "default_weights", {}))
    w = layovers_d.get("weight")
    if w is None:
        w = default_weights_d.get("layovers", 1.0)

    # award rates
    base_stats_d = _to_dict(_get(bundle.analytics_features, "base_stats", {}))

    items: List[Tuple[float, int, str]] = []
    for i, p in enumerate(_get(bundle.pairing_features, "pairings", []) or []):
        pid = _get(p, "id", "")
        city = _get(p, "layover_city", None)

        award = _to_dict(base_stats_d.get(city, {})).get("award_rate", 0.5)

        if city in prefer:
            pref_score = 1.0
        elif city in avoid:
            pref_score = 0.0
        else:
            pref_score = 0.5

        score = award + w * pref_score
        items.append((score, -i, pid))  # stable: earlier wins ties

    winners = heapq.nlargest(K, items, key=itemgetter(0, 1))

    # Keep pairings empty (legacy hashing behavior)
    return [
        CandidateSchedule(
            candidate_id=pid,
            score=award,
            hard_ok=True,
            soft_breakdown={},
            pairings=[],
        )
        for (score, _neg_i, pid) in winners
    ]
