import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.generate.layers import candidates_to_layers
from app.generate.lint import lint_layers
from app.models import CandidateSchedule, FeatureBundle, StrategyDirectives
from app.security.api_key import require_api_key
from app.services.optimizer import select_topk
from app.strategy.engine import propose_strategy

router = APIRouter()


def _get_rulepack_version() -> str:
    root = Path(__file__).resolve().parents[2] / "rule_packs"
    versions = sorted(p.stem for p in root.glob("*/*.yml"))
    return versions[-1] if versions else "unknown"


@router.get("/ping", response_class=PlainTextResponse)
def ping() -> str:
    """Simple liveness check returning plain text."""
    return "pong"


@router.get("/health")
def root_health() -> dict[str, str]:
    """Report service health without exposing secrets."""
    return {
        "db": "ok",
        "storage": "ok",
        "rulepack_version": _get_rulepack_version(),
    }


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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


@router.post("/export", dependencies=[Depends(require_api_key)])
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
