# app/api/routes.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.generate.layers import candidates_to_layers
from app.generate.lint import lint_layers
from app.models import (
    BidLayerArtifact,
    CandidateSchedule,
    ContextSnapshot,
    FeatureBundle,
    PreferenceSchema,
    StrategyDirectives,
)
from app.rules.engine import load_rule_pack, validate_feasibility
from app.security.api_key import require_api_key
from app.services.optimizer import select_topk
from app.strategy.engine import propose_strategy

router = APIRouter()


RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULES = load_rule_pack(RULE_PACK_PATH)


@router.post("/validate", tags=["Validate"])
def validate(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Body:
      {
        "preference_schema": {...},
        "context": {...},
        "pairings": {"pairings":[...] }
      }
    Returns: {"violations":[...], "feasible_pairings":[...]}
    """
    try:
        bundle = FeatureBundle(
            context=ContextSnapshot(**payload["context"]),
            preference_schema=PreferenceSchema(**payload["preference_schema"]),
            analytics_features={},
            compliance_flags={},
            pairing_features=payload["pairings"],
        )
        force = payload.get("force_reload", False)
        global _RULES
        if force:
            _RULES = load_rule_pack(RULE_PACK_PATH, force_reload=True)
        return validate_feasibility(bundle, _RULES)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/optimize", tags=["Optimize"])
def optimize(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    K = int(payload.get("K", 50))
    topk = select_topk(bundle, K)
    return {"candidates": [c.model_dump() for c in topk]}


@router.post("/strategy", tags=["Strategy"])
def strategy(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Body:
      {"feature_bundle": {...}, "candidates": [...]}
    Returns:
      {"directives": StrategyDirectives}
    """
    try:
        bundle = FeatureBundle(**payload["feature_bundle"])
        topk = [CandidateSchedule(**c) for c in payload["candidates"]]
        directives: StrategyDirectives = propose_strategy(bundle, topk)
        return {"directives": directives.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/generate_layers", tags=["Generate"])
def generate_layers(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Body:
      {"feature_bundle": {...}, "candidates": [...]}
    Returns:
      {"artifact": BidLayerArtifact}
    """
    try:
        bundle = FeatureBundle(**payload["feature_bundle"])
        topk = [CandidateSchedule(**c) for c in payload["candidates"]]
        artifact: BidLayerArtifact = candidates_to_layers(topk, bundle)
        return {"artifact": artifact.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/lint", tags=["Generate"])
def lint(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Body: {"artifact": {...}}
    Returns: {"errors": [...], "warnings": [...]}
    """
    try:
        return lint_layers(payload["artifact"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/export", tags=["Export"], dependencies=[Depends(require_api_key)])
def export(payload: dict[str, Any]) -> dict[str, str]:
    """
    Protected when VECTORBID_API_KEY is set.
    Accepts: {"artifact": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports) and returns a filesystem path.
    """
    try:
        art = payload.get("artifact", {})
        export_hash = art.get("export_hash") or "no-hash"

        export_dir = Path(os.environ.get("EXPORT_DIR", Path.cwd() / "exports"))
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{export_hash}.pbs2.json"

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(art, f, indent=2, ensure_ascii=False)

        return {"export_path": str(out_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
