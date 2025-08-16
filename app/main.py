from __future__ import annotations
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import json
from typing import Dict
from app.models import (
    PreferenceSchema, ContextSnapshot, FeatureBundle,
    CandidateSchedule, StrategyDirectives, BidLayerArtifact
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
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/schemas", tags=["Meta"])
def get_all_schemas() -> Dict[str, Dict]:
    return {cls.__name__: cls.model_json_schema() for cls in MODELS}

from app.api import router as api_router
app.include_router(api_router)
