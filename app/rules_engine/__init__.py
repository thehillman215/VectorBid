"""
VectorBid Rules Engine

Deterministic rule validation and scoring for pilot bid preferences.
Compiles YAML rule packs into immutable Python objects for validation.
"""

from .compiler import compile_rule_pack
from .health import (
    dsl_health,
    pack_registry_health,
    pack_status,
    pack_validation_health,
)
from .models import DerivedRule, HardRule, RulePack, ScoreBreakdown, SoftRule, Violation
from .resolver import PackResolver
from .validator import RulePackValidator, score_schedule

__all__ = [
    "RulePack",
    "HardRule",
    "SoftRule",
    "DerivedRule",
    "Violation",
    "ScoreBreakdown",
    "compile_rule_pack",
    "RulePackValidator",
    "score_schedule",
    "PackResolver",
    "pack_status",
    "pack_registry_health",
    "pack_validation_health",
    "dsl_health",
]
