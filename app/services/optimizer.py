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
    md = getattr(x, "model_dump", None)
    if callable(md):
        try:
            return md()
        except Exception:
            pass
    try:
        return dict(x)  # type: ignore[arg-type]
    except Exception:
        pass
    try:
        return {k: v for k, v in vars(x).items() if not k.startswith("_")}
    except Exception:
        return {}

def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def select_topk(bundle: FeatureBundle, K: int) -> List[CandidateSchedule]:
    """
    award_rate + weighted layover preference, stable ties (earlier input wins),
    O(N log K). Tolerates dicts or Pydantic models throughout.
    """
    # prefs / layovers
    prefs_d = _to_dict(_get(bundle.preference_schema, "soft_prefs"))
    layovers_d = _to_dict(_get(prefs_d, "layovers"))

    prefer = set(_get(layovers_d, "prefer", []) or [])
    avoid  = set(_get(layovers_d, "avoid", []) or [])

    # weight: layovers.weight -> context.default_weights["layovers"] -> 1.0
    default_weights_d = _to_dict(_get(bundle.context, "default_weights"))
    w = _get(layovers_d, "weight", None)
    if w is None:
        w = _get(default_weights_d, "layovers", 1.0)

    # base stats: dict(city -> {award_rate})
    base_stats_d = _to_dict(_get(bundle.analytics_features, "base_stats", {}))

    # pairings list (dict or model)
    pf = _to_dict(_get(bundle, "pairing_features"))
    pairings = pf.get("pairings")
    if pairings is None:
        pairings = _get(_get(bundle, "pairing_features"), "pairings", [])
    pairings = pairings or []

    items: List[Tuple[float, int, str]] = []
    for i, p in enumerate(pairings):
        d = _to_dict(p)
        pid  = d.get("id")
        city = d.get("layover_city")
        if not pid or not city:
            continue

        award = _to_dict(base_stats_d.get(city) or {}).get("award_rate", 0.5)
        pref_score = 1.0 if city in prefer else (0.0 if city in avoid else 0.5)
        score = award + w * pref_score

        # Deterministic tie-breaker: earlier index wins
        items.append((score, -i, pid))

    winners = heapq.nlargest(K, items, key=itemgetter(0, 1))

    # Build full CandidateSchedule objects (fields required by the model)
    return [
        CandidateSchedule(
            candidate_id=pid,
            score=score,
            hard_ok=True,
            soft_breakdown={},
            pairings=[],
        )
        for (score, _neg_i, pid) in winners
    ]
