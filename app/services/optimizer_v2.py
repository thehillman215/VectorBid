from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from pydantic import BaseModel, Field
except Exception:

    class BaseModel:
        def __init__(self, **data):
            self.__dict__.update(data)

        def model_dump(self):
            return dict(self.__dict__)

    def Field(default_factory=None):
        return default_factory() if callable(default_factory) else default_factory


# === Public surface expected by tests ===
SCORING_CATEGORIES: tuple[str, ...] = (
    "layovers",
    "award_rate",
    "text_relevance",
    "contract_compliance",
    "fatigue_risk",
    "seniority_bonus",
    "historic_success",
    "recency",
    "diversity",
)
__all__ = [
    "rank_candidates",
    "select_topk",
    "SCORING_CATEGORIES",
    "_get_scoring_weights",
]

# --- Optional v1/v2 backends (kept for lower-level tests) ---
try:
    from .optimizer_v1 import rank_candidates as _rank_v1
except Exception:
    _rank_v1 = None
try:
    from .optimizer_v2 import rank_candidates as _rank_v2
except Exception:
    _rank_v2 = None

# === Utils ===
_ID_KEYS = ("id", "candidate_id", "uuid", "pk")
_TOKEN_FIELDS = ("text", "name", "title", "content", "body", "summary")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _coerce_id(d: Mapping[str, Any]) -> str:
    for k in _ID_KEYS:
        v = d.get(k)
        if v is not None:
            return str(v)
    return str(d.get("id") or d)


def _tokenize(s: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(s or "")]


def _extract_text_blob(item: Mapping[str, Any]) -> str:
    for k in _TOKEN_FIELDS:
        v = item.get(k)
        if isinstance(v, str) and v:
            return v
    return " ".join([v for v in item.values() if isinstance(v, str)])


def _as_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return dict(obj)
    for attr in ("model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return dict(fn())
            except Exception:
                pass
    try:
        import dataclasses

        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
    except Exception:
        pass
    return dict(getattr(obj, "__dict__", {}))


def _get_in(obj: Any, *path: str, default: Any = None) -> Any:
    cur = obj
    for p in path:
        cur = (
            cur.get(p, default)
            if isinstance(cur, Mapping)
            else getattr(cur, p, default)
        )
        if cur is default:
            break
    return cur


# === Weights API ===
def _derive_defaults_from_bundle(bundle_like: Any) -> dict[str, float]:
    """
    If context.default_weights is empty/zeroed, bootstrap sensible defaults:
      - layovers: from preference_schema.soft_prefs.layovers.weight (or 1.0 if 'prefer' exists)
      - award_rate: 1.0 if analytics.base_stats present
    """
    out: dict[str, float] = {}
    prefs = _get_in(bundle_like, "preference_schema") or {}
    p_lay = _get_in(prefs, "soft_prefs", "layovers", "weight")
    prefer = _get_in(prefs, "soft_prefs", "layovers", "prefer", default=[])
    if isinstance(p_lay, int | float) and p_lay > 0:
        out["layovers"] = float(p_lay)
    elif isinstance(prefer, Sequence) and len(prefer) > 0:
        out["layovers"] = 1.0
    analytics = _get_in(bundle_like, "analytics_features") or {}
    base_stats = _get_in(analytics, "base_stats", default={})
    if isinstance(base_stats, Mapping) and base_stats:
        out["award_rate"] = 1.0
    return out


def _get_scoring_weights(
    bundle_or_categories: Sequence[str] | Mapping[str, Any] | Any | None = None,
    overrides: Mapping[str, float] | None = None,
    *,
    normalize: bool = True,
) -> dict[str, float]:
    base: dict[str, float]
    is_bundle = bundle_or_categories is not None and (
        (
            isinstance(bundle_or_categories, Mapping)
            and "context" in bundle_or_categories
        )
        or hasattr(bundle_or_categories, "context")
    )
    if is_bundle:
        ctx = _get_in(bundle_or_categories, "context")
        ctxd = _as_dict(ctx)
        dw = ctxd.get("default_weights") or {}
        if not isinstance(dw, Mapping):
            dw = {}
        # start with context defaults
        base = {}
        for k, v in dict(dw).items():
            if isinstance(v, int | float) and v > 0:
                base[str(k)] = float(v)
        # if nothing positive, derive from prefs/analytics
        if sum(base.values()) <= 0:
            base.update(_derive_defaults_from_bundle(bundle_or_categories))
        # persona: family_first => bump layovers and downweight award_rate (pre-normalization)
        persona = _get_in(
            bundle_or_categories, "preference_schema", "source", "persona"
        )
        if isinstance(persona, str) and persona.lower() == "family_first":
            base["layovers"] = base.get("layovers", 0.0) + 2.0
            base["award_rate"] = base.get("award_rate", 0.0) * 0.5
    else:
        cats = (
            tuple(bundle_or_categories) if bundle_or_categories else SCORING_CATEGORIES
        )
        base = {str(c): 1.0 for c in cats}
    # allow overrides to introduce new keys
    if overrides:
        for k, v in overrides.items():
            try:
                base[str(k)] = float(v)
            except Exception:
                continue
    # Keep only positive-weighted categories for normalization
    if normalize:
        pos = {k: v for k, v in base.items() if v > 0}
        if pos:
            s = sum(pos.values())
            base = {k: (v / s) for k, v in pos.items()}
        else:
            # fallback uniform across two primary knobs to avoid 1/9 dilution
            base = {"layovers": 0.5, "award_rate": 0.5}
    return base


# === Low-level rank_candidates (kept) ===
def _normalize_v2_to_v1(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        rid = _coerce_id(it)
        try:
            score = float(it.get("score", 0))
        except Exception:
            score = 0.0
        m = dict(it)
        m["id"] = rid
        m["score"] = score
        out.append(m)
    out.sort(key=lambda x: (-x["score"], x["id"]))
    return out


def _fallback_v1_rank(
    candidates: Sequence[Mapping[str, Any]],
    query: str | Any,
    *,
    top_k: int = 10,
    strategy: str = "bm25",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    q = str(query) if not isinstance(query, str) else query
    q_tokens = _tokenize(q) or ["*"]
    q_weight = {
        t: 1.0 / (1.0 + math.log1p(i)) for i, t in enumerate(sorted(set(q_tokens)))
    }
    scored = []
    for it in candidates:
        rid = _coerce_id(it)
        toks = _tokenize(_extract_text_blob(it))
        score = (
            0.0
            if not toks
            else sum(q_weight.get(t, 1.0) for t in (set(q_tokens) & set(toks)))
            / (1.0 + 0.1 * len(toks))
        )
        m = {"id": rid, "score": float(score)}
        for k, v in it.items():
            if k not in m:
                m[k] = v
        scored.append(m)
    scored.sort(key=lambda x: (-x["score"], x["id"]))
    return scored[:top_k]


def rank_candidates(
    candidates: Sequence[Mapping[str, Any]],
    query: str | Any,
    *,
    top_k: int = 10,
    strategy: str = "bm25",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    use_v2 = os.getenv("OPTIMIZER_V2", "0") == "1" and callable(_rank_v2)
    if use_v2:
        out = _rank_v2(
            candidates=candidates,
            query=str(query),
            top_k=top_k,
            strategy=strategy,
            **kwargs,
        )
        return _normalize_v2_to_v1(out)[:top_k]
    if callable(_rank_v1):
        out = _rank_v1(
            candidates=candidates,
            query=str(query),
            top_k=top_k,
            strategy=strategy,
            **kwargs,
        )
        norm = []
        for it in out:
            rid = _coerce_id(it)
            try:
                sc = float(it.get("score", 0))
            except Exception:
                sc = 0.0
            m = dict(it)
            m["id"] = rid
            m["score"] = sc
            norm.append(m)
        norm.sort(key=lambda x: (-x["score"], x["id"]))
        return norm[:top_k]
    return _fallback_v1_rank(
        candidates, query, top_k=top_k, strategy=strategy, **kwargs
    )[:top_k]


# === High-level select_topk ===
class RankedCandidate(BaseModel):
    candidate_id: str
    score: float
    rationale: str | None = None
    soft_breakdown: dict[str, float] = Field(default_factory=dict)
    pairings: list[str] = Field(default_factory=list)


def _extract_bundle(bundle: Any) -> dict[str, Any]:
    b = _as_dict(bundle)
    context = b.get("context") or _as_dict(getattr(bundle, "context", None))
    prefs = b.get("preference_schema") or _as_dict(
        getattr(bundle, "preference_schema", None)
    )
    analytics = b.get("analytics_features") or _as_dict(
        getattr(bundle, "analytics_features", None)
    )
    compliance = b.get("compliance_flags") or _as_dict(
        getattr(bundle, "compliance_flags", None)
    )
    pf = b.get("pairing_features") or _as_dict(
        getattr(bundle, "pairing_features", None)
    )
    pairings = pf.get("pairings") if isinstance(pf, Mapping) else None
    if pairings is None:
        pairings = _get_in(bundle, "pairing_features", "pairings", default=[])
    if not isinstance(pairings, Sequence):
        pairings = []
    pairings = [
        _as_dict(p) if not isinstance(p, Mapping) else dict(p) for p in pairings
    ]
    return {
        "context": _as_dict(context),
        "prefs": _as_dict(prefs),
        "analytics": _as_dict(analytics),
        "compliance": _as_dict(compliance),
        "pairings": pairings,
    }


def _score_pairing(
    p: Mapping[str, Any],
    ctx: Mapping[str, Any],
    prefs: Mapping[str, Any],
    analytics: Mapping[str, Any],
    W: Mapping[str, float],
) -> tuple[float, list[str], dict[str, float]]:
    notes = []
    bd = dict.fromkeys(SCORING_CATEGORIES, 0.0)  # exact key set

    # Layovers: 1.0 if explicit match; if data missing (no city or prefer list), neutral 0.5
    city = p.get("layover_city") or p.get("city")
    prefer = _get_in(prefs, "soft_prefs", "layovers", "prefer", default=[]) or _get_in(
        prefs, "layovers", "prefer", default=[]
    )
    lay_base = (
        0.5
        if (not prefer or not city)
        else (1.0 if (isinstance(prefer, Sequence) and city in prefer) else 0.0)
    )
    bd["layovers"] = W.get("layovers", 0.0) * lay_base
    if lay_base == 1.0:
        notes.append(f"+layovers({city})")

    # Award rate: neutral 0.5 if missing
    rate = _get_in(analytics, "base_stats", str(city), "award_rate", default=None)
    rate_missing = not isinstance(rate, int | float)
    if rate_missing:
        rate = 0.5
    bd["award_rate"] = W.get("award_rate", 0.0) * float(rate)

    # Fatigue penalty
    fatigue_w = W.get("fatigue_risk", 0.0)
    pen_raw = 0.0
    if fatigue_w:
        if bool(p.get("redeye", False)):
            pen_raw += 1.0
        rest = p.get("rest_hours")
        if isinstance(rest, int | float) and rest < 10:
            pen_raw += 0.5
        if pen_raw:
            bd["fatigue_risk"] = -fatigue_w * pen_raw
            notes.append("-fatigue")

    # Base score = sum of breakdown contributions (excl. seniority_bonus which we add below)
    base = sum(v for k, v in bd.items() if k != "seniority_bonus")

    # Seniority as additive bonus equal to 10% * base * percentile (keeps sum(breakdown)==score)
    sp = ctx.get("seniority_percentile")
    if isinstance(sp, int | float):
        sp_eff = (
            min(float(sp), 0.2) if rate_missing else float(sp)
        )  # slight dampening when analytics missing
        bd["seniority_bonus"] = 0.1 * sp_eff * base

    score = base + bd["seniority_bonus"]
    return score, notes, bd


def select_topk(
    bundle: Any, top_k: int = 10, *, strategy: str = "bm25", **kwargs: Any
) -> list[RankedCandidate]:
    parts = _extract_bundle(bundle)
    ctx, prefs, analytics, pairings = (
        parts["context"],
        parts["prefs"],
        parts["analytics"],
        parts["pairings"],
    )
    W = _get_scoring_weights(bundle, normalize=True)
    ranked = []
    for p in pairings:
        pid = _coerce_id(p)
        s, notes, bd = _score_pairing(p, ctx, prefs, analytics, W)
        ranked.append(
            RankedCandidate(
                candidate_id=pid,
                score=float(s),
                rationale="; ".join(notes) if notes else "baseline",
                soft_breakdown=bd,
                pairings=[pid],
            )
        )
    ranked.sort(key=lambda x: (-x.score, x.candidate_id))
    return ranked[:top_k]
