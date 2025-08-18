"""
FastAPI main application for VectorBid
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Import Pydantic models
try:
    from app.models import (
        PreferenceSchema, 
        CandidateSchedule, 
        BidLayerArtifact,
        HardConstraints,
        SoftPrefs,
        Layer
    )
except ImportError:
    # Fallback models if app.models not available
    from pydantic import BaseModel
    from typing import List, Dict, Any, Literal, Optional
    
    class HardConstraints(BaseModel):
        no_weekends: bool = False
        no_redeyes: bool = False
        domestic_only: bool = False
        max_duty_days: Optional[int] = None
    
    class SoftPrefs(BaseModel):
        weekend_weight: float = 0.5
        credit_weight: float = 0.5
        trip_weight: float = 0.5
    
    class PreferenceSchema(BaseModel):
        pilot_id: str
        airline: Literal["UAL"] = "UAL"
        base: str = "SFO"
        seat: Literal["FO", "CA"] = "FO"
        equip: List[str] = ["B737"]
        hard_constraints: HardConstraints = HardConstraints()
        soft_prefs: SoftPrefs = SoftPrefs()
        preferences_text: Optional[str] = None
        persona: Optional[str] = None
    
    class CandidateSchedule(BaseModel):
        candidate_id: str
        score: float
        hard_ok: bool
        soft_breakdown: Dict[str, float]
        pairings: List[str]
        rationale: List[str] = []
    
    class Filter(BaseModel):
        type: str
        op: str
        values: List[Any]
    
    class Layer(BaseModel):
        n: int
        filters: List[Filter]
        prefer: Literal["YES", "NO"]
        
    # Additional helper model for UI
    class LayerDisplay(BaseModel):
        layer_number: int
        description: str
        pbs_commands: List[str]
        probability: float
        expected_outcome: str
    
    class BidLayerArtifact(BaseModel):
        airline: Literal["UAL"] = "UAL"
        format: Literal["PBS2"] = "PBS2"
        month: str
        layers: List[Layer]
        lint: Dict[str, List[str]]
        export_hash: str

app = FastAPI(
    title="VectorBid API",
    description="AI-powered pilot schedule bidding assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve the SPA
@app.get("/")
async def serve_spa():
    """Serve the single page application"""
    spa_path = Path(__file__).parent / "static" / "index.html"
    if spa_path.exists():
        return FileResponse(spa_path)
    return {"message": "SPA not found - please build frontend"}

# Mock data for development
MOCK_PERSONAS = {
    "family_first": {
        "name": "Family First",
        "description": "Maximize time at home with family",
        "icon": "fas fa-home",
        "preferences": "I want weekends off and no early departures. Prefer short trips of 1-3 days.",
        "weights": {"weekend_priority": 0.9, "trip_length": 0.8, "time_of_day": 0.7}
    },
    "money_maker": {
        "name": "Money Maker", 
        "description": "Maximize earnings and credit",
        "icon": "fas fa-dollar-sign",
        "preferences": "I want long trips with maximum credit hours. International flying preferred.",
        "weights": {"credit_hours": 0.9, "international": 0.8, "trip_length": 0.7}
    },
    "commuter_friendly": {
        "name": "Commuter Friendly",
        "description": "Optimize for easy commuting",
        "icon": "fas fa-plane-departure", 
        "preferences": "Late starts and early finishes for commuting. Trips starting after 10am.",
        "weights": {"departure_time": 0.9, "arrival_time": 0.8, "layover_length": 0.6}
    }
}

@app.get("/api/personas")
async def get_personas():
    """Get available pilot personas"""
    return {"personas": MOCK_PERSONAS}

@app.post("/api/parse_preferences")
async def parse_preferences(data: Dict[str, Any]):
    """Parse free-text preferences into structured format"""
    preferences_text = data.get("preferences", "")
    persona = data.get("persona")
    
    # Mock parsing logic - in real implementation would use LLM
    parsed = {
        "hard_constraints": {
            "no_weekends": "weekend" in preferences_text.lower(),
            "no_redeyes": "red-eye" in preferences_text.lower() or "redeye" in preferences_text.lower(),
            "max_days": 4 if "short trip" in preferences_text.lower() else 6
        },
        "soft_preferences": {
            "morning_departures": 0.8 if "morning" in preferences_text.lower() else 0.3,
            "domestic_preferred": 0.7 if "domestic" in preferences_text.lower() else 0.4,
            "weekend_priority": 0.9 if "weekend" in preferences_text.lower() else 0.2
        },
        "confidence": 0.85,
        "parsed_items": [
            {"text": "Weekends off", "confidence": 0.9, "category": "hard_constraint"},
            {"text": "Morning departures preferred", "confidence": 0.8, "category": "soft_preference"}
        ]
    }
    
    return {
        "original_text": preferences_text,
        "parsed_preferences": parsed,
        "persona_influence": persona,
        "suggestions": ["Consider specifying layover preferences", "Add aircraft type preferences"]
    }

@app.post("/api/validate_constraints") 
async def validate_constraints(preferences: PreferenceSchema):
    """Validate preference constraints"""
    violations = []
    warnings = []
    
    # Mock validation logic
    hard_constraints = preferences.hard_constraints
    soft_prefs = preferences.soft_prefs
    
    max_duty = getattr(hard_constraints, 'max_duty_days', None)
    if max_duty and max_duty > 6:
        violations.append("Maximum duty days cannot exceed 6")
    
    credit_weight = getattr(soft_prefs, 'credit_weight', 0.5)
    if credit_weight > 1.0:
        warnings.append("Credit weight is very high - may conflict with other preferences")
        
    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "score": 0.85
    }

@app.post("/api/optimize")
async def optimize_schedule(preferences: PreferenceSchema):
    """Optimize schedule based on preferences"""
    
    # Mock candidate schedules
    candidates = [
        CandidateSchedule(
            candidate_id="sched_001",
            score=0.92,
            hard_ok=True,
            soft_breakdown={
                "weekend_priority": 0.95,
                "credit_hours": 0.88,
                "trip_length": 0.90
            },
            pairings=["UAL101-SFO-LAX", "UAL205-LAX-DEN", "UAL330-DEN-SFO"],
            rationale=[
                "Optimizes weekend time off",
                "Meets credit hour targets",
                "Minimizes red-eye exposure"
            ]
        ),
        CandidateSchedule(
            candidate_id="sched_002", 
            score=0.87,
            hard_ok=True,
            soft_breakdown={
                "weekend_priority": 0.82,
                "credit_hours": 0.95,
                "trip_length": 0.85
            },
            pairings=["UAL150-SFO-ORD", "UAL275-ORD-IAH", "UAL180-IAH-SFO"],
            rationale=[
                "Maximizes credit hours",
                "Good trip variety",
                "Reasonable layover times"
            ]
        )
    ]
    
    return {
        "candidates": candidates,
        "optimization_time_ms": 1250,
        "total_evaluated": 450,
        "preferences_applied": preferences.dict()
    }

@app.post("/api/generate_layers")
async def generate_layers(preferences: PreferenceSchema):
    """Generate PBS-style bid layers"""
    
    # Mock bid layers - using proper schema
    schema_layers = [
        Layer(
            n=1,
            filters=[
                Filter(type="duty_period", op="not_overlaps", values=["SAT", "SUN"]),
                Filter(type="route_type", op="equals", values=["DOMESTIC"])
            ],
            prefer="YES"
        ),
        Layer(
            n=2,
            filters=[
                Filter(type="duty_period", op="not_overlaps", values=["SAT", "SUN"]),
                Filter(type="duty_days", op="lte", values=[4])
            ],
            prefer="YES"
        ),
        Layer(
            n=3,
            filters=[
                Filter(type="line_type", op="not_equals", values=["RESERVE"])
            ],
            prefer="YES"
        )
    ]
    
    # Display layers for UI
    display_layers = [
        LayerDisplay(
            layer_number=1,
            description="Perfect weekends + domestic",
            pbs_commands=[
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                "PREFER DOMESTIC TRIPS"
            ],
            probability=0.15,
            expected_outcome="Best case scenario"
        ),
        LayerDisplay(
            layer_number=2, 
            description="Weekends off, any routes",
            pbs_commands=[
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                "PREFER TRIPS WITH DUTY_DAYS <= 4"
            ],
            probability=0.35,
            expected_outcome="Good work-life balance"
        ),
        LayerDisplay(
            layer_number=3,
            description="Any line to avoid reserve",
            pbs_commands=[
                "PREFER ANY LINE OVER RESERVE"
            ],
            probability=0.95,
            expected_outcome="Guaranteed line"
        )
    ]
    
    artifact = BidLayerArtifact(
        airline="UAL",
        format="PBS2",
        month="2025-09",
        layers=schema_layers,
        lint={"errors": [], "warnings": ["Layer 1 probability very low"]},
        export_hash="abc123def456"
    )
    
    # Return both schema and display data for frontend
    return {
        "schema": artifact,
        "display": {
            "airline": "UAL",
            "format": "PBS2", 
            "month": "2025-09",
            "layers": display_layers,
            "lint": {"errors": [], "warnings": ["Layer 1 probability very low"]},
            "export_hash": "abc123def456"
        }
    }

@app.get("/api/exports/{export_id}")
async def get_export(export_id: str):
    """Get exported bid file"""
    return {
        "export_id": export_id,
        "format": "PBS2", 
        "created_at": datetime.now().isoformat(),
        "download_url": f"/api/downloads/{export_id}",
        "content": "# PBS Commands\\nAVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN\\n"
    }

@app.get("/api/explain/{candidate_id}")
async def explain_candidate(candidate_id: str):
    """Explain why a candidate was ranked as it was"""
    return {
        "candidate_id": candidate_id,
        "explanation": {
            "score_breakdown": {
                "base_score": 0.70,
                "weekend_bonus": 0.15,
                "credit_bonus": 0.05,
                "penalties": -0.02
            },
            "key_factors": [
                "Strong weekend protection",
                "Meets minimum credit requirements", 
                "One suboptimal layover"
            ],
            "comparison_rank": 1,
            "improvement_suggestions": [
                "Consider accepting some weekend flying for higher pay",
                "Look at international options for more credit"
            ]
        }
    }

@app.post("/api/lint")
async def lint_preferences(data: Dict[str, Any]):
    """Lint preference configuration for issues"""
    return {
        "errors": [],
        "warnings": [
            "High credit weight may conflict with weekend preference",
            "No aircraft type specified"
        ],
        "suggestions": [
            "Consider balancing credit vs. quality of life",
            "Add equipment preferences for better matching"
        ],
        "score": 0.82
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VectorBid FastAPI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)