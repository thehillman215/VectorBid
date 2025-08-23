"""
Contract Management API Routes

Endpoints for uploading, processing, and managing pilot contracts.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.services.contract_extractor_v2 import ContractExtractorV2
from app.services.llm_service import LLMService
from app.services.pilot_assistant import PilotAssistant
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

# Initialize services (in production, use dependency injection)
llm_service = LLMService(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

vector_store = VectorStoreService(
    store_type=os.getenv("VECTOR_STORE_TYPE", "memory"),
    llm_service=llm_service,
)

contract_extractor = ContractExtractorV2(
    llm_service=llm_service,
    vector_store=vector_store,
)

pilot_assistant = PilotAssistant(
    llm_service=llm_service,
    vector_store=vector_store,
)


class ContractUploadResponse(BaseModel):
    """Response for contract upload"""
    contract_id: str
    status: str
    message: str
    processing_time: Optional[float] = None
    rules_extracted: Optional[int] = None
    estimated_cost: Optional[float] = None


class RuleSearchRequest(BaseModel):
    """Request for searching contract rules"""
    query: str
    airline: str
    contract_version: str
    category: Optional[str] = None
    top_k: int = 50


class ScheduleEvaluationRequest(BaseModel):
    """Request for schedule evaluation"""
    pilot_preferences: dict
    candidate_schedules: list
    airline: str
    contract_version: str
    explain_details: bool = True


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    airline: str = Form(...),
    version: str = Form(...),
    auto_approve: bool = Form(False),
):
    """
    Upload and process a new contract PDF.
    
    This endpoint:
    1. Accepts a PDF contract file
    2. Extracts all rules using Claude 3 Opus (heavy model)
    3. Validates rules using GPT-4 Turbo (fast model)
    4. Stores rules in vector database for semantic search
    5. Generates YAML rule pack for compatibility
    
    Args:
        file: PDF contract file
        airline: Airline code (e.g., "UAL", "DAL")
        version: Contract version (e.g., "2025.08")
        auto_approve: Skip manual approval for high-confidence extractions
    
    Returns:
        Upload status and extraction results
    """
    
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are supported")
        
        # Save uploaded file temporarily
        temp_dir = Path("/tmp/contract_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / f"{airline}_{version}_{datetime.now().timestamp()}.pdf"
        
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Processing contract: {airline} v{version} ({len(content)} bytes)")
        
        # Estimate processing cost
        page_count = len(content) // 3000  # Rough estimate
        estimated_cost = llm_service.estimate_cost(
            model="claude-3-opus-20240229",
            input_tokens=page_count * 800,  # ~800 tokens per page
            output_tokens=page_count * 200,  # Expected output
        )
        
        # Process contract
        result = await contract_extractor.process_contract(
            pdf_path=temp_path,
            airline=airline,
            version=version,
            auto_approve=auto_approve,
        )
        
        # Clean up temp file
        temp_path.unlink()
        
        if result["status"] == "success":
            return ContractUploadResponse(
                contract_id=f"{airline}_{version}",
                status="success",
                message=f"Successfully extracted {result['rules_extracted']} rules",
                processing_time=result["processing_time_seconds"],
                rules_extracted=result["rules_extracted"],
                estimated_cost=result["llm_costs"]["total_cost"],
            )
        else:
            raise HTTPException(500, f"Processing failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Contract upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@router.get("/list")
async def list_contracts(
    airline: Optional[str] = Query(None),
):
    """
    List all uploaded contracts.
    
    Args:
        airline: Optional filter by airline
    
    Returns:
        List of contract metadata
    """
    
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    
    async with AsyncSessionLocal() as session:
        query = select(PilotContract)
        if airline:
            query = query.where(PilotContract.airline == airline)
        
        result = await session.execute(query)
        contracts = result.scalars().all()
        
        return [
            {
                "id": str(contract.id),
                "airline": contract.airline,
                "version": contract.contract_version,
                "title": contract.title,
                "status": contract.status,
                "upload_date": contract.created_at.isoformat(),
                "rules_count": len(contract.parsed_data.get("rules", [])) if contract.parsed_data else 0,
            }
            for contract in contracts
        ]


@router.post("/search-rules")
async def search_rules(request: RuleSearchRequest):
    """
    Search for specific rules within a contract using semantic search.
    
    Args:
        request: Search parameters
    
    Returns:
        List of matching rules with relevance scores
    """
    
    try:
        results = await contract_extractor.search_contract_rules(
            query=request.query,
            airline=request.airline,
            version=request.contract_version,
            top_k=request.top_k,
        )
        
        return {
            "query": request.query,
            "results_count": len(results),
            "rules": results,
        }
        
    except Exception as e:
        logger.error(f"Rule search failed: {e}")
        raise HTTPException(500, f"Search failed: {str(e)}")


@router.get("/rules/{airline}/{version}")
async def get_contract_rules(
    airline: str,
    version: str,
    category: Optional[str] = Query(None),
):
    """
    Get all rules for a specific contract.
    
    Args:
        airline: Airline code
        version: Contract version
        category: Optional category filter
    
    Returns:
        All matching rules
    """
    
    try:
        rules = await contract_extractor.get_all_contract_rules(
            airline=airline,
            version=version,
            category=category,
        )
        
        return {
            "airline": airline,
            "version": version,
            "category": category,
            "rules_count": len(rules),
            "rules": rules,
        }
        
    except Exception as e:
        logger.error(f"Failed to get rules: {e}")
        raise HTTPException(500, f"Failed to get rules: {str(e)}")


@router.post("/evaluate-schedule")
async def evaluate_schedule(request: ScheduleEvaluationRequest):
    """
    Evaluate candidate schedules against contract rules and pilot preferences.
    
    This endpoint uses the fast runtime model (GPT-4 Turbo) with full contract
    context to provide comprehensive evaluation in under 2 seconds.
    
    Args:
        request: Evaluation parameters
    
    Returns:
        Detailed evaluation results for each schedule
    """
    
    try:
        evaluations = await pilot_assistant.evaluate_schedules(
            pilot_preferences=request.pilot_preferences,
            candidate_schedules=request.candidate_schedules,
            airline=request.airline,
            contract_version=request.contract_version,
            explain_details=request.explain_details,
        )
        
        # Convert to dict format
        results = []
        for eval in evaluations:
            results.append({
                "schedule_id": eval.schedule_id,
                "overall_score": eval.overall_score,
                "is_valid": eval.is_valid,
                "violations": eval.hard_violations,
                "penalties": eval.soft_penalties,
                "summary": eval.summary,
                "explanation": eval.detailed_explanation,
                "improvements": eval.improvements,
            })
        
        return {
            "evaluations": results,
            "performance": pilot_assistant.get_performance_stats(),
        }
        
    except Exception as e:
        logger.error(f"Schedule evaluation failed: {e}")
        raise HTTPException(500, f"Evaluation failed: {str(e)}")


@router.post("/approve/{contract_id}")
async def approve_contract_rules(
    contract_id: str,
    approved_rule_ids: list = [],
    rejected_rule_ids: list = [],
):
    """
    Approve or reject extracted contract rules.
    
    Args:
        contract_id: Contract identifier
        approved_rule_ids: List of approved rule IDs
        rejected_rule_ids: List of rejected rule IDs
    
    Returns:
        Approval status
    """
    
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import ContractRule, PilotContract
    
    async with AsyncSessionLocal() as session:
        # Update contract status
        airline, version = contract_id.split("_", 1)
        
        contract_query = select(PilotContract).where(
            PilotContract.airline == airline,
            PilotContract.contract_version == version,
        )
        result = await session.execute(contract_query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise HTTPException(404, "Contract not found")
        
        # Update approval status
        contract.status = "approved"
        contract.approved_at = datetime.now()
        
        # Remove rejected rules from vector store
        if rejected_rule_ids:
            await vector_store.store.delete(rejected_rule_ids)
            
            # Delete from database
            delete_query = select(ContractRule).where(
                ContractRule.contract_id == contract.id,
                ContractRule.rule_id.in_(rejected_rule_ids),
            )
            rules_to_delete = await session.execute(delete_query)
            for rule in rules_to_delete.scalars():
                session.delete(rule)
        
        await session.commit()
        
        return {
            "contract_id": contract_id,
            "status": "approved",
            "approved_rules": len(approved_rule_ids),
            "rejected_rules": len(rejected_rule_ids),
        }


@router.get("/stats")
async def get_system_stats():
    """
    Get system statistics for contract processing and evaluation.
    
    Returns:
        System performance metrics
    """
    
    return {
        "llm_service": llm_service.get_usage_stats(),
        "vector_store": vector_store.get_statistics(),
        "pilot_assistant": pilot_assistant.get_performance_stats(),
    }