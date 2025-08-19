import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.compat.validate_router import router as compat_validate_router
from app.logging_utils import install_pii_filter
from app.middleware import RequestIDMiddleware
from app.models import (
    BidLayerArtifact,
    CandidateSchedule,
    ContextSnapshot,
    FeatureBundle,
    PreferenceSchema,
    StrategyDirectives,
)
from app.routes.faq import router as faq_router
from app.routes.meta import router as meta_router
from app.routes.ops import router as ops_router
from app.routes.ui import router as ui_router

MODELS = [
    PreferenceSchema,
    ContextSnapshot,
    FeatureBundle,
    CandidateSchedule,
    StrategyDirectives,
    BidLayerArtifact,
]

install_pii_filter()


def _export_model_schemas() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    schema_dir = root_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for cls in MODELS:
        (schema_dir / f"{cls.__name__}.json").write_text(
            json.dumps(cls.model_json_schema(), indent=2)
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    # on startup
    _export_model_schemas()
    yield
    # on shutdown (noop)


app = FastAPI(
    title="VectorBid API",
    description="AI-powered pilot schedule bidding assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount routers
app.include_router(api_router, tags=["API"])
app.include_router(meta_router, tags=["Meta"])
app.include_router(ops_router, tags=["Ops"])
app.include_router(ui_router, tags=["UI"])
app.include_router(faq_router, tags=["FAQ"])

# Legacy compatibility
app.include_router(compat_validate_router)


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
        "preferences": (
            "I want weekends off and no early departures. "
            "Prefer short trips of 1-3 days."
        ),
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


@app.get("/schemas", tags=["Meta"])
def get_all_schemas() -> dict[str, dict]:
    return {cls.__name__: cls.model_json_schema() for cls in MODELS}
