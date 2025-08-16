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


# Import and include UI routes
from app.routes.ui import router as ui_router
app.include_router(ui_router, prefix="", tags=["UI"])
print("✅ UI routes registered at /")

# UI Routes (opt-in only)
import os as _os
if _os.getenv("ENABLE_UI") == "1":
    try:
        from app.routes.ui import router as ui_router  # heavy: uses Form()
        app.include_router(ui_router)
        print("✅ UI routes added")
    except Exception as e:
        print(f"⚠️ UI disabled: {e}")
