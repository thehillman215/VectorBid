from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import httpx
import json
import os
from typing import Dict, Any, Optional
import csv
import io

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

# Backend URL from environment or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

async def get_http_client():
    """Dependency to get HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main UI page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/parse-preview", response_class=HTMLResponse)
async def parse_preview(
    request: Request,
    preferences: str = Form(...),
    persona: str = Form(...),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Parse preferences and return preview chips"""
    try:
        # For now, do local parsing until backend endpoint is ready
        parsed_items = []

        # Simple keyword extraction
        keywords = {
            "weekends": "Weekends Off",
            "red-eye": "No Red-eyes",
            "redeye": "No Red-eyes",
            "commute": "Commuter",
            "layover": "Layover Preference",
            "money": "High Pay",
            "senior": "Seniority",
        }

        pref_lower = preferences.lower()
        for key, label in keywords.items():
            if key in pref_lower:
                parsed_items.append(label)

        if persona:
            parsed_items.append(f"Persona: {persona.title()}")

        return templates.TemplateResponse(
            "partials/_parse_chips.html",
            {"request": request, "items": parsed_items},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/_alerts.html",
            {"request": request, "error": str(e), "type": "error"},
        )

@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(
    request: Request,
    preferences: str = Form(...),
    persona: str = Form(...),
    airline: str = Form("UAL"),
    base: str = Form("EWR"),
    seat: str = Form("FO"),
    equipment: str = Form("73G"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Run full pipeline and return results"""
    try:
        # Build the full pipeline request
        pilot_context = {
            "pilot_id": "user1",
            "airline": airline,
            "base": base,
            "seat": seat,
            "equip": [equipment],
        }

        # For MVP, create mock PBS layers
        pbs_layers = [
            "AVOID PAIRINGS",
            "  IF REPORT < 0800",
            "  IF LAYOVER CITY = 'LAS'",
            "",
            "PREFER PAIRINGS",
            "  IF LAYOVER CITY = 'SAN'",
            "  IF CREDIT > 5:00",
            "",
            "AWARD PAIRINGS",
            "  IF DOW = 'SAT,SUN' POINTS -100",
            "  IF REPORT > 0600 AND REPORT < 1000 POINTS +50",
        ]

        # Create results
        results = {
            "pbs_layers": pbs_layers,
            "stats": {
                "total_pairings": 127,
                "filtered": 45,
                "preferred": 12,
                "success_probability": "73%",
            },
            "warnings": [],
            "pilot_context": pilot_context,
        }

        return templates.TemplateResponse(
            "partials/_results_table.html",
            {"request": request, "results": results},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/_alerts.html",
            {"request": request, "error": str(e), "type": "error"},
        )

@router.get("/download/csv")
async def download_csv(data: str = ""):
    """Download results as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Layer", "Command"])
    # Add data rows here

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vectorbid-results.csv"},
    )

@router.get("/health-check", response_class=JSONResponse)
async def health_check(client: httpx.AsyncClient = Depends(get_http_client)):
    """Check backend health"""
    try:
        response = await client.get(f"{BACKEND_URL}/health")
        return {"backend": "online", "status": response.json()}
    except Exception:
        return {"backend": "offline", "status": None}
