from __future__ import annotations

import heapq
from operator import itemgetter
from typing import Any

from app.audit import log_event
from app.db import Candidate, SessionLocal
from app.models import CandidateRationale, CandidateSchedule, FeatureBundle


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


def _rule_hits_misses(bundle: FeatureBundle, pairing: Any) -> tuple[list[str], list[str]]:
    """Determine which hard rules are satisfied or violated."""

    hits: list[str] = []
    misses: list[str] = []

    hard = _to_dict(_get(bundle.preference_schema, "hard_constraints", {}))
    no_red = bool(hard.get("no_red_eyes"))

    rest_hours = float(_get(pairing, "rest_hours", 999) or 999)
    if rest_hours < 10:
        misses.append("FAR117_MIN_REST")
    else:
        hits.append("FAR117_MIN_REST")

    is_redeye = bool(_get(pairing, "redeye", False))
    if no_red and is_redeye:
        misses.append("NO_REDEYE_IF_SET")
    else:
        hits.append("NO_REDEYE_IF_SET")

    return hits, misses


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


DEFAULT_WEIGHTS: dict[str, float] = {"award_rate": 1.0, "layovers": 1.0}

PERSONA_WEIGHTS: dict[str, dict[str, float]] = {
    "family_first": {"layovers": 1.2},
    "money_maker": {"award_rate": 1.2},
    "commuter_friendly": {"layovers": 1.1},
    "quality_of_life": {"layovers": 1.1},
    "reserve_avoider": {},
    "adventure_seeker": {"layovers": 1.2},
}


def _get_scoring_weights(bundle: FeatureBundle) -> dict[str, float]:
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


def _score_days_off(bundle: FeatureBundle, pairing: Any, weights: dict[str, float]) -> float:
    """Score whether pairing avoids requested days off."""

    req = set(
        _to_dict(_get(_get(bundle.preference_schema, "hard_constraints", {}), "days_off", [])) or []
    )
    pairing_days = set(_get(pairing, "dates", []) or _get(pairing, "duty_days", []) or [])
    if not req or not pairing_days:
        base = 0.0
    else:
        base = 1.0 if not req.intersection(pairing_days) else 0.0
    return weights.get("days_off", 0.0) * base


def _score_block_hours(pairing: Any, weights: dict[str, float]) -> float:
    """Favor higher block or credit hours."""

    block = float(_get(pairing, "block_hours", _get(pairing, "credit_hours", 0.0)) or 0.0)
    base = min(block, 100.0) / 100.0
    return weights.get("block_hours", 0.0) * base


def _score_duty_hours(pairing: Any, weights: dict[str, float]) -> float:
    """Higher score for lower duty hours."""

    duty = float(_get(pairing, "duty_hours", _get(pairing, "duty_time", 0.0)) or 0.0)
    if duty <= 0:
        base = 0.0
    else:
        base = max(0.0, 1.0 - min(duty, 16.0) / 16.0)
    return weights.get("duty_hours", 0.0) * base


def _score_layover_quality(pairing: Any, weights: dict[str, float]) -> float:
    """Use rest hours as a proxy for layover quality."""

    rest = float(_get(pairing, "rest_hours", _get(pairing, "layover_rest_hours", 0.0)) or 0.0)
    base = min(rest, 24.0) / 24.0
    return weights.get("layover_quality", 0.0) * base


def _score_report_time(bundle: FeatureBundle, pairing: Any, weights: dict[str, float]) -> float:
    """Score later report times higher."""

    time_str = _get(pairing, "report_time", "") or ""
    digits = str(time_str).replace(":", "")
    if len(digits) == 4 and digits.isdigit():
        minutes = int(digits[:2]) * 60 + int(digits[2:])
        base = minutes / (24 * 60)
    else:
        base = 0.0
    return weights.get("report_time", 0.0) * base


def _score_commutability(pairing: Any, weights: dict[str, float]) -> float:
    """Binary score if pairing is marked commutable."""

    is_commutable = _get(pairing, "is_commutable", None)
    if is_commutable is None:
        base = 0.0
    else:
        base = 1.0 if is_commutable else 0.0
    return weights.get("commutability", 0.0) * base


def _score_trip_length(bundle: FeatureBundle, pairing: Any, weights: dict[str, float]) -> float:
    """Score against preferred trip lengths."""

    prefs_d = _to_dict(_get(bundle.preference_schema, "soft_prefs", {}))
    length_d = _to_dict(prefs_d.get("pairing_length"))
    prefer = set(length_d.get("prefer") or [])
    avoid = set(length_d.get("avoid") or [])
    pref_w = float(length_d.get("weight", 1.0) or 1.0)
    length = int(
        _get(
            pairing,
            "trip_length",
            _get(pairing, "days", _get(pairing, "duration_days", 0)),
        )
        or 0
    )
    if length == 0:
        base = 0.0
    elif length in prefer:
        base = 1.0
    elif length in avoid:
        base = 0.0
    else:
        base = 0.5
    return weights.get("trip_length", 0.0) * pref_w * base


def _score_equipment(bundle: FeatureBundle, pairing: Any, weights: dict[str, float]) -> float:
    """Score if the pairing's equipment matches pilot preferences."""

    desired = set(_get(bundle.preference_schema, "equip", []) or [])
    equip = _get(pairing, "equipment", _get(pairing, "equip", None))
    if not equip or not desired:
        base = 0.0
    else:
        base = 1.0 if equip in desired else 0.0
    return weights.get("equipment", 0.0) * base


def select_topk(bundle: FeatureBundle, K: int = 50) -> list[CandidateSchedule]:
    """
    Legacy-compatible Top-K selection:
    - DO NOT hard-filter here (legacy scored all pairings; later stages enforce rules)
    - Score = award_rate(city) + weight * pref(city) where pref∈{1.0, 0.5, 0.0}
    - Stable ties by earlier input order
    - O(N log K)
    """
    weights = _get_scoring_weights(bundle)
    seniority_factor = _get_seniority_adjustment(bundle)

    # soft prefs / weights for layovers
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
        items.append((score, -i, pid, breakdown, p))  # stable: earlier wins ties

    winners = heapq.nlargest(K, items, key=itemgetter(0, 1))

    result: list[CandidateSchedule] = []
    for winner_score, _neg_i, pid, breakdown, pairing in winners:
        hits, misses = _rule_hits_misses(bundle, pairing)
        result.append(
            CandidateSchedule(
                candidate_id=pid,
                score=winner_score,
                hard_ok=len(misses) == 0,
                soft_breakdown=breakdown,
                pairings=[pid],
                rationale=CandidateRationale(
                    hard_hits=hits,
                    hard_misses=misses,
                    notes=_generate_rationale(pairing, breakdown),
                ),
            )
        )

    ctx_id = bundle.context.ctx_id
    with SessionLocal() as db:
        for cand in result:
            db.add(Candidate(ctx_id=ctx_id, data=cand.model_dump()))
        db.commit()

    log_event(ctx_id, "optimize", {"candidates": [c.candidate_id for c in result]})

    return result


def retune_candidates(
    candidates: list[CandidateSchedule], weight_deltas: dict[str, float]
) -> list[CandidateSchedule]:
    """Re-score already feasible candidates with lightweight weight tweaks.

    Parameters
    ----------
    candidates:
        List of pre-computed feasible candidates, typically output from
        :func:`select_topk`. Each candidate must contain a ``soft_breakdown``
        with the contribution of every scoring factor.
    weight_deltas:
        Mapping of factor name to a *relative* weight adjustment. The new
        contribution for factor ``k`` becomes ``breakdown[k] * (1 + delta)``.

    Returns
    -------
    list[CandidateSchedule]
        Candidates with updated ``score`` and ``soft_breakdown`` fields,
        sorted in descending score order. No feasibility checks or parsing is
        performed; this function is purely a stateless reweighting step and
        runs in O(N·F) where ``F`` is the number of scoring factors. With 50
        candidates it completes well under 150 ms on commodity hardware.
    """

    adjusted: list[CandidateSchedule] = []
    for cand in candidates:
        new_breakdown: dict[str, float] = {}
        for key, val in cand.soft_breakdown.items():
            factor = 1.0 + float(weight_deltas.get(key, 0.0))
            new_breakdown[key] = val * factor

        new_score = sum(new_breakdown.values())
        adjusted.append(
            cand.model_copy(
                update={
                    "score": new_score,
                    "soft_breakdown": new_breakdown,
                    "rationale": _generate_rationale(None, new_breakdown),
                }
            )
        )

    adjusted.sort(key=lambda c: c.score, reverse=True)
    return adjusted
