# app/api/routes.py
from __future__ import annotations

import hashlib
import hmac
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
    HardConstraints,
    PreferenceSchema,
    SoftPrefs,
    StrategyDirectives,
)
from app.rules.engine import load_rule_pack, validate_feasibility
from app.security.auth import require_auth
from app.services.optimizer import select_topk
from app.strategy.engine import propose_strategy

router = APIRouter(prefix="/api")


RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULES = load_rule_pack(RULE_PACK_PATH)


@router.post("/parse", tags=["Parse"])
def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Parse free-text preferences into structured format using NLP/LLM

    Body:
      {
        "preferences_text": "I want weekends off and no red-eyes",
        "persona": "family_first",
        "context": {...}
      }
    Returns: {"parsed_preferences": {...}, "confidence": 0.85}
    """
    try:
        preferences_text = payload.get("preferences_text", "")
        persona = payload.get("persona")

        # TODO: Implement actual NLP parsing logic
        # For now, return mock parsed data
        parsed = {
            "hard_constraints": {
                "no_weekends": "weekend" in preferences_text.lower(),
                "no_redeyes": "red-eye" in preferences_text.lower()
                or "redeye" in preferences_text.lower(),
                "max_duty_days": 4 if "short trip" in preferences_text.lower() else 6,
            },
            "soft_preferences": {
                "morning_departures": (
                    0.8 if "morning" in preferences_text.lower() else 0.3
                ),
                "domestic_preferred": (
                    0.7 if "domestic" in preferences_text.lower() else 0.4
                ),
                "weekend_priority": (
                    0.9 if "weekend" in preferences_text.lower() else 0.2
                ),
            },
            "confidence": 0.85,
            "parsed_items": [
                {
                    "text": "Weekends off",
                    "confidence": 0.9,
                    "category": "hard_constraint",
                },
                {
                    "text": "Morning departures preferred",
                    "confidence": 0.8,
                    "category": "soft_preference",
                },
            ],
        }

        return {
            "original_text": preferences_text,
            "parsed_preferences": parsed,
            "persona_influence": persona,
            "suggestions": [
                "Consider specifying layover preferences",
                "Add aircraft type preferences",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/parse_preview", tags=["Parse"])
def parse_preview(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a PreferenceSchema preview without persistence."""
    try:
        text = payload.get("text", "")
        persona = payload.get("persona")
        hard = HardConstraints(
            no_red_eyes="red-eye" in text.lower() or "redeye" in text.lower()
        )
        soft = SoftPrefs(
            weekend_priority={"weight": 0.9} if "weekend" in text.lower() else {}
        )
        schema = PreferenceSchema(
            pilot_id="preview",
            airline="UAL",
            base="SFO",
            seat="FO",
            equip=["73G"],
            hard_constraints=hard,
            soft_prefs=soft,
            source={"persona": persona, "preview": True},
        )
        return {"preference_schema": schema.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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


@router.post("/export", tags=["Export"], dependencies=[Depends(require_auth)])
def export(payload: dict[str, Any]) -> dict[str, str]:
    """Protected export endpoint.

    Accepts: {"artifact": {...}}
    Writes JSON to $EXPORT_DIR (or ./exports), signs it with HMAC SHA256,
    and returns the filesystem path and signature.
    """
    try:
        art = payload.get("artifact", {})
        export_hash = art.get("export_hash") or "no-hash"

        export_dir = Path(os.environ.get("EXPORT_DIR", Path.cwd() / "exports"))
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{export_hash}.pbs2.json"

        # Write artifact
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(art, f, indent=2, ensure_ascii=False)

        key = os.environ.get("EXPORT_SIGNING_KEY")
        if not key:
            raise HTTPException(status_code=500, detail="signing key not configured")
        data = out_path.read_bytes()
        signature = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
        (out_path.with_suffix(out_path.suffix + ".sig")).write_text(
            signature, encoding="utf-8"
        )

        return {"export_path": str(out_path), "signature": signature}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
