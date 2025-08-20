import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    export as api_export,
    generate_layers as api_generate_layers,
    lint as api_lint,
    optimize as api_optimize,
    router as api_router,
    strategy as api_strategy,
)
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
from app.routes.ingestion import router as ingestion_router
from app.routes.marketing import router as marketing_router
from app.routes.products import router as products_router
from app.routes.solutions import router as solutions_router
from app.routes.meta import router as meta_router
from app.routes.ops import router as ops_router
from app.routes.rule_packs import router as rule_packs_router
from app.routes.ui import router as ui_router
from app.security.api_key import require_api_key

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
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(ingestion_router, tags=["Ingestion"])
app.include_router(meta_router, tags=["Meta"])
app.include_router(ops_router, tags=["Ops"])
app.include_router(rule_packs_router, tags=["Rule Packs"])
app.include_router(ui_router, tags=["UI"])
app.include_router(faq_router, tags=["FAQ"])
app.include_router(marketing_router, tags=["Marketing"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(solutions_router, prefix="/solutions", tags=["Solutions"])

# Legacy compatibility
app.include_router(compat_validate_router)
app.add_api_route("/optimize", api_optimize, methods=["POST"], tags=["compat"])
app.add_api_route("/strategy", api_strategy, methods=["POST"], tags=["compat"])
app.add_api_route("/generate_layers", api_generate_layers, methods=["POST"], tags=["compat"])
app.add_api_route("/lint", api_lint, methods=["POST"], tags=["compat"])
app.add_api_route(
    "/export",
    api_export,
    methods=["POST"],
    tags=["compat"],
    dependencies=[Depends(require_api_key)],
)


# Root route now handled by marketing router
# Professional landing page served by /app/routes/marketing.py

# A/B testing route for landing page v2
@app.get("/landing/v2")
async def serve_landing_v2():
    """Alternative landing page for A/B testing"""
    landing_path = Path(__file__).parent / "static" / "pages" / "landing" / "v2.html"
    if landing_path.exists():
        return FileResponse(landing_path)
    return {"message": "Landing page v2 not found"}


# Mock data for development
MOCK_PERSONAS = {
    "family_first": {
        "name": "Family First",
        "description": "Maximize time at home with family",
        "icon": "fas fa-home",
        "preferences": (
            "I want weekends off and no early departures. Prefer short trips of 1-3 days."
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
