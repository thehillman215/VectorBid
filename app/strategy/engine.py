from __future__ import annotations

from app.models import CandidateSchedule, FeatureBundle, StrategyDirectives

MAX_DELTA = 0.15


def propose_strategy(bundle: FeatureBundle, topk: list[CandidateSchedule]) -> StrategyDirectives:
    """
    Heuristic, bounded strategy:
    - If top candidate benefits from layover prefs and there exists at least one candidate
      with a lower layover score, nudge layovers weight by +0.1 (bounded by ±0.15).
    - Otherwise, no-op.
    """
    delta = 0.0
    if topk:
        try:
            top_lay = float(topk[0].soft_breakdown.get("layovers", 0.0))
            min_lay = min(float(c.soft_breakdown.get("layovers", 0.0)) for c in topk)
            if top_lay > min_lay:
                delta = min(0.10, MAX_DELTA)
        except Exception:
            delta = 0.0

    return StrategyDirectives(
        weight_deltas={"layovers": delta} if delta else {},
        focus_hints={},
        layer_templates=[],
        rationale=([f"nudge layovers +{delta:.2f}"] if delta else ["no-op; bounded strategy gate"]),
    )
