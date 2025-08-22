# app/api/routes.py
from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.audit import log_event
from app.db import Audit, SessionLocal
from app.explain.legal import explain as explain_legal
from app.export.audit import get_record, insert_record
from app.export.storage import write_artifact
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
from app.security.api_key import require_api_key
from app.services.optimizer import retune_candidates, select_topk
from app.strategy.engine import propose_strategy

router = APIRouter()

# Import satisfaction engine (with fallback if not available)
try:
    from app.services.satisfaction import SatisfactionEngine, create_default_request
    from app.services.satisfaction.types import BidLayer, PilotContext
    SATISFACTION_AVAILABLE = True
except ImportError:
    SATISFACTION_AVAILABLE = False


RULE_PACK_PATH = "rule_packs/UAL/2025.08.yml"
_RULES = load_rule_pack(RULE_PACK_PATH)
CANDIDATE_STORE: dict[str, CandidateSchedule] = {}


@router.post("/parse_preferences", tags=["Parse"])
async def parse_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    """
    PRIMARY: LLM parses natural language preferences
    FALLBACK: Rule-based parsing if LLM fails

    Body:
      {
        "preferences_text": "I want weekends off and no red-eyes",
        "persona": "family_first", 
        "airline": "UAL",
        "pilot_context": {"base": "SFO", "equipment": ["737"], "seniority_percentile": 0.65}
      }
    Returns: {
        "parsed_preferences": {...}, 
        "confidence": 0.85,
        "method": "llm|fallback",
        "suggestions": [...],
        "warnings": [...]
    }
    """
    try:
        from app.services.llm_parser import PreferenceParser
        
        preferences_text = payload.get("preferences_text", "")
        persona = payload.get("persona")
        airline = payload.get("airline", "UAL")
        pilot_context = payload.get("pilot_context", {})
        
        if not preferences_text.strip():
            raise HTTPException(status_code=400, detail="preferences_text cannot be empty")
        
        # Initialize LLM parser
        parser = PreferenceParser()
        
        # LLM-first parsing with fallback
        result = await parser.parse_preferences(
            text=preferences_text,
            persona=persona,
            airline=airline,
            pilot_context=pilot_context
        )
        
        return {
            "parsed_preferences": result.preferences.model_dump(),
            "confidence": result.confidence,
            "method": result.parsing_method.value,
            "reasoning": result.reasoning,
            "suggestions": result.suggestions,
            "warnings": result.warnings,
            "model_version": result.model_version,
            "tokens_used": result.tokens_used
        }
        
    except ImportError:
        # Fallback if LLM service not available
        print("⚠️ LLM service not available, using basic parsing")
        parsed = {
            "hard_constraints": {
                "no_weekends": "weekend" in preferences_text.lower(),
                "no_redeyes": "red-eye" in preferences_text.lower() or "redeye" in preferences_text.lower(),
            },
            "soft_prefs": {
                "weekend_priority": 0.8 if "weekend" in preferences_text.lower() else 0.3,
                "departure_time_weight": 0.6 if "morning" in preferences_text.lower() else 0.3,
            },
            "confidence": 0.6,
            "source": {"method": "basic_fallback"}
        }

        return {
            "parsed_preferences": parsed,
            "confidence": 0.6,
            "method": "basic_fallback", 
            "reasoning": "LLM service unavailable, used basic keyword matching",
            "suggestions": [
                "Install LLM dependencies for better parsing",
                "Consider specifying layover preferences",
                "Add aircraft type preferences",
            ],
            "warnings": ["Basic parsing may miss nuanced preferences"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/parse_preview", tags=["Parse"])
def parse_preview(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a PreferenceSchema preview without persistence."""
    try:
        text = payload.get("text", "")
        persona = payload.get("persona")
        hard = HardConstraints(no_red_eyes="red-eye" in text.lower() or "redeye" in text.lower())
        soft = SoftPrefs(weekend_priority={"weight": 0.9} if "weekend" in text.lower() else {})
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


@router.post("/validate_constraints", tags=["Validate"])
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
        cand.rationale.notes.extend(explain_legal(cand, report))
        # Store candidates for later retrieval
        CANDIDATE_STORE[cand.candidate_id] = cand
    return {"candidates": [c.model_dump() for c in topk]}


@router.post("/optimize_enhanced", tags=["Optimize"])
async def optimize_enhanced(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Enhanced optimization with LLM-guided analysis
    
    Body:
      {
        "feature_bundle": {...},
        "K": 50,
        "use_llm": true,
        "pilot_context": {...}
      }
    Returns: {
        "enhanced_candidates": [...],
        "optimization_analysis": {...},
        "recommendations": {...},
        "ai_insights": {...}
    }
    """
    try:
        # Step 1: Mathematical optimization (existing pipeline)
        bundle = FeatureBundle(**payload["feature_bundle"])
        K = int(payload.get("K", 50))
        use_llm = payload.get("use_llm", True)
        pilot_context = payload.get("pilot_context", {})
        
        # Get mathematical optimization results
        topk = select_topk(bundle, K)
        report = validate_feasibility(bundle, _RULES)
        
        for cand in topk:
            cand.rationale.notes.extend(explain_legal(cand, report))
            CANDIDATE_STORE[cand.candidate_id] = cand
        
        # Step 2: LLM enhancement (if enabled)
        if use_llm and topk:
            try:
                from app.services.llm_optimizer import LLMOptimizer
                
                optimizer = LLMOptimizer()
                
                # Extract preferences from bundle
                preferences = bundle.preference_schema
                
                # Run LLM-guided optimization
                llm_result = await optimizer.optimize_candidates(
                    candidates=topk,
                    preferences=preferences,
                    pilot_context=pilot_context,
                    feature_bundle=bundle
                )
                
                # Return enhanced results
                return {
                    "enhanced_candidates": [c.model_dump() for c in llm_result.enhanced_candidates],
                    "optimization_analysis": {
                        "quality": llm_result.optimization_quality,
                        "preference_alignment": llm_result.preference_alignment,
                        "trade_off_analysis": llm_result.trade_off_analysis,
                        "missing_opportunities": llm_result.missing_opportunities,
                        "risk_assessment": llm_result.risk_assessment
                    },
                    "recommendations": {
                        "recommended_candidate_id": llm_result.recommended_candidate_id,
                        "explanation": llm_result.explanation,
                        "alternative_choices": llm_result.alternative_choices,
                        "bidding_strategy": llm_result.bidding_strategy
                    },
                    "ai_insights": {
                        "confidence": llm_result.confidence,
                        "model_insights": llm_result.model_insights,
                        "method": llm_result.optimization_method.value,
                        "model_version": llm_result.model_version,
                        "tokens_used": llm_result.tokens_used
                    }
                }
                
            except Exception as llm_error:
                print(f"❌ LLM optimization failed: {llm_error}")
                # Fallback: Return mathematical results with notice
                return {
                    "enhanced_candidates": [c.model_dump() for c in topk],
                    "optimization_analysis": {
                        "quality": 0.7,
                        "preference_alignment": 0.6,
                        "trade_off_analysis": "AI analysis unavailable - mathematical optimization only",
                        "missing_opportunities": ["AI insights not available"],
                        "risk_assessment": ["Manual review recommended"]
                    },
                    "recommendations": {
                        "recommended_candidate_id": topk[0].candidate_id if topk else "",
                        "explanation": "Top mathematical candidate - AI analysis unavailable",
                        "alternative_choices": [],
                        "bidding_strategy": "Enable AI features for enhanced guidance"
                    },
                    "ai_insights": {
                        "confidence": 0.5,
                        "model_insights": ["AI analysis failed - check API configuration"],
                        "method": "mathematical_only",
                        "model_version": "fallback",
                        "tokens_used": 0
                    }
                }
        else:
            # Mathematical optimization only
            return {
                "enhanced_candidates": [c.model_dump() for c in topk],
                "optimization_analysis": {
                    "quality": 0.8,
                    "preference_alignment": 0.7,
                    "trade_off_analysis": "Mathematical optimization completed successfully",
                    "missing_opportunities": ["Enable AI analysis for enhanced insights"],
                    "risk_assessment": []
                },
                "recommendations": {
                    "recommended_candidate_id": topk[0].candidate_id if topk else "",
                    "explanation": "Top candidate from mathematical optimization",
                    "alternative_choices": [],
                    "bidding_strategy": "Mathematical optimization based on preferences"
                },
                "ai_insights": {
                    "confidence": 0.7,
                    "model_insights": ["Mathematical optimization only"],
                    "method": "mathematical_only", 
                    "model_version": "n/a",
                    "tokens_used": 0
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced optimization failed: {str(e)}"
        )


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
def export(payload: dict[str, Any]) -> dict[str, str]:
    """Protected export endpoint.

    Accepts: {"artifact": {...}, "ctx_id": "..."}
    Persists artifact, computes SHA256 signature, writes .sig, inserts audit row,
    and returns the id, path, and signature. Export succeeds even if DB insert fails.
    """
    try:
        art = payload.get("artifact", {})
        ctx_id = payload.get("ctx_id", "unknown")

        export_dir = Path(os.environ.get("EXPORT_DIR", Path.cwd() / "exports"))
        out_path = write_artifact(art, export_dir)

        data = out_path.read_bytes()

        # Use HMAC signing if EXPORT_SIGNING_KEY is set, otherwise fall back to SHA256
        signing_key = os.environ.get("EXPORT_SIGNING_KEY")
        if signing_key:
            signature = hmac.new(signing_key.encode(), data, hashlib.sha256).hexdigest()
        else:
            signature = hashlib.sha256(data).hexdigest()

        sig_path = out_path.with_suffix(out_path.suffix + ".sig")
        sig_path.write_text(signature, encoding="utf-8")

        export_id = out_path.stem
        try:
            insert_record(export_id, ctx_id, out_path, signature)
        except Exception as db_err:  # pragma: no cover - best effort
            log_event(ctx_id, "export_db_error", {"error": str(db_err)})

        log_event(
            ctx_id,
            "export_created",
            {
                "id": export_id,
                "export_path": str(out_path),
                "signature": signature,
            },
        )

        return {
            "id": export_id,
            "export_path": str(out_path),
            "path": str(out_path),
            "signature": signature,
            "sha256": signature,
        }
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/exports/{export_id}", tags=["Export"])
def get_export(export_id: str) -> dict[str, Any]:
    """Get export record by ID."""
    record = get_record(export_id)
    if not record:
        raise HTTPException(status_code=404, detail="export not found")
    return record


@router.get("/exports/{export_id}/download", tags=["Export"])
def download_export(export_id: str) -> FileResponse:
    """Download export file by ID."""
    record = get_record(export_id)
    if not record:
        raise HTTPException(status_code=404, detail="export not found")

    file_path = Path(record["path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="export file not found")

    return FileResponse(file_path, filename=f"{export_id}.json")


@router.get("/audit/{ctx_id}", tags=["Audit"])
def get_audit(ctx_id: str) -> dict[str, Any]:
    """Return audit trail for a given context."""
    with SessionLocal() as db:
        rows = db.query(Audit).filter(Audit.ctx_id == ctx_id).order_by(Audit.timestamp.asc()).all()
        events = [
            {
                "stage": r.stage,
                "timestamp": r.timestamp.isoformat(),
                "payload": r.payload,
            }
            for r in rows
        ]
    return {"events": events}


@router.post("/chat/start", tags=["AI Chat"])
async def start_chat_session(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Start a new conversation with VectorBot AI Assistant
    
    Body:
      {
        "user_id": "pilot_123",
        "pilot_context": {
          "base": "SFO",
          "equipment": ["737"],
          "seniority_percentile": 0.65,
          "career_stage": "captain"
        }
      }
    Returns: {
        "session_id": "pilot_123",
        "conversation": {...},
        "greeting_message": "...",
        "status": "active"
    }
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        user_id = payload.get("user_id")
        pilot_context = payload.get("pilot_context", {})
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        assistant = VectorBidChatAssistant()
        conversation = await assistant.start_conversation(user_id, pilot_context)
        
        # Get the greeting message
        greeting_message = conversation.messages[-1] if conversation.messages else None
        
        return {
            "session_id": user_id,
            "conversation": conversation.model_dump(),
            "greeting_message": greeting_message.content if greeting_message else "Hello! I'm VectorBot, ready to help with your bidding questions!",
            "status": "active",
            "created_at": conversation.created_at.isoformat()
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start chat session: {str(e)}")


@router.post("/chat/message", tags=["AI Chat"])
async def send_chat_message(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Send a message to VectorBot and get AI response
    
    Body:
      {
        "user_id": "pilot_123",
        "message": "How should I set my preferences for maximum family time?",
        "context_update": {
          "current_preferences": {...},
          "current_schedules": [...]
        }
      }
    Returns: {
        "response": "...",
        "timestamp": "...",
        "conversation_id": "pilot_123"
    }
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        user_id = payload.get("user_id")
        message = payload.get("message")
        context_update = payload.get("context_update")
        
        if not user_id or not message:
            raise HTTPException(status_code=400, detail="user_id and message are required")
        
        assistant = VectorBidChatAssistant()
        response = await assistant.chat(user_id, message, context_update)
        
        return {
            "response": response.content,
            "timestamp": response.timestamp.isoformat(),
            "conversation_id": user_id,
            "message_role": response.role,
            "context": response.context or {}
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")


@router.get("/chat/history/{user_id}", tags=["AI Chat"])
async def get_chat_history(user_id: str) -> dict[str, Any]:
    """
    Get conversation history for a user
    
    Returns: {
        "conversation": {...},
        "message_count": 10,
        "last_updated": "..."
    }
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        conversation = assistant.get_conversation_history(user_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="No conversation found for this user")
        
        return {
            "conversation": conversation.model_dump(),
            "message_count": len(conversation.messages),
            "last_updated": conversation.updated_at.isoformat(),
            "context": conversation.context
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.delete("/chat/{user_id}", tags=["AI Chat"])
async def clear_chat_history(user_id: str) -> dict[str, Any]:
    """Clear conversation history for a user"""
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        assistant = VectorBidChatAssistant()
        cleared = assistant.clear_conversation(user_id)
        
        return {
            "user_id": user_id,
            "cleared": cleared,
            "message": "Conversation history cleared" if cleared else "No conversation found"
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")


@router.post("/chat/analyze_preferences", tags=["AI Chat"])
async def chat_analyze_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Get AI analysis of pilot preferences through chat interface
    
    Body:
      {
        "user_id": "pilot_123",
        "preferences_text": "I want weekends off and good credit hours",
        "current_preferences": {...}
      }
    Returns: {
        "analysis": "...",
        "suggestions": [...],
        "conversation_updated": true
    }
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        user_id = payload.get("user_id")
        preferences_text = payload.get("preferences_text")
        current_preferences = payload.get("current_preferences")
        
        if not user_id or not preferences_text:
            raise HTTPException(status_code=400, detail="user_id and preferences_text are required")
        
        assistant = VectorBidChatAssistant()
        analysis = await assistant.analyze_preferences(user_id, preferences_text, current_preferences)
        
        return {
            "analysis": analysis,
            "user_id": user_id,
            "conversation_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze preferences: {str(e)}")


@router.post("/chat/compare_schedules", tags=["AI Chat"])
async def chat_compare_schedules(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Get AI comparison of schedule options through chat interface
    
    Body:
      {
        "user_id": "pilot_123",
        "schedules": [...],
        "pilot_priorities": "family time and decent credit hours"
      }
    Returns: {
        "comparison": "...",
        "recommendation": "...",
        "conversation_updated": true
    }
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        from app.models import CandidateSchedule
        
        user_id = payload.get("user_id")
        schedules_data = payload.get("schedules", [])
        pilot_priorities = payload.get("pilot_priorities")
        
        if not user_id or not schedules_data:
            raise HTTPException(status_code=400, detail="user_id and schedules are required")
        
        # Convert to CandidateSchedule objects
        schedules = [CandidateSchedule(**s) for s in schedules_data]
        
        assistant = VectorBidChatAssistant()
        comparison = await assistant.compare_schedules(user_id, schedules, pilot_priorities)
        
        return {
            "comparison": comparison,
            "user_id": user_id,
            "schedules_analyzed": len(schedules),
            "conversation_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare schedules: {str(e)}")


@router.get("/chat/tips/{category}", tags=["AI Chat"])
async def get_quick_tips(category: str = "general") -> dict[str, Any]:
    """
    Get quick bidding tips by category
    
    Categories: general, family, commuting, career
    """
    try:
        from app.services.chat_assistant import VectorBidChatAssistant
        
        valid_categories = ["general", "family", "commuting", "career"]
        if category not in valid_categories:
            category = "general"
        
        assistant = VectorBidChatAssistant()
        tips = await assistant.get_quick_tips(category)
        
        return {
            "category": category,
            "tips": tips,
            "available_categories": valid_categories
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Chat assistant not available - check AI dependencies"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tips: {str(e)}")


@router.post("/satisfaction_probability", tags=["Satisfaction"])
async def calculate_satisfaction_probability(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate realistic satisfaction probability for bid request.
    
    Body:
      {
        "pilot_context": {
          "base": "ORD",
          "equipment": "737", 
          "seniority_number": 150,
          "total_pilots": 400,
          "seniority_pct": 0.375
        },
        "bid_layers": [
          {
            "layer_id": "layer_1",
            "layer_type": "SET",
            "hard_constraints": ["weekends_off", "no_redeye"],
            "priority": 1
          }
        ],
        "month": 7
      }
    Returns: {
        "satisfaction_probability": 65.4,
        "satisfaction_ceiling": 70.0,
        "confidence_interval": [58.1, 72.7],
        "seniority_reality": "As #150 of 400 pilots...",
        "limiting_factors": [...],
        "improvement_suggestions": [...],
        "supply_demand_analysis": {...}
    }
    """
    if not SATISFACTION_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Satisfaction probability engine not available"
        )
    
    try:
        pilot_data = payload.get("pilot_context", {})
        layers_data = payload.get("bid_layers", [])
        month = payload.get("month", 6)
        
        if not pilot_data:
            raise HTTPException(status_code=400, detail="pilot_context is required")
        
        # Create pilot context
        pilot = PilotContext(**pilot_data)
        
        # Create bid layers
        layers = []
        for layer_data in layers_data:
            layers.append(BidLayer(**layer_data))
        
        # Calculate satisfaction
        engine = SatisfactionEngine()
        request = create_default_request(pilot, layers, month)
        result = engine.calculate_satisfaction(request)
        
        return {
            "satisfaction_probability": result.overall_satisfaction,
            "satisfaction_ceiling": result.satisfaction_ceiling,
            "confidence_interval": result.confidence_interval,
            "seniority_reality": result.seniority_reality,
            "limiting_factors": result.limiting_factors,
            "improvement_suggestions": result.improvement_levers,
            "supply_demand_analysis": result.supply_demand_analysis,
            "layer_probabilities": result.layer_probabilities,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Satisfaction calculation failed: {str(e)}")


@router.post("/satisfaction_quick_test", tags=["Satisfaction"])
async def satisfaction_quick_test() -> dict[str, Any]:
    """Quick test endpoint for satisfaction engine - returns sample results."""
    if not SATISFACTION_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Satisfaction probability engine not installed"
        }
    
    try:
        # Test with a few sample pilots
        engine = SatisfactionEngine()
        
        test_results = []
        
        # Senior pilot test
        senior_pilot = PilotContext(
            base="ORD", equipment="777", seniority_number=1, total_pilots=400, seniority_pct=0.0
        )
        senior_layers = [
            BidLayer(layer_id="1", layer_type="SET", hard_constraints=["weekends_off", "hawaii_layover"], priority=1)
        ]
        senior_result = engine.calculate_satisfaction(create_default_request(senior_pilot, senior_layers, 3))
        
        test_results.append({
            "pilot_type": "Senior (#1 of 400)",
            "satisfaction": senior_result.overall_satisfaction,
            "ceiling": senior_result.satisfaction_ceiling,
            "reality": senior_result.seniority_reality
        })
        
        # Junior pilot test
        junior_pilot = PilotContext(
            base="DEN", equipment="737", seniority_number=350, total_pilots=400, seniority_pct=0.875
        )
        junior_layers = [
            BidLayer(layer_id="1", layer_type="SET", hard_constraints=["weekends_off"], priority=1)
        ]
        junior_result = engine.calculate_satisfaction(create_default_request(junior_pilot, junior_layers, 12))
        
        test_results.append({
            "pilot_type": "Junior (#350 of 400)",
            "satisfaction": junior_result.overall_satisfaction,
            "ceiling": junior_result.satisfaction_ceiling,
            "reality": junior_result.seniority_reality
        })
        
        return {
            "status": "success",
            "message": "Satisfaction engine is working correctly",
            "test_results": test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Satisfaction engine test failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
