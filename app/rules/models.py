from __future__ import annotations

from pydantic import BaseModel, Field


class FAR117(BaseModel):
    """FAR117 regulatory parameters."""

    min_rest_hours: int = 10


class UnionRules(BaseModel):
    """Union contract parameters."""

    max_duty_hours_per_day: int | None = None
    no_red_eyes: bool = False


class HardRule(BaseModel):
    """Schema for a hard rule entry."""

    id: str
    desc: str | None = None
    when: str | None = None
    check: str | None = None


class SoftRule(BaseModel):
    """Schema for a soft rule entry."""

    id: str
    weight: float | str | None = None
    score: str | None = None
    desc: str | None = None


class RulePack(BaseModel):
    """Top-level rule pack schema."""

    version: str
    airline: str
    far117: FAR117 = Field(default_factory=FAR117)
    union: UnionRules = Field(default_factory=UnionRules)
    hard: list[HardRule] = Field(default_factory=list)
    soft: list[SoftRule] = Field(default_factory=list)
