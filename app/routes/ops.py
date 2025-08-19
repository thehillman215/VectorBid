import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.generate.layers import candidates_to_layers
from app.generate.lint import lint_layers
from app.models import CandidateSchedule, FeatureBundle, StrategyDirectives
from app.security.auth import require_auth
from app.services.optimizer import select_topk
from app.strategy.engine import propose_strategy

router = APIRouter()


@router.get("/health")
def root_health() -> dict[str, str]:
    """Simple health check used by tests."""
    return {"status": "ok"}


@router.get("/ping")
def ping() -> dict[str, str]:
    """Simple ping endpoint for CI smoke tests"""
    return {"ping": "pong"}


@router.post("/optimize")
def optimize(payload: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper for the optimization endpoint."""
    bundle = FeatureBundle(**payload["feature_bundle"])
    k = int(payload.get("K", 50))
    topk = select_topk(bundle, k)
    return {"candidates": [c.model_dump() for c in topk]}


@router.post("/generate_layers")
def generate_layers(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    topk = [CandidateSchedule(**c) for c in payload["candidates"]]
    artifact = candidates_to_layers(topk, bundle)
    return {"artifact": artifact.model_dump()}


@router.post("/strategy")
def strategy(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    topk = [CandidateSchedule(**c) for c in payload["candidates"]]
    directives: StrategyDirectives = propose_strategy(bundle, topk)
    return {"directives": directives.model_dump()}


@router.post("/lint")
def lint(payload: dict[str, Any]) -> dict[str, Any]:
    return lint_layers(payload["artifact"])


@router.post("/export", dependencies=[Depends(require_auth)])
def export(payload: dict[str, Any]) -> dict[str, str]:
    try:
        art = payload.get("artifact", {})
        export_hash = art.get("export_hash") or "no-hash"

        export_dir = Path(os.environ.get("EXPORT_DIR", Path.cwd() / "exports"))
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{export_hash}.pbs2.json"

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(art, f, indent=2, ensure_ascii=False)

        return {"export_path": str(out_path)}
    except Exception as e:  # pragma: no cover - unexpected file errors
        raise HTTPException(status_code=400, detail=str(e)) from e
