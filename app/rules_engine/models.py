"""
Rule engine data models.

Immutable, frozen dataclasses for rule packs, rules, and validation results.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel


class HardRule(BaseModel):
    """Hard constraint that must be satisfied."""

    name: str
    description: str
    check: str  # DSL expression that must evaluate to True
    severity: str = "error"  # error, warning
    bounds: tuple[float, float] | None = None


class SoftRule(BaseModel):
    """Soft preference that affects scoring."""

    name: str
    description: str
    weight: float
    score: str  # DSL expression that returns a score
    bounds: tuple[float, float] | None = None


class DerivedRule(BaseModel):
    """Computed field derived from other data."""

    name: str
    description: str
    compute: str  # DSL expression that computes a value
    output_type: str = "float"  # float, int, str, bool


class RulePack(BaseModel):
    """Collection of rules for a specific contract period."""

    version: str
    airline: str
    contract_period: str
    base: str | None
    fleet: str | None
    effective_start: date
    effective_end: date | None
    hard_rules: list[HardRule] = []
    soft_rules: list[SoftRule] = []
    derived_rules: list[DerivedRule] = []
    metadata: dict[str, Any] = {}


class Violation(BaseModel):
    """Rule violation details."""

    rule_name: str
    rule_type: str  # hard, soft, derived
    message: str
    severity: str
    data_excerpt: str | None = None
    fix_hint: str | None = None
    ctx_id: str | None = None


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for soft rules."""

    total: float
    components: dict[str, float]  # rule_name -> score
