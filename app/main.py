from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.models import (
    BidLayerArtifact,
    CandidateSchedule,
    ContextSnapshot,
    FeatureBundle,
    PreferenceSchema,
    StrategyDirectives,
)

MODELS = [
    PreferenceSchema, ContextSnapshot, FeatureBundle,
    CandidateSchedule, StrategyDirectives, BidLayerArtifact
]

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

app = FastAPI(title="VectorBid (v0.3 scaffold)", lifespan=lifespan)

@app.get("/health", tags=["Meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/schemas", tags=["Meta"])
def get_all_schemas() -> dict[str, dict]:
    return {cls.__name__: cls.model_json_schema() for cls in MODELS}

from app.api import router as api_router

app.include_router(api_router)

# UI Routes Integration
try:
    from app.routes.ui import router as ui_router
    app.include_router(ui_router, prefix="", tags=["UI"])
    print("✅ UI routes registered")
except ImportError as e:
    print(f"⚠️  UI routes not available: {e}")

# Static files
try:
    from fastapi.staticfiles import StaticFiles
    import os
    if os.path.exists("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
        print("✅ Static files mounted")
except Exception as e:
    print(f"⚠️  Static files not mounted: {e}")
