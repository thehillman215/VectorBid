from typing import List, Optional, Union

from pydantic import BaseModel, Field


class FAR117(BaseModel):
    """FAR117 regulatory parameters."""

    min_rest_hours: int = 10
    hard: List["HardRule"] = Field(default_factory=list)
    soft: List["SoftRule"] = Field(default_factory=list)


class UnionRules(BaseModel):
    """Union contract parameters."""

    max_duty_hours_per_day: Optional[int] = None
    no_red_eyes: bool = False
    hard: List["HardRule"] = Field(default_factory=list)
    soft: List["SoftRule"] = Field(default_factory=list)


class HardRule(BaseModel):
    """Schema for a hard rule entry."""

    id: str
    desc: Optional[str] = None
    when: Optional[str] = None
    check: Optional[str] = None


class SoftRule(BaseModel):
    """Schema for a soft rule entry."""

    id: str
    weight: Optional[Union[float, str]] = None
    score: Optional[str] = None
    desc: Optional[str] = None


class RulePack(BaseModel):
    """Top-level rule pack schema."""

    version: str
    airline: str
    far117: FAR117 = Field(default_factory=FAR117)
    union: UnionRules = Field(default_factory=UnionRules)
    hard: List["HardRule"] = Field(default_factory=list)
    soft: List["SoftRule"] = Field(default_factory=list)
