from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class HardConstraints(BaseModel):
    days_off: List[str] = Field(default_factory=list)
    no_red_eyes: bool = False
    max_duty_hours_per_day: Optional[int] = None
    legalities: List[str] = ["FAR117"]

class SoftPrefs(BaseModel):
    pairing_length: Dict[str, Any] | None = None
    layovers: Dict[str, Any] | None = None
    report_time: Dict[str, Any] | None = None
    release_time: Dict[str, Any] | None = None
    credit: Dict[str, Any] | None = None
    weekend_priority: Dict[str, Any] | None = None
    position_swap: Dict[str, Any] | None = None
    commutable: Dict[str, Any] | None = None

class PreferenceSchema(BaseModel):
    pilot_id: str
    airline: Literal["UAL"]
    base: str
    seat: Literal["FO", "CA"]
    equip: List[str]
    hard_constraints: HardConstraints = HardConstraints()
    soft_prefs: SoftPrefs = SoftPrefs()
    weights_version: str = "2025-08-16"
    confidence: Optional[float] = None
    source: Dict[str, Any] = {}

class ContextSnapshot(BaseModel):
    ctx_id: str
    pilot_id: str
    airline: str
    base: str
    seat: str
    equip: List[str]
    seniority_percentile: float
    commuting_profile: Dict[str, Any] = {}
    default_weights: Dict[str, float] = {}

class FeatureBundle(BaseModel):
    context: ContextSnapshot
    preference_schema: PreferenceSchema
    analytics_features: Dict[str, Any]
    compliance_flags: Dict[str, Any]
    pairing_features: Dict[str, Any]

class CandidateSchedule(BaseModel):
    candidate_id: str
    score: float
    hard_ok: bool
    soft_breakdown: Dict[str, float]
    pairings: List[str]
    rationale: List[str] = []

class StrategyDirectives(BaseModel):
    weight_deltas: Dict[str, float] = {}
    focus_hints: Dict[str, List[str]] = {}
    layer_templates: List[Dict[str, Any]] = []
    rationale: List[str] = []

class Filter(BaseModel):
    type: str
    op: str
    values: List[Any]

class Layer(BaseModel):
    n: int
    filters: List[Filter]
    prefer: Literal["YES","NO"]

class BidLayerArtifact(BaseModel):
    airline: Literal["UAL"]
    format: Literal["PBS2"]
    month: str
    layers: List[Layer]
    lint: Dict[str, List[str]]
    export_hash: str
