from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.models import (
    PreferenceSchema, ContextSnapshot, FeatureBundle,
    CandidateSchedule, StrategyDirectives, BidLayerArtifact
)
from app.context.enrich import build_context_snapshot
from app.orchestrator.run import compile_inputs
from app.fusion.fusion import fuse
from app.rules.engine import load_rule_pack, validate_feasibility
from app.optimize.optimizer import rank_candidates
from app.strategy.engine import propose_strategy
from app.analytics.probability import estimate_success_prob
from app.generate.layers import candidates_to_layers
from app.generate.lint import lint_layers
from app.utils.hashing import stable_hash

router = APIRouter()

@router.post("/parse_preferences")
def parse_preferences(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal parser: accept either a full PreferenceSchema, or a naive NL fallback:
    payload = {"pilot_id": "...", "airline": "UAL", "base": "EWR", "seat": "FO", "equip": ["73G"],
               "text": "prefer layovers SAN,SJU; no redeyes"}
    """
    if "pilot_id" in payload and "airline" in payload and "seat" in payload and "equip" in payload:
        # assume it's already structured
        pref = PreferenceSchema(**{k: v for k, v in payload.items() if k != "text"})
        ask_backs: List[str] = []
        conf = 0.95
        return {"preference_schema": pref.model_dump(), "ask_backs": ask_backs, "confidence": conf}

    # naive NL fallback (deterministic, simple)
    text = (payload.get("text") or "").lower()
    if not text:
        raise HTTPException(400, "text required for NL parsing")
    lays = []
    if "san" in text: lays.append("SAN")
    if "sju" in text: lays.append("SJU")
    no_redeyes = ("no red" in text) or ("no redeye" in text)
    pref = PreferenceSchema(
        pilot_id=payload.get("pilot_id", "unknown"),
        airline="UAL",
        base=payload.get("base", "EWR"),
        seat=payload.get("seat", "FO"),
        equip=payload.get("equip", ["73G"]),
        hard_constraints={"no_red_eyes": no_redeyes},
        soft_prefs={"layovers": {"prefer": lays, "weight": 1.0}} if lays else {}
    )
    return {"preference_schema": pref.model_dump(), "ask_backs": [], "confidence": 0.80}

@router.post("/validate")
def validate(payload: Dict[str, Any]) -> Dict[str, Any]:
    pref = PreferenceSchema(**payload["preference_schema"])
    ctx = ContextSnapshot(**payload["context"])
    # fusion inputs (precheck/analytics/pairings) can be empty for validation
    bundle = FeatureBundle(
        context=ctx, preference_schema=pref,
        analytics_features=payload.get("analytics", {}),
        compliance_flags=payload.get("precheck", {}),
        pairing_features=payload.get("pairings", {}),
    )
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml")
    result = validate_feasibility(bundle, rules)
    return {"violations": result.get("violations", []), "feasible_pairings": result.get("feasible_pairings", [])}

@router.post("/optimize")
def optimize(payload: Dict[str, Any]) -> Dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    rules = load_rule_pack("rule_packs/UAL/2025.08.yml")
    feas = validate_feasibility(bundle, rules)
    feas_list = feas.get("feasible_pairings", [])
    topk = rank_candidates(bundle, feas_list, K=int(payload.get("K", 10)))
    return {"candidates": [c.model_dump() for c in topk]}

@router.post("/strategy")
def strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    topk = [CandidateSchedule(**x) for x in payload["candidates"]]
    directives = propose_strategy(bundle, topk)
    return {"directives": directives.model_dump()}

@router.post("/generate_layers")
def generate_layers(payload: Dict[str, Any]) -> Dict[str, Any]:
    bundle = FeatureBundle(**payload["feature_bundle"])
    topk = [CandidateSchedule(**x) for x in payload["candidates"]]
    artifact = candidates_to_layers(topk, bundle)
    # deterministic export hash
    artifact_dict = artifact.model_dump()
    artifact_dict["export_hash"] = stable_hash({"bundle": bundle.model_dump(), "candidates": [c.model_dump() for c in topk]})
    return {"artifact": artifact_dict}

@router.post("/lint")
def lint(payload: Dict[str, Any]) -> Dict[str, Any]:
    art = BidLayerArtifact(**payload["artifact"])
    report = lint_layers(art)
    return report
