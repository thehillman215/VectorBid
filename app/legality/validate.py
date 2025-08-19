from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field


class Rule(BaseModel):
    id: str
    desc: str
    clause: str
    severity: str
    evaluate: str


class RuleHit(BaseModel):
    id: str
    desc: str
    clause: str
    severity: str
    trip_id: str | None = None


class ValidationReport(BaseModel):
    valid_trips: list[dict[str, Any]] = Field(default_factory=list)
    rule_hits: list[RuleHit] = Field(default_factory=list)


def _load_rules() -> list[Rule]:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "rule_packs" / "UAL" / "2025.09.yml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [Rule.model_validate(r) for r in data.get("rules", [])]


_RULES = _load_rules()


def validate(trips: list[dict[str, Any]], context: dict[str, Any]) -> ValidationReport:
    """Validate trips against hard legality rules.

    Trips with hard rule hits are excluded from the returned ``valid_trips``.
    ``rule_hits`` include clause references for downstream reporting.
    """

    rule_hits: list[RuleHit] = []
    valid_trips: list[dict[str, Any]] = []

    for trip in trips:
        trip_hits: list[RuleHit] = []
        for rule in _RULES:
            if "trip" in rule.evaluate:
                env = {"trip": trip, "context": context}
                ok = bool(eval(rule.evaluate, {}, env))  # noqa: S307
                if not ok:
                    hit = RuleHit(
                        id=rule.id,
                        desc=rule.desc,
                        clause=rule.clause,
                        severity=rule.severity,
                        trip_id=trip.get("id"),
                    )
                    rule_hits.append(hit)
                    trip_hits.append(hit)
        if not any(h.severity == "hard" for h in trip_hits):
            valid_trips.append(trip)

    for rule in _RULES:
        if "trip" not in rule.evaluate:
            env = {"context": context}
            ok = bool(eval(rule.evaluate, {}, env))  # noqa: S307
            if not ok:
                rule_hits.append(
                    RuleHit(
                        id=rule.id,
                        desc=rule.desc,
                        clause=rule.clause,
                        severity=rule.severity,
                        trip_id=None,
                    )
                )

    return ValidationReport(valid_trips=valid_trips, rule_hits=rule_hits)
