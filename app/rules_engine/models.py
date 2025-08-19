"""
Rule engine data models.

Immutable, frozen dataclasses for rule packs, rules, and validation results.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional, Union

from pydantic import BaseModel


class HardRule(BaseModel):
    """Hard constraint that must be satisfied."""

    name: str
    description: str
    check: str  # DSL expression that must evaluate to True
    severity: str = "error"  # error, warning
    bounds: Optional[tuple[float, float]] = None


class SoftRule(BaseModel):
    """Soft preference that affects scoring."""

    name: str
    description: str
    weight: float
    score: str  # DSL expression that returns a score
    bounds: Optional[tuple[float, float]] = None


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
    base: Optional[str] = None
    fleet: Optional[str] = None
    effective_start: date
    effective_end: Optional[date] = None
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
    data_excerpt: Optional[str] = None
    fix_hint: Optional[str] = None
    ctx_id: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for soft rules."""

    total: float
    components: dict[str, float]  # rule_name -> score
