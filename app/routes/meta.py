import sys
from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/meta/health")
def meta_health():
    """Health check endpoint with service details."""
    return {
        "ok": True,
        "service": "api",
        "version": "1.0.0",
        "py": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "now": datetime.now().isoformat()
    }


@router.get("/api/meta/parsers")
def meta_parsers():
    """Get supported parser formats and fields."""
    return {
        "supported_formats": [
            {
                "extension": ".csv",
                "description": "Comma-separated values with pairings and trips",
                "fields": ["pairing_id", "base", "fleet", "month", "trip_id", "day", "origin", "destination"]
            },
            {
                "extension": ".jsonl",
                "description": "JSON Lines format with pairing objects",
                "fields": ["pairing_id", "base", "fleet", "month", "trips"]
            },
            {
                "extension": ".pdf",
                "description": "PDF bid packages (United Airlines format supported)",
                "fields": ["trip_id", "days", "credit_hours", "route", "equipment"]
            },
            {
                "extension": ".txt",
                "description": "Text files with trip information",
                "fields": ["trip_id", "days", "credit_hours", "route"]
            }
        ],
        "required_fields": {
            "airline": "Airline code (e.g., UAL)",
            "month": "Bid month (e.g., 2025-09)",
            "base": "Pilot base (e.g., SFO)",
            "fleet": "Aircraft fleet (e.g., 737)",
            "seat": "Pilot seat (FO or CA)",
            "pilot_id": "Pilot identifier"
        },
        "parser_version": "1.0.0"
    }
