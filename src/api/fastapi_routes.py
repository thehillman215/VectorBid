"""
FastAPI routes for VectorBid
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.core.extensions import get_db
from src.lib.pbs_command_generator import generate_pbs_commands
from src.lib.personas import PILOT_PERSONAS
from src.lib.bid_packet_manager import BidPacketManager

router = APIRouter()


# Pydantic models for request/response
class PBSGenerateRequest(BaseModel):
    preferences: str
    pilot_profile: Dict[str, Any] = {}


class PBSGenerateResponse(BaseModel):
    success: bool
    pbs_commands: List[str]
    preferences_processed: str
    pilot_profile: Dict[str, Any]


class PersonasResponse(BaseModel):
    success: bool
    personas: Dict[str, Any]
    count: int


class BidPacketsResponse(BaseModel):
    success: bool
    bid_packets: List[Dict[str, Any]]
    count: int
    filter_airline: Optional[str] = None


# Routes
@router.post("/pbs/generate", response_model=PBSGenerateResponse)
async def generate_pbs(request: PBSGenerateRequest, db: Session = Depends(get_db)):
    """Generate PBS commands from pilot preferences"""
    try:
        if not request.preferences:
            raise HTTPException(status_code=400, detail="Preferences text is required")
        
        pbs_commands = generate_pbs_commands(request.preferences, request.pilot_profile)
        
        return PBSGenerateResponse(
            success=True,
            pbs_commands=pbs_commands,
            preferences_processed=request.preferences,
            pilot_profile=request.pilot_profile
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PBS generation failed: {str(e)}")


@router.get("/personas", response_model=PersonasResponse)
async def get_personas():
    """Get available pilot personas"""
    try:
        return PersonasResponse(
            success=True,
            personas=PILOT_PERSONAS,
            count=len(PILOT_PERSONAS)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve personas: {str(e)}")


@router.get("/bid-packets", response_model=BidPacketsResponse)
async def get_bid_packets(airline: Optional[str] = None):
    """Get available bid packets"""
    try:
        manager = BidPacketManager()
        packets = manager.get_available_bid_packets(airline)
        
        return BidPacketsResponse(
            success=True,
            bid_packets=packets,
            count=len(packets),
            filter_airline=airline
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bid packets: {str(e)}")


@router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_status": "active",
        "framework": "FastAPI",
        "endpoints": [
            "/api/v1/pbs/generate",
            "/api/v1/personas",
            "/api/v1/bid-packets",
            "/api/v1/status"
        ]
    }