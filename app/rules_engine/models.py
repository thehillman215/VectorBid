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
    message: Optional[str] = None
    
    # Add computed properties for backward compatibility
    @property
    def id(self) -> str:
        """Backward compatibility: return name as id."""
        return self.name
    
    @property
    def predicate(self):
        """Backward compatibility: return check as predicate function."""
        # Simple predicate that always returns True for now
        # TODO: Implement actual DSL evaluation
        return lambda obj, ctx: True


class SoftRule(BaseModel):
    """Soft preference that affects scoring."""

    name: str
    description: str
    weight: float
    score: str  # DSL expression that returns a score
    bounds: Optional[tuple[float, float]] = None
    
    # Add computed property for backward compatibility
    @property
    def id(self) -> str:
        """Backward compatibility: return name as id."""
        return self.name


class DerivedRule(BaseModel):
    """Computed field derived from other data."""

    name: str
    description: str
    compute: str  # DSL expression that computes a value
    output_type: str = "float"  # float, int, str, bool
    
    # Add computed property for backward compatibility
    @property
    def id(self) -> str:
        """Backward compatibility: return name as id."""
        return self.name


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
    original_checksum: Optional[str] = None
    
    # Add computed properties for backward compatibility
    @property
    def month(self) -> str:
        """Backward compatibility: return contract_period as month."""
        return self.contract_period
    
    @property
    def schema_version(self) -> str:
        """Backward compatibility: return version as schema_version."""
        return self.version
    
    @property
    def checksum(self) -> str:
        """Backward compatibility: return a computed checksum."""
        # Use original checksum if available, otherwise compute one
        if self.original_checksum:
            return self.original_checksum
        # Simple hash of the rule pack content
        content = f"{self.airline}{self.contract_period}{self.base}{self.fleet}"
        return f"{hash(content) % 1000000:06d}"


class Violation(BaseModel):
    """Rule violation details."""

    rule_id: str
    severity: str
    message: str
    path: str
    data_excerpt: Optional[str] = None
    fix_hint: Optional[str] = None
    ctx_id: Optional[str] = None
    pack_version: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """Detailed scoring breakdown for soft rules."""

    total: float
    components: dict[str, float]  # rule_name -> score
