import os

# Create updated UI with separated workflows
ui_route = '''from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import json

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

PERSONAS = {
    "commuter": {
        "name": "🏠 Commuter",
        "defaults": "Minimize nights away from home, prefer day trips, avoid back-to-back trips",
        "priorities": {"time_home": 10, "pay": 5, "easy_trips": 7}
    },
    "family": {
        "name": "👨‍👩‍👧‍👦 Family First", 
        "defaults": "Weekends off, no holidays, predictable schedule",
        "priorities": {"time_home": 10, "weekends": 10, "pay": 3}
    },
    "money": {
        "name": "💰 Money Maximizer",
        "defaults": "Maximum credit hours, international trips, holiday pay",
        "priorities": {"pay": 10, "credit": 10, "time_home": 2}
    },
    "seniority": {
        "name": "📈 Seniority Builder",
        "defaults": "High-value trips, wide-body equipment, international",
        "priorities": {"equipment": 8, "international": 9, "pay": 7}
    },
    "quality": {
        "name": "✨ Quality of Life",
        "defaults": "No red-eyes, good layovers, reasonable show times",
        "priorities": {"comfort": 10, "rest": 9, "time_home": 6}
    }
}

# Mock pilot profile (in production, this would be from database)
def get_pilot_profile(pilot_id: Optional[str]) -> dict:
    if pilot_id:
        # Mock data - replace with database lookup
        return {
            "pilot_id": pilot_id,
            "name": "Captain Smith",
            "airline": "UAL",
            "base": "EWR", 
            "seat": "CPT",
            "equipment": "737",
            "seniority": "1234",
            "hire_date": "2015-03-15"
        }
    return None

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, pilot_id: Optional[str] = Cookie(None)):
    """Main page - check if pilot has profile"""
    profile = get_pilot_profile(pilot_id)
    
    if not profile:
        # First time - redirect to onboarding
        return RedirectResponse(url="/onboarding", status_code=302)
    
    # Has profile - show monthly bid workflow
    return templates.TemplateResponse("monthly_bid.html", {
        "request": request,
        "profile": profile,
        "personas": PERSONAS,
        "current_month": "January 2025"
    })

@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    """One-time pilot profile setup"""
    return templates.TemplateResponse("onboarding.html", {"request": request})

@router.post("/save-profile", response_class=HTMLResponse)
async def save_profile(
    request: Request,
    airline: str = Form(...),
    base: str = Form(...),
    seat: str = Form(...),
    equipment: str = Form(...),
    seniority: str = Form(...),
    hire_date: str = Form(None)
):
    """Save pilot profile and redirect to bidding"""
    # In production, save to database
    # For now, just set a cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="pilot_id", value="pilot123")
    return response

@router.get("/profile", response_class=HTMLResponse) 
async def profile_settings(request: Request, pilot_id: Optional[str] = Cookie(None)):
    """Edit pilot profile settings"""
    profile = get_pilot_profile(pilot_id)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": profile
    })

@router.post("/generate-pbs", response_class=HTMLResponse)
async def generate_pbs(
    request: Request,
    pilot_id: Optional[str] = Cookie(None),
    persona: str = Form(...),
    preferences: str = Form(...),
    priority_time_home: int = Form(5),
    priority_pay: int = Form(5),
    priority_weekends: int = Form(5),
    priority_comfort: int = Form(5)
):
    """Generate PBS commands for monthly bid"""
    profile = get_pilot_profile(pilot_id)
    
    # Generate PBS based on profile + persona + preferences
    pbs_layers = []
    
    # High priority items
    if priority_weekends >= 8:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DOW CONTAINS SA,SU"
        ])
    
    if priority_time_home >= 8:
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF TAFB < 48:00"
        ])
    
    # Parse custom preferences
    pref_lower = preferences.lower()
    if "red-eye" in pref_lower or "redeye" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF REPORT < 0600"
        ])
    
    if "christmas" in pref_lower or "holiday" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DATE IN (24DEC, 25DEC, 26DEC)"
        ])
    
    # Default
    pbs_layers.extend([
        "",
        "AWARD PAIRINGS",
        "  IN SENIORITY ORDER"
    ])
    
    results = {
        "pbs_layers": pbs_layers,
        "profile": profile,
        "persona": PERSONAS.get(persona, {}),
        "month": "January 2025"
    }
    
    return templates.TemplateResponse("pbs_results.html", {
        "request": request,
        "results": results
    })
'''

with open("app/routes/ui.py", "w") as f:
    f.write(ui_route)

print("✅ Updated UI routes with proper workflow separation!")
