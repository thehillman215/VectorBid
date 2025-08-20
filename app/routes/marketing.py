# app/routes/marketing.py
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/")
async def serve_landing_page():
    """Serve the professional marketing landing page"""
    landing_path = Path(__file__).parent.parent / "static" / "pages" / "landing" / "home.html"
    if landing_path.exists():
        return FileResponse(landing_path)
    # Fallback to current SPA during development
    spa_path = Path(__file__).parent.parent / "static" / "index.html"
    if spa_path.exists():
        return FileResponse(spa_path)
    return {"message": "Landing page not found"}

@router.get("/company/about")
async def serve_about_page():
    """About page"""
    about_path = Path(__file__).parent.parent / "static" / "pages" / "company" / "about.html"
    if about_path.exists():
        return FileResponse(about_path)
    return {"message": "About page coming soon"}

@router.get("/company/security")  
async def serve_security_page():
    """Security page"""
    security_path = Path(__file__).parent.parent / "static" / "pages" / "company" / "security.html"
    if security_path.exists():
        return FileResponse(security_path)
    return {"message": "Security page coming soon"}

@router.get("/pricing")
async def serve_pricing_page():
    """Pricing page"""
    pricing_path = Path(__file__).parent.parent / "static" / "pages" / "pricing.html"
    if pricing_path.exists():
        return FileResponse(pricing_path)
    return {"message": "Pricing page coming soon"}

@router.get("/demo")
async def serve_demo_page():
    """Interactive demo page"""
    demo_path = Path(__file__).parent.parent / "static" / "pages" / "demo" / "index.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    # Fallback to current SPA for demo functionality
    spa_path = Path(__file__).parent.parent / "static" / "index.html"
    if spa_path.exists():
        return FileResponse(spa_path)
    return {"message": "Demo page not found"}