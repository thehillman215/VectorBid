from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.models import FeatureBundle
from app.rules.models import RulePack
from app.audit import log_event
from app.db import Preference, Pilot, RulePack as RulePackModel, SessionLocal

DEFAULT_RULES: dict[str, Any] = {
    "hard": [
        {
            "id": "rest_min_10",
            "desc": "Rest >= 10h",
            "check": "pairing.rest_hours >= 10",
        }
    ],
    "soft": [],
}

_RULE_CACHE: dict[str, dict[str, Any]] = {}
_PAIRING_CACHE: dict[
    tuple[str, str, str, str, str, str], tuple[tuple[str, ...], dict[str, Any]]
] = {}


def _cache_key(bundle: FeatureBundle) -> tuple[str, str, str, str, str, str]:
    ctx = bundle.context
    pairings = bundle.pairing_features.get("pairings", []) or []
    month = ""
    for p in pairings:
        m = p.get("month")
        if m:
            month = str(m)
            break
    equip = ",".join(sorted(ctx.equip))
    return (ctx.airline, month, ctx.base, equip, ctx.seat, ctx.pilot_id)


def _merge_sections(data: dict[str, Any]) -> dict[str, Any]:
    hard: list[dict[str, Any]] = []
    soft: list[dict[str, Any]] = []
    for section in ("far117", "union"):
        sec = data.get(section) or {}
        hard.extend(sec.get("hard") or [])
        soft.extend(sec.get("soft") or [])
    return {"hard": hard, "soft": soft}


def load_rule_pack(path: str, force_reload: bool = False) -> dict[str, Any]:
    """Load a YAML rule pack and merge sections to hard/soft lists.

    Returns DEFAULT_RULES when the file is missing or malformed. Results are
    cached by absolute path unless ``force_reload`` is True.
    """

    pth = Path(path)
    if not pth.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        pth = repo_root / path
    pth = pth.resolve()
    key = str(pth)
    if not force_reload and key in _RULE_CACHE:
        return _RULE_CACHE[key]
    if not pth.exists():
        logging.error("rule pack not found for %s", path)
        _RULE_CACHE[key] = DEFAULT_RULES
        return DEFAULT_RULES
    try:
        with pth.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        try:
            rp = RulePack.model_validate(data)
        except ValidationError as e:
            logging.error("invalid rule pack %s: %s", path, e)
            _RULE_CACHE[key] = DEFAULT_RULES
            return DEFAULT_RULES
        merged = _merge_sections(rp.model_dump())
        if not merged["hard"] or not merged["soft"]:
            logging.error("rule pack missing required keys")
            _RULE_CACHE[key] = DEFAULT_RULES
            return DEFAULT_RULES
        _RULE_CACHE[key] = merged
        return merged
    except Exception as e:  # pragma: no cover - unexpected YAML issues
        logging.error("error loading rule pack %s: %s", path, e)
        _RULE_CACHE[key] = DEFAULT_RULES
        return DEFAULT_RULES


def validate_feasibility(bundle: FeatureBundle, rules: dict[str, Any]) -> dict[str, Any]:
    """Very small feasibility check used by tests.

    Flags pairings that are red-eyes when the preference disallows them or
    whose rest_hours fall below 10. Returns a dict with ``violations`` and
    ``feasible_pairings`` lists.
    """

    key = _cache_key(bundle)
    pref = bundle.preference_schema.model_dump()
    pairings = bundle.pairing_features.get("pairings", [])
    no_red = pref.get("hard_constraints", {}).get("no_red_eyes")
    sig = tuple(sorted(p.get("id", "") for p in pairings))

    cached = _PAIRING_CACHE.get(key)
    if cached and cached[0] == sig:
        base = cached[1]
    else:
        base_violations: list[dict[str, Any]] = []
        base_feasible: list[dict[str, Any]] = []
        for p in pairings:
            pid = p.get("id")
            if p.get("rest_hours", 999) < 10:
                base_violations.append({"pairing_id": pid, "rule": "FAR117_MIN_REST"})
            else:
                base_feasible.append(p)
        base = {"violations": base_violations, "feasible_pairings": base_feasible}
        _PAIRING_CACHE[key] = (sig, base)

    violations: list[dict[str, Any]] = list(base["violations"])
    feasible: list[dict[str, Any]] = []
    for p in base["feasible_pairings"]:
        if no_red and p.get("redeye"):
            violations.append({"pairing_id": p.get("id"), "rule": "NO_REDEYE_IF_SET"})
        else:
            feasible.append(p)

    ctx = bundle.context
    with SessionLocal() as db:
        db.merge(Pilot(pilot_id=ctx.pilot_id))
        db.add(
            Preference(
                ctx_id=ctx.ctx_id,
                pilot_id=ctx.pilot_id,
                data=bundle.preference_schema.model_dump(),
            )
        )
        db.add(
            RulePackModel(
                ctx_id=ctx.ctx_id,
                airline=ctx.airline,
                version="",  # version unknown
                data=rules,
            )
        )
        db.commit()

    log_event(ctx.ctx_id, "validate", {"violations": len(violations)})

    return {"violations": violations, "feasible_pairings": feasible}
