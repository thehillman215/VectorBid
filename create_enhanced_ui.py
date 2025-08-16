import os

# Create the enhanced UI with all suggested features
ui_route = '''from fastapi import APIRouter, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime
import json

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

PERSONAS = {
    "commuter": {
        "name": "🏠 Commuter",
        "icon": "🏠",
        "badges": ["Min Nights Away", "Day Trips", "Home Daily"],
        "default_text": "I want to minimize nights away from home. Prefer day trips and turns. Avoid back-to-back trips. Need to be home every night for family commitments. Prefer early morning departures with evening returns.",
        "priorities": {"time_home": 10, "pay": 4, "weekends": 7, "comfort": 6}
    },
    "family": {
        "name": "👨‍👩‍👧‍👦 Family First",
        "icon": "👨‍👩‍👧‍👦", 
        "badges": ["Weekends Off", "No Holidays", "Predictable"],
        "default_text": "I need weekends off for family time. Avoid all major holidays (Thanksgiving, Christmas, New Year). Want a predictable schedule with no surprises. School events are important - need flexibility for those dates.",
        "priorities": {"time_home": 9, "weekends": 10, "pay": 3, "comfort": 7}
    },
    "money": {
        "name": "💰 Money Maximizer",
        "icon": "💰",
        "badges": ["Max Credit", "Long Trips", "Holiday Pay"],
        "default_text": "I want maximum credit hours and highest pay. Give me the long international trips. I'll work holidays for premium pay. Prefer high-credit turns and efficient trips. Don't care about weekends off.",
        "priorities": {"pay": 10, "time_home": 2, "weekends": 2, "comfort": 3}
    },
    "seniority": {
        "name": "📈 Seniority Builder",
        "icon": "📈",
        "badges": ["Premium Routes", "Wide-body", "International"],
        "default_text": "I want to build seniority on premium routes. Prefer wide-body international flying. Looking for high-value trips that build my resume. Paris, London, Tokyo routes preferred. Avoid domestic short-hauls.",
        "priorities": {"pay": 7, "time_home": 5, "weekends": 5, "comfort": 8}
    },
    "quality": {
        "name": "✨ Quality of Life",
        "icon": "✨",
        "badges": ["No Red-eyes", "Good Layovers", "Easy Trips"],
        "default_text": "No red-eyes or early morning shows. Want good layover cities (SAN, DEN, SEA). Minimum 12-hour layovers for proper rest. Avoid short connections. Prefer 2-3 day trips maximum. Quality over quantity.",
        "priorities": {"comfort": 10, "time_home": 6, "weekends": 6, "pay": 4}
    }
}

# Mock saved preferences (in production, from database)
SAVED_PREFERENCES = {
    "pilot123": [
        {"name": "Christmas Week Off", "text": "I need December 24-26 completely off for family Christmas."},
        {"name": "Avoid East Coast", "text": "Avoid all East Coast destinations due to commute difficulties."},
        {"name": "Prefer West Routes", "text": "Prefer SAN, LAX, SFO, SEA layovers - better weather and hotels."}
    ]
}

# Mock history (in production, from database)
def get_pilot_history(pilot_id: str) -> dict:
    return {
        "last_month": {
            "persona": "family",
            "month": "December 2024",
            "success_rate": "87%"
        },
        "common_requests": [
            "Weekends off",
            "Christmas off", 
            "SAN layovers"
        ]
    }

def get_pilot_profile(pilot_id: Optional[str]) -> dict:
    if pilot_id:
        return {
            "pilot_id": pilot_id,
            "name": "Captain Sarah Chen",
            "airline": "UAL",
            "base": "EWR", 
            "seat": "CPT",
            "equipment": "787",
            "seniority": "1234",
            "hire_date": "2015-03-15"
        }
    return None

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, pilot_id: Optional[str] = Cookie(None)):
    """Main bidding page"""
    profile = get_pilot_profile(pilot_id)
    
    if not profile:
        return RedirectResponse(url="/onboarding", status_code=302)
    
    history = get_pilot_history(pilot_id)
    saved_prefs = SAVED_PREFERENCES.get(pilot_id, [])
    
    return templates.TemplateResponse("smart_bid.html", {
        "request": request,
        "profile": profile,
        "personas": PERSONAS,
        "current_month": "January 2025",
        "history": history,
        "saved_preferences": saved_prefs
    })

@router.get("/api/persona/{persona_id}", response_class=JSONResponse)
async def get_persona(persona_id: str):
    """API endpoint to get persona details"""
    if persona_id in PERSONAS:
        return PERSONAS[persona_id]
    return {"error": "Persona not found"}

@router.post("/generate-pbs", response_class=HTMLResponse)
async def generate_pbs(
    request: Request,
    pilot_id: Optional[str] = Cookie(None),
    persona: str = Form(...),
    preferences: str = Form(...),
    priority_time_home: int = Form(5),
    priority_pay: int = Form(5),
    priority_weekends: int = Form(5),
    priority_comfort: int = Form(5),
    save_preference: bool = Form(False)
):
    """Generate PBS commands"""
    profile = get_pilot_profile(pilot_id)
    
    pbs_layers = ["START PAIRINGS"]
    
    # Parse priorities
    if priority_weekends >= 8:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DOW CONTAINS SA,SU"
        ])
    
    if priority_time_home >= 8:
        pbs_layers.extend([
            "AVOID PAIRINGS", 
            "  IF TAFB > 48:00"
        ])
    
    if priority_pay >= 8:
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF CREDIT > 5:30 POINTS +100"
        ])
    
    # Parse text preferences
    pref_lower = preferences.lower()
    if "red-eye" in pref_lower or "redeye" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF REPORT < 0600 OR REPORT > 2300"
        ])
    
    if "christmas" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DATE IN (24DEC, 25DEC, 26DEC)"
        ])
    
    if "san" in pref_lower.upper() or "SAN" in preferences:
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF LAYOVER = SAN POINTS +50"
        ])
    
    # Award with seniority
    pbs_layers.extend([
        "",
        "AWARD PAIRINGS",
        "  IN SENIORITY ORDER",
        "",
        "END PAIRINGS"
    ])
    
    results = {
        "pbs_layers": pbs_layers,
        "profile": profile,
        "persona": PERSONAS.get(persona, {}),
        "month": "January 2025",
        "estimated_success": "78%",
        "warnings": [],
        "stats": {
            "total_pairings": 156,
            "matching": 42,
            "blocked": 18
        }
    }
    
    return templates.TemplateResponse("pbs_results.html", {
        "request": request,
        "results": results
    })

@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    """One-time setup"""
    return templates.TemplateResponse("onboarding.html", {"request": request})

@router.post("/save-profile")
async def save_profile(
    request: Request,
    airline: str = Form(...),
    base: str = Form(...),
    seat: str = Form(...),
    equipment: str = Form(...),
    seniority: str = Form(...)
):
    """Save pilot profile"""
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="pilot_id", value="pilot123")
    return response
'''

with open("app/routes/ui.py", "w") as f:
    f.write(ui_route)

print("✅ Enhanced routes created with all features!")
