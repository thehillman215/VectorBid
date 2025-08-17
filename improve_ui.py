# Quick script to enhance the UI
import os

# Add more realistic PBS commands
ui_code = """from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(request: Request, 
                       preferences: str = Form(...),
                       airline: str = Form("UAL"),
                       base: str = Form("EWR")):
    # Parse preferences to generate PBS
    pbs_layers = []
    
    if "weekend" in preferences.lower():
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF DOW CONTAINS SA,SU"
        ])
    
    if "red-eye" in preferences.lower() or "redeye" in preferences.lower():
        pbs_layers.extend([
            "AVOID PAIRINGS",
            "  IF REPORT < 0600"
        ])
    
    if "SAN" in preferences.upper():
        pbs_layers.extend([
            "PREFER PAIRINGS",
            "  IF LAYOVER CITY = 'SAN'"
        ])
    
    if not pbs_layers:
        pbs_layers = [
            "AWARD PAIRINGS",
            "  IN SENIORITY ORDER"
        ]
    
    results = {
        "pbs_layers": pbs_layers,
        "airline": airline,
        "base": base,
        "preferences": preferences
    }
    return templates.TemplateResponse("results.html", {"request": request, "results": results})
"""

with open("app/routes/ui.py", "w") as f:
    f.write(ui_code)

print("✅ UI enhanced with smarter PBS generation!")
