from datetime import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class HardConstraints(BaseModel):
    days_off: list[str] = Field(default_factory=list)
    no_red_eyes: bool = False
    max_duty_hours_per_day: Optional[int] = None
    legalities: list[str] = ["FAR117"]


class SoftPrefs(BaseModel):
    pairing_length: Optional[dict[str, Any]] = None
    layovers: Optional[dict[str, Any]] = None
    report_time: Optional[dict[str, Any]] = None
    release_time: Optional[dict[str, Any]] = None
    credit: Optional[dict[str, Any]] = None
    weekend_priority: Optional[dict[str, Any]] = None
    position_swap: Optional[dict[str, Any]] = None
    commutable: Optional[dict[str, Any]] = None


class PreferenceSchema(BaseModel):
    pilot_id: str
    airline: Literal["UAL"]
    base: str
    seat: Literal["FO", "CA"]
    equip: list[str]
    hard_constraints: HardConstraints = HardConstraints()
    soft_prefs: SoftPrefs = SoftPrefs()
    weights_version: str = "2025-08-16"
    confidence: Optional[float] = None
    source: dict[str, Any] = {}


class ContextSnapshot(BaseModel):
    ctx_id: str
    pilot_id: str
    airline: str
    month: str  # Added for rule pack integration
    base: str
    seat: str
    equip: list[str]
    seniority_percentile: float
    commuting_profile: dict[str, Any] = {}
    default_weights: dict[str, float] = {}


class FeatureBundle(BaseModel):
    context: ContextSnapshot
    preference_schema: PreferenceSchema
    analytics_features: dict[str, Any]
    compliance_flags: dict[str, Any]
    pairing_features: dict[str, Any]


class CandidateRationale(BaseModel):
    hard_hits: list[str] = Field(default_factory=list)
    hard_misses: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CandidateSchedule(BaseModel):
    candidate_id: str
    score: float
    hard_ok: bool
    soft_breakdown: dict[str, float]
    pairings: list[str]
    rationale: CandidateRationale = CandidateRationale()


class StrategyDirectives(BaseModel):
    weight_deltas: dict[str, float] = {}
    focus_hints: dict[str, list[str]] = {}
    layer_templates: list[dict[str, Any]] = []
    rationale: list[str] = []


class Filter(BaseModel):
    type: str
    op: str
    values: list[Any]


class Layer(BaseModel):
    n: int
    filters: list[Filter]
    prefer: Literal["YES", "NO"]


class BidLayerArtifact(BaseModel):
    airline: Literal["UAL"]
    format: Literal["PBS2"]
    month: str
    layers: list[Layer]
    lint: dict[str, list[Union[str, dict[str, str]]]]
    export_hash: str


# New models for ingestion API
class IngestionRequest(BaseModel):
    airline: str
    month: str
    base: str
    fleet: str
    seat: str
    pilot_id: str


class IngestionResponse(BaseModel):
    success: bool
    summary: dict[str, Any]
    message: Optional[str] = None
    error: Optional[str] = None


class BidPackage(BaseModel):
    id: Optional[str] = None
    pilot_id: str
    airline: str
    month: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    hash: Optional[str] = None


class FAQItem(BaseModel):
    """FAQ entry served by `/faq`"""

    id: str
    question: str
    answer: str
    rationale: Optional[str] = None
