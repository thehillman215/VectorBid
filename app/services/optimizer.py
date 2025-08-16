from __future__ import annotations
from typing import List, Tuple
from operator import itemgetter
import heapq

from app.models import FeatureBundle, CandidateSchedule

def select_topk(bundle: FeatureBundle, K: int) -> List[CandidateSchedule]:
    """
    Behavior-identical top-K selection:
    - Same scoring as before (award_rate + weighted layover preference)
    - Deterministic/stable for equal scores: earlier input order wins ties
    - O(N log K) vs O(N log N)
    """
    prefs = bundle.preference_schema.soft_prefs or {}
    layovers = (prefs.get("layovers") or {})
    prefer = set(layovers.get("prefer") or [])
    avoid = set(layovers.get("avoid") or [])

    default_weights = bundle.context.default_weights or {}
    w = layovers.get("weight")
    if w is None:
        w = default_weights.get("layovers", 1.0)

    base_stats = (bundle.analytics_features.base_stats or {})
    bs_get = base_stats.get

    items: List[Tuple[float, int, str]] = []
    for i, p in enumerate(bundle.pairing_features.pairings):
        city = p.layover_city
        st = bs_get(city) or {}
        award = st.get("award_rate", 0.5)

        if city in prefer:
            pref_score = 1.0
        elif city in avoid:
            pref_score = 0.0
        else:
            pref_score = 0.5

        score = award + w * pref_score
        # Deterministic tie-break: earlier input index wins
        items.append((score, -i, p.id))

    # Higher is better: key = (score desc, -i desc)
    winners = heapq.nlargest(K, items, key=itemgetter(0, 1))
    return [CandidateSchedule(candidate_id=pid, score=score) for (score, _neg_i, pid) in winners]
