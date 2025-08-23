from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")


# Root route moved to main.py to serve professional landing page
# @router.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Serve the bid package upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


# Essential User Journey Routes
@router.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """User registration page"""
    signup_path = Path(__file__).parent.parent / "static" / "pages" / "auth" / "signup.html"
    if signup_path.exists():
        return FileResponse(signup_path)
    return {"message": "Signup page not found"}


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """User login page"""
    login_path = Path(__file__).parent.parent / "static" / "pages" / "auth" / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"message": "Login page not found"}


@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    """Guided user onboarding"""
    onboarding_path = Path(__file__).parent.parent / "static" / "pages" / "onboarding.html"
    if onboarding_path.exists():
        return FileResponse(onboarding_path)
    return {"message": "Onboarding page not found"}


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """User dashboard"""
    dashboard_path = Path(__file__).parent.parent / "static" / "pages" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"message": "Dashboard page not found"}


# Keep the demo for authenticated users
@router.get("/demo", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Technical demo (moved from root)"""
    demo_path = Path(__file__).parent.parent / "static" / "index.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/test-llm", response_class=HTMLResponse)
async def test_llm_ui():
    """Test interface for LLM and scoring features"""
    test_path = Path(__file__).parent.parent / "static" / "test_llm_ui.html"
    if test_path.exists():
        return FileResponse(test_path)
    return HTMLResponse("<h1>Test UI not found</h1>", status_code=404)


@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(request: Request, preferences: str = Form(...)):
    pbs_layers = [
        "AVOID PAIRINGS",
        "  IF REPORT < 0800",
        "PREFER PAIRINGS",
        "  IF LAYOVER CITY = 'SAN'",
    ]
    results = {"pbs_layers": pbs_layers}
    return templates.TemplateResponse("results.html", {"request": request, "results": results})
