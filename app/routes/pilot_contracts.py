"""
Pilot Contract Routes

Pilot-facing endpoints for using contracts (read-only access to active contracts).
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.dependencies import require_pilot_role
from app.services.pilot_assistant import PilotAssistant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pilot/contracts", tags=["pilot-contracts"])

# Initialize services
pilot_assistant = PilotAssistant()


class ActiveContractResponse(BaseModel):
    """Response for active contract information"""
    airline: str
    version: str
    effective_date: date
    expiration_date: date
    title: str
    rules_count: int
    last_updated: datetime


class ScheduleEvaluationRequest(BaseModel):
    """Request for schedule evaluation"""
    pilot_preferences: dict
    candidate_schedules: list
    explain_details: bool = True


class RuleSearchRequest(BaseModel):
    """Request for rule search"""
    query: str
    category: Optional[str] = None
    limit: int = 50


@router.get("/active/{airline}", dependencies=[Depends(require_pilot_role)])
async def get_active_contract(
    airline: str,
    current_user: dict = Depends(require_pilot_role),
) -> ActiveContractResponse:
    """
    Get the currently active contract for an airline.
    
    Pilots can only access active contracts, not historical ones.
    
    Args:
        airline: Airline code (e.g., UAL, DAL)
        current_user: Authenticated pilot user
    
    Returns:
        Active contract information
    """
    
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    
    async with AsyncSessionLocal() as session:
        # Find active contract
        query = select(PilotContract).where(
            PilotContract.airline == airline,
            PilotContract.status == "active"
        )
        
        result = await session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            # Check metadata for is_active flag
            query = select(PilotContract).where(
                PilotContract.airline == airline
            )
            result = await session.execute(query)
            contracts = result.scalars().all()
            
            for c in contracts:
                if c.metadata and c.metadata.get("is_active"):
                    contract = c
                    break
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active contract found for {airline}"
            )
        
        metadata = contract.metadata or {}
        
        return ActiveContractResponse(
            airline=contract.airline,
            version=contract.contract_version,
            effective_date=date.fromisoformat(metadata.get("effective_date", "2025-01-01")),
            expiration_date=date.fromisoformat(metadata.get("expiration_date", "2026-01-01")),
            title=contract.title,
            rules_count=contract.parsed_data.get("rules_extracted", 0) if contract.parsed_data else 0,
            last_updated=contract.updated_at,
        )


@router.post("/evaluate", dependencies=[Depends(require_pilot_role)])
async def evaluate_schedule(
    request: ScheduleEvaluationRequest,
    airline: str = Query(..., description="Airline code"),
    current_user: dict = Depends(require_pilot_role),
):
    """
    Evaluate schedules against the active contract.
    
    Uses the fast runtime model with full contract context for <2 second responses.
    
    Args:
        request: Evaluation parameters
        airline: Airline code
        current_user: Authenticated pilot
    
    Returns:
        Schedule evaluations with explanations
    """
    
    # Get active contract version
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    
    async with AsyncSessionLocal() as session:
        # Find active contract
        query = select(PilotContract).where(
            PilotContract.airline == airline
        )
        result = await session.execute(query)
        contracts = result.scalars().all()
        
        active_contract = None
        for contract in contracts:
            if contract.metadata and contract.metadata.get("is_active"):
                active_contract = contract
                break
        
        if not active_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active contract found for {airline}"
            )
        
        # Log pilot usage
        logger.info(
            f"Pilot {current_user['email']} evaluating schedules against "
            f"{airline} v{active_contract.contract_version}"
        )
        
        # Evaluate schedules
        evaluations = await pilot_assistant.evaluate_schedules(
            pilot_preferences=request.pilot_preferences,
            candidate_schedules=request.candidate_schedules,
            airline=airline,
            contract_version=active_contract.contract_version,
            explain_details=request.explain_details,
        )
        
        # Format response
        results = []
        for eval in evaluations:
            results.append({
                "schedule_id": eval.schedule_id,
                "score": eval.overall_score,
                "is_valid": eval.is_valid,
                "violations": eval.hard_violations,
                "summary": eval.summary,
                "explanation": eval.detailed_explanation if request.explain_details else None,
                "suggestions": eval.improvements,
            })
        
        return {
            "contract_version": active_contract.contract_version,
            "evaluations": results,
            "evaluated_at": datetime.now().isoformat(),
        }


@router.post("/search-rules", dependencies=[Depends(require_pilot_role)])
async def search_contract_rules(
    request: RuleSearchRequest,
    airline: str = Query(..., description="Airline code"),
    current_user: dict = Depends(require_pilot_role),
):
    """
    Search for rules in the active contract.
    
    Uses semantic search to find relevant rules.
    
    Args:
        request: Search parameters
        airline: Airline code
        current_user: Authenticated pilot
    
    Returns:
        Matching rules from active contract
    """
    
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    
    async with AsyncSessionLocal() as session:
        # Get active contract
        query = select(PilotContract).where(
            PilotContract.airline == airline
        )
        result = await session.execute(query)
        contracts = result.scalars().all()
        
        active_contract = None
        for contract in contracts:
            if contract.metadata and contract.metadata.get("is_active"):
                active_contract = contract
                break
        
        if not active_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active contract found for {airline}"
            )
        
        # Search rules
        from app.services.contract_extractor_v2 import ContractExtractorV2
        extractor = ContractExtractorV2()
        
        results = await extractor.search_contract_rules(
            query=request.query,
            airline=airline,
            version=active_contract.contract_version,
            top_k=request.limit,
        )
        
        # Filter by category if specified
        if request.category:
            results = [r for r in results if r.get("category") == request.category]
        
        return {
            "query": request.query,
            "contract_version": active_contract.contract_version,
            "results_count": len(results),
            "rules": results,
        }


@router.get("/available-airlines", dependencies=[Depends(require_pilot_role)])
async def get_available_airlines(
    current_user: dict = Depends(require_pilot_role),
) -> List[str]:
    """
    Get list of airlines with active contracts.
    
    Args:
        current_user: Authenticated pilot
    
    Returns:
        List of airline codes with active contracts
    """
    
    from sqlalchemy import distinct, select

    from app.db.database import AsyncSessionLocal
    from app.db.models import PilotContract
    
    async with AsyncSessionLocal() as session:
        # Find all airlines with active contracts
        query = select(distinct(PilotContract.airline)).where(
            PilotContract.status == "active"
        )
        
        result = await session.execute(query)
        active_airlines = result.scalars().all()
        
        # Also check metadata
        if not active_airlines:
            query = select(PilotContract)
            result = await session.execute(query)
            contracts = result.scalars().all()
            
            airlines_set = set()
            for contract in contracts:
                if contract.metadata and contract.metadata.get("is_active"):
                    airlines_set.add(contract.airline)
            
            active_airlines = list(airlines_set)
        
        return sorted(active_airlines)


@router.get("/my-preferences", dependencies=[Depends(require_pilot_role)])
async def get_pilot_preferences(
    current_user: dict = Depends(require_pilot_role),
):
    """
    Get saved preferences for the current pilot.
    
    Args:
        current_user: Authenticated pilot
    
    Returns:
        Pilot's saved preferences
    """
    
    from sqlalchemy import select

    from app.db.database import AsyncSessionLocal
    from app.db.models import Pilot, Preference
    
    async with AsyncSessionLocal() as session:
        # Get pilot profile
        query = select(Pilot).where(
            Pilot.user_id == current_user["id"]
        )
        result = await session.execute(query)
        pilot = result.scalar_one_or_none()
        
        if not pilot:
            return {
                "preferences": {},
                "message": "No pilot profile found"
            }
        
        # Get preferences
        pref_query = select(Preference).where(
            Preference.pilot_id == pilot.pilot_id
        ).order_by(Preference.created_at.desc())
        
        pref_result = await session.execute(pref_query)
        preference = pref_result.scalar_one_or_none()
        
        if preference:
            return {
                "pilot_id": pilot.pilot_id,
                "airline": pilot.airline,
                "base": pilot.base,
                "preferences": preference.data,
                "last_updated": preference.created_at.isoformat(),
            }
        else:
            return {
                "pilot_id": pilot.pilot_id,
                "airline": pilot.airline,
                "base": pilot.base,
                "preferences": {},
                "message": "No preferences saved"
            }