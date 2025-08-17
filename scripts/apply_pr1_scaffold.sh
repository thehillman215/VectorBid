set -euo pipefail

mkdir -p app/{context,orchestrator,ingestion,fusion,rules,optimize,strategy,analytics,generate} schemas tests

# app/__init__.py
cat > app/__init__.py <<'PY'
"""VectorBid FastAPI app package (v0.3 scaffold)."""
PY

# app/models.py
cat > app/models.py <<'PY'
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
PY

# app/main.py
cat > app/main.py <<'PY'
from __future__ import annotations
from fastapi import FastAPI
from pathlib import Path
import json
from typing import Dict
from app.models import (
    PreferenceSchema, ContextSnapshot, FeatureBundle,
    CandidateSchedule, StrategyDirectives, BidLayerArtifact
)

app = FastAPI(title="VectorBid (v0.3 scaffold)")

MODELS = [
    PreferenceSchema, ContextSnapshot, FeatureBundle,
    CandidateSchedule, StrategyDirectives, BidLayerArtifact
]

@app.on_event("startup")
def export_model_schemas() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    schema_dir = root_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for cls in MODELS:
        (schema_dir / f"{cls.__name__}.json").write_text(
            json.dumps(cls.model_json_schema(), indent=2)
        )

@app.get("/health", tags=["Meta"])
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/schemas", tags=["Meta"])
def get_all_schemas() -> Dict[str, Dict]:
    return {cls.__name__: cls.model_json_schema() for cls in MODELS}
PY

# stubs (raise NotImplementedError) for PR2 targets
cat > app/context/__init__.py <<'PY'
from .enrich import build_context_snapshot  # noqa: F401
PY
cat > app/context/enrich.py <<'PY'
from app.models import ContextSnapshot
def build_context_snapshot(pilot_id: str) -> ContextSnapshot:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/orchestrator/__init__.py <<'PY'
from .run import compile_inputs  # noqa: F401
PY
cat > app/orchestrator/run.py <<'PY'
from typing import Dict, Any
from app.models import ContextSnapshot
import asyncio
async def compile_inputs(ctx: ContextSnapshot, text: str, sliders: Dict[str, Any]):
    # Will run NLP, precheck, analytics via asyncio.gather in PR2
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/ingestion/__init__.py <<'PY'
from .packet import parse_bid_packet  # noqa: F401
PY
cat > app/ingestion/packet.py <<'PY'
from typing import Dict
def parse_bid_packet(upload_path: str) -> Dict:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/fusion/__init__.py <<'PY'
from .fusion import fuse  # noqa: F401
PY
cat > app/fusion/fusion.py <<'PY'
from typing import Dict, Any
from app.models import ContextSnapshot, PreferenceSchema, FeatureBundle
def fuse(ctx: ContextSnapshot, pref: PreferenceSchema, precheck: Dict[str, Any], analytics: Dict[str, Any], pairings: Dict[str, Any]) -> FeatureBundle:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/rules/__init__.py <<'PY'
from .engine import load_rule_pack, validate_feasibility  # noqa: F401
PY
cat > app/rules/engine.py <<'PY'
from typing import Any, Dict, List, Tuple
from app.models import FeatureBundle
def load_rule_pack(path: str) -> Any:
    raise NotImplementedError("Implemented in PR2")
def validate_feasibility(bundle: FeatureBundle, rules: Any) -> Dict[str, Any]:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/strategy/__init__.py <<'PY'
from .engine import propose_strategy  # noqa: F401
PY
cat > app/strategy/engine.py <<'PY'
from typing import List
from app.models import FeatureBundle, CandidateSchedule, StrategyDirectives
def propose_strategy(bundle: FeatureBundle, topk: List[CandidateSchedule]) -> StrategyDirectives:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/analytics/__init__.py <<'PY'
from .probability import estimate_success_prob  # noqa: F401
PY
cat > app/analytics/probability.py <<'PY'
from typing import Dict, Any, List
from app.models import ContextSnapshot
def estimate_success_prob(filters: List[Dict[str, Any]], ctx: ContextSnapshot, analytics: Dict[str, Any]) -> float:
    raise NotImplementedError("Implemented in PR2")
PY

cat > app/generate/__init__.py <<'PY'
from .layers import candidates_to_layers  # noqa: F401
from .lint import lint_layers  # noqa: F401
PY
cat > app/generate/layers.py <<'PY'
from typing import List
from app.models import CandidateSchedule, BidLayerArtifact, FeatureBundle
def candidates_to_layers(topk: List[CandidateSchedule], bundle: FeatureBundle) -> BidLayerArtifact:
    raise NotImplementedError("Implemented in PR2")
PY
cat > app/generate/lint.py <<'PY'
from typing import Dict
from app.models import BidLayerArtifact
def lint_layers(artifact: BidLayerArtifact) -> Dict:
    raise NotImplementedError("Implemented in PR2")
PY

# tests/tests_meta.py
cat > tests/tests_meta.py <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_schemas_present():
    r = client.get("/schemas")
    assert r.status_code == 200
    data = r.json()
    # Must include the key models
    for name in [
        "PreferenceSchema",
        "ContextSnapshot",
        "FeatureBundle",
        "CandidateSchedule",
        "StrategyDirectives",
        "BidLayerArtifact",
    ]:
        assert name in data
        assert isinstance(data[name], dict)
PY

# placeholder so the dir is tracked
echo ' ' > schemas/.gitkeep
