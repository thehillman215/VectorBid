"""
FastAPI main application for VectorBid
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import routers
from app.api.routes import router as api_router
from app.routes.meta import router as meta_router
from app.routes.ops import router as ops_router
from app.routes.ui import router as ui_router

# Import Pydantic models
try:
    from app.models import (
        BidLayerArtifact,
        CandidateSchedule,
        HardConstraints,
        Layer,
        PreferenceSchema,
        SoftPrefs,
    )
except ImportError:
    # Fallback models if app.models not available
    from typing import Any, Literal

    from pydantic import BaseModel

    class HardConstraints(BaseModel):
        no_weekends: bool = False
        no_redeyes: bool = False
        domestic_only: bool = False
        max_duty_days: int | None = None

    class SoftPrefs(BaseModel):
        weekend_weight: float = 0.5
        credit_weight: float = 0.5
        trip_weight: float = 0.5

    class PreferenceSchema(BaseModel):
        pilot_id: str
        airline: Literal["UAL"] = "UAL"
        base: str = "SFO"
        seat: Literal["FO", "CA"] = "FO"
        equip: list[str] = ["B737"]
        hard_constraints: HardConstraints = HardConstraints()
        soft_prefs: SoftPrefs = SoftPrefs()
        preferences_text: str | None = None
        persona: str | None = None

    class CandidateSchedule(BaseModel):
        candidate_id: str
        score: float
        hard_ok: bool
        soft_breakdown: dict[str, float]
        pairings: list[str]
        rationale: list[str] = []

    class Filter(BaseModel):
        type: str
        op: str
        values: list[Any]

    class Layer(BaseModel):
        n: int
        filters: list[Filter]
        prefer: Literal["YES", "NO"]

    # Additional helper model for UI
    class LayerDisplay(BaseModel):
        layer_number: int
        description: str
        pbs_commands: list[str]
        probability: float
        expected_outcome: str

    class BidLayerArtifact(BaseModel):
        airline: Literal["UAL"] = "UAL"
        format: Literal["PBS2"] = "PBS2"
        month: str
        layers: list[Layer]
        lint: dict[str, list[str]]
        export_hash: str


app = FastAPI(
    title="VectorBid API",
    description="AI-powered pilot schedule bidding assistant",
    version="1.0.0",
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

# Mount routers
app.include_router(api_router, tags=["API"])
app.include_router(meta_router, tags=["Meta"])
app.include_router(ops_router, tags=["Ops"])
app.include_router(ui_router, tags=["UI"])

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
        "weights": {"weekend_priority": 0.9, "trip_length": 0.8, "time_of_day": 0.7},
    },
    "money_maker": {
        "name": "Money Maker",
        "description": "Maximize earnings and credit",
        "icon": "fas fa-dollar-sign",
        "preferences": "I want long trips with maximum credit hours. International flying preferred.",
        "weights": {"credit_hours": 0.9, "international": 0.8, "trip_length": 0.7},
    },
    "commuter_friendly": {
        "name": "Commuter Friendly",
        "description": "Optimize for easy commuting",
        "icon": "fas fa-plane-departure",
        "preferences": "Late starts and early finishes for commuting. Trips starting after 10am.",
        "weights": {"departure_time": 0.9, "arrival_time": 0.8, "layover_length": 0.6},
    },
}


@app.get("/api/personas")
async def get_personas():
    """Get available pilot personas"""
    return {"personas": MOCK_PERSONAS}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VectorBid FastAPI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
