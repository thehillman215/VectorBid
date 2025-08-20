"""API routes for rule pack management."""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rule_pack_loader import rule_pack_loader

logger = logging.getLogger(__name__)

router = APIRouter()


class RulePackInfo(BaseModel):
    """Information about an available rule pack."""
    airline: str
    month: str
    path: str


@router.get("/api/rule-packs/{airline}/{month}")
async def get_rule_pack(airline: str, month: str):
    """Get rule pack for airline and month.
    
    Args:
        airline: Airline code (e.g., 'UAL')
        month: Month in format YYYY.MM (e.g., '2025.09')
        
    Returns:
        Rule pack data as JSON
        
    Raises:
        404: If rule pack not found
        500: If rule pack loading fails
    """
    try:
        rule_pack = rule_pack_loader.load_rule_pack(airline, month)
        return rule_pack.model_dump()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"Rule pack not found for {airline}/{month}"
        )
    except Exception as e:
        logger.error(f"Failed to load rule pack {airline}/{month}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to load rule pack: {e}"
        )


@router.get("/api/rule-packs", response_model=List[RulePackInfo])
async def list_rule_packs():
    """List available rule packs.
    
    Returns:
        List of available rule packs with airline, month, and path info
    """
    try:
        available_packs = rule_pack_loader.list_available_rule_packs()
        return [RulePackInfo(**pack) for pack in available_packs]
    except Exception as e:
        logger.error(f"Failed to list rule packs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list rule packs: {e}"
        )


@router.post("/api/rule-packs/clear-cache")
async def clear_rule_pack_cache():
    """Clear the rule pack cache.
    
    This forces reloading of rule packs from disk on next access.
    Useful for development or when rule pack files are updated.
    
    Returns:
        Success message
    """
    try:
        rule_pack_loader.clear_cache()
        return {"message": "Rule pack cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear rule pack cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {e}"
        )
