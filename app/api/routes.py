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
from app.explain.legal import explain as explain_legal
from app.security.api_key import require_api_key
from app.services.optimizer import retune_candidates, select_topk
from app.strategy.engine import propose_strategy
from app.audit import log_event
from app.db import Audit, Export, SessionLocal

router = APIRouter()


RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULES = load_rule_pack(RULE_PACK_PATH)
CANDIDATE_STORE: dict[str, CandidateSchedule] = {}


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
    report = validate_feasibility(bundle, _RULES)
    for cand in topk:
        cand.rationale.extend(explain_legal(cand, report))
    return {"candidates": [c.model_dump() for c in topk]}


@router.get("/candidates/{candidate_id}", tags=["Candidates"])
def get_candidate(candidate_id: str) -> dict[str, Any]:
    cand = CANDIDATE_STORE.get(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="candidate not found")
    return {"candidate": cand.model_dump()}


@router.post("/optimize/retune", tags=["Optimize"])
def retune(payload: dict[str, Any]) -> dict[str, Any]:
    _candidate_id = payload.get("candidate_id")  # for API symmetry; unused
    candidates = [CandidateSchedule(**c) for c in payload.get("candidates", [])]
    weight_deltas = payload.get("weight_deltas", {})
    adjusted = retune_candidates(candidates, weight_deltas)
    return {"candidates": [c.model_dump() for c in adjusted]}


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
def export(payload: dict[str, Any]) -> str:
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

        # Add signature if key is configured
        signature = None
        key = os.environ.get("EXPORT_SIGNING_KEY")
        if key:
            data = out_path.read_bytes()
            signature = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
            (out_path.with_suffix(out_path.suffix + ".sig")).write_text(
                signature, encoding="utf-8"
            )

        # Audit the export
        ctx_id = payload.get("ctx_id")
        with SessionLocal() as db:
            db.add(Export(ctx_id=ctx_id, path=str(out_path)))
            db.commit()

        log_event(ctx_id or "", "export", {"path": str(out_path)})

        # Return response with optional signature
        response = {"export_path": str(out_path)}
        if signature:
            response["signature"] = signature
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/audit/{ctx_id}", tags=["Audit"])
def get_audit(ctx_id: str) -> dict[str, Any]:
    """Return audit trail for a given context."""
    with SessionLocal() as db:
        rows = (
            db.query(Audit)
            .filter(Audit.ctx_id == ctx_id)
            .order_by(Audit.timestamp.asc())
            .all()
        )
        events = [
            {
                "stage": r.stage,
                "timestamp": r.timestamp.isoformat(),
                "payload": r.payload,
            }
            for r in rows
        ]
    return {"events": events}
