import os

# Create enhanced UI route with personas and sliders
ui_route = """from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

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
        "defaults": "Weekends off, no holidays, predictable schedule, home every night if possible",
        "priorities": {"time_home": 10, "weekends": 10, "pay": 3}
    },
    "money": {
        "name": "💰 Money Maximizer",
        "defaults": "Maximum credit hours, international trips, holiday pay, long trips OK",
        "priorities": {"pay": 10, "credit": 10, "time_home": 2}
    },
    "seniority": {
        "name": "📈 Seniority Builder",
        "defaults": "High-value trips, wide-body equipment, international routes",
        "priorities": {"equipment": 8, "international": 9, "pay": 7}
    },
    "quality": {
        "name": "✨ Quality of Life",
        "defaults": "No red-eyes, good layover cities, reasonable show times, avoid short layovers",
        "priorities": {"comfort": 10, "rest": 9, "time_home": 6}
    }
}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("pilot_form.html", {
        "request": request,
        "personas": PERSONAS
    })

@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(
    request: Request,
    persona: str = Form(...),
    preferences: str = Form(...),
    airline: str = Form("UAL"),
    base: str = Form("EWR"),
    equipment: str = Form("737"),
    priority_time_home: int = Form(5),
    priority_pay: int = Form(5),
    priority_weekends: int = Form(5),
    priority_comfort: int = Form(5)
):
    # Generate PBS based on persona + custom preferences + priorities
    pbs_layers = []
    
    # Apply persona defaults
    if persona in PERSONAS:
        persona_data = PERSONAS[persona]
        
        # High priority items go first in PBS
        if priority_weekends >= 8:
            pbs_layers.extend([
                "AVOID PAIRINGS",
                "  IF DOW CONTAINS SA,SU"
            ])
        
        if priority_time_home >= 8:
            pbs_layers.extend([
                "PREFER PAIRINGS",
                "  IF TAFB < 48:00"  # Time away from base < 48 hours
            ])
    
    # Parse custom preferences
    pref_lower = preferences.lower()
    
    if "weekend" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DOW CONTAINS SA,SU"
        ])
    
    if "red-eye" in pref_lower or "redeye" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF REPORT < 0600 OR RELEASE > 2300"
        ])
    
    if "SAN" in preferences.upper():
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF LAYOVER = SAN POINTS +100"
        ])
    
    if "christmas" in pref_lower or "holiday" in pref_lower:
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DATE IN (24DEC, 25DEC, 26DEC, 31DEC, 01JAN)"
        ])
    
    # Add priority-based scoring
    if priority_pay >= 7:
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF CREDIT > 5:30 POINTS +50"
        ])
    
    # Default award
    pbs_layers.extend([
        "",
        "AWARD PAIRINGS",
        "  IN SENIORITY ORDER"
    ])
    
    results = {
        "pbs_layers": pbs_layers,
        "airline": airline,
        "base": base,
        "equipment": equipment,
        "persona": PERSONAS.get(persona, {}),
        "priorities": {
            "time_home": priority_time_home,
            "pay": priority_pay,
            "weekends": priority_weekends,
            "comfort": priority_comfort
        }
    }
    
    return templates.TemplateResponse("pilot_results.html", {
        "request": request,
        "results": results
    })
"""

with open("app/routes/ui.py", "w") as f:
    f.write(ui_route)

print("✅ Pilot UI route created!")
