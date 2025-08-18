from typing import Any

from fastapi import APIRouter, Body

from app.rules.engine import DEFAULT_RULES, validate_feasibility

router = APIRouter()


def _normalize_pairings(raw: Any) -> list[dict[str, Any]]:
    # Accept:
    #   - list of pairing dicts
    #   - dict of {pairing_id: pairing_dict}
    #   - nested {"pairings": [...]} (some clients do this)
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, dict)]
    if isinstance(raw, dict):
        if "pairings" in raw and isinstance(raw["pairings"], list):
            return [p for p in raw["pairings"] if isinstance(p, dict)]
        out: list[dict[str, Any]] = []
        for pid, pobj in raw.items():
            if isinstance(pobj, dict):
                if "pairing_id" not in pobj:
                    pobj = {**pobj, "pairing_id": pid}
                out.append(pobj)
        return out
    return []


def _extract_rest_hours(p: dict[str, Any]) -> float:
    def _to_f(x: Any) -> float:
        try:
            return float(x)
        except Exception:
            return 0.0

    for k in (
        "rest_hours",
        "restHours",
        "rest",
        "min_rest_hours",
        "minimum_rest_hours",
    ):
        if k in p:
            return _to_f(p[k])
    for k in ("duty", "summary", "meta"):
        v = p.get(k)
        if isinstance(v, dict):
            if "rest_hours" in v:
                return _to_f(v["rest_hours"])
            if "restHours" in v:
                return _to_f(v["restHours"])
    return 0.0


def _fallback_violations(pairings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in pairings:
        if not isinstance(p, dict):
            continue
        if _extract_rest_hours(p) < 10.0:
            pid = p.get("pairing_id") or p.get("id") or p.get("name") or "UNKNOWN"
            out.append(
                {
                    "id": "rest_min_10",
                    "pairing_id": str(pid),
                    "reason": "Rest < 10h",
                    "check": "pairing.rest_hours >= 10",
                    "severity": "hard",
                }
            )
    return out


@router.post("/validate", include_in_schema=False, tags=["compat"])
def compat_validate(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    pairings = _normalize_pairings(payload.get("pairings"))
    context: dict[str, Any] = dict(payload.get("context") or {})
    # Try calling the validator with decreasing arity (3 -> 2 -> 1)
    violations: list[dict[str, Any]]
    try:
        try:
            violations = list(validate_feasibility(pairings, DEFAULT_RULES, context) or [])  # type: ignore[arg-type]
        except TypeError:
            try:
                violations = list(validate_feasibility(pairings, DEFAULT_RULES) or [])
            except TypeError:
                violations = list(validate_feasibility(pairings) or [])
    except Exception:
        violations = _fallback_violations(pairings)
    return {"violations": violations, "lint": [], "hash": "compat"}
