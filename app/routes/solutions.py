# app/routes/solutions.py
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/")
async def serve_solutions_page():
    """Solutions overview page"""
    solutions_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "index.html"
    if solutions_path.exists():
        return FileResponse(solutions_path)
    return {"message": "Solutions page coming soon"}

@router.get("/regional")
async def serve_regional_page():
    """Regional Airlines solution page"""
    regional_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "regional.html"
    if regional_path.exists():
        return FileResponse(regional_path)
    return {"message": "Regional Airlines page coming soon"}

@router.get("/major")
async def serve_major_page():
    """Major Airlines solution page"""
    major_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "major.html"
    if major_path.exists():
        return FileResponse(major_path)
    return {"message": "Major Airlines page coming soon"}

@router.get("/corporate")
async def serve_corporate_page():
    """Corporate Aviation solution page"""
    corporate_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "corporate.html"
    if corporate_path.exists():
        return FileResponse(corporate_path)
    return {"message": "Corporate Aviation page coming soon"}

@router.get("/first-officers")
async def serve_first_officers_page():
    """First Officers solution page"""
    first_officers_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "first-officers.html"
    if first_officers_path.exists():
        return FileResponse(first_officers_path)
    return {"message": "First Officers page coming soon"}

@router.get("/captains")
async def serve_captains_page():
    """Captains solution page"""
    captains_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "captains.html"
    if captains_path.exists():
        return FileResponse(captains_path)
    return {"message": "Captains page coming soon"}

@router.get("/commuters")
async def serve_commuters_page():
    """Commuter Pilots solution page"""
    commuters_path = Path(__file__).parent.parent / "static" / "pages" / "solutions" / "commuters.html"
    if commuters_path.exists():
        return FileResponse(commuters_path)
    return {"message": "Commuter Pilots page coming soon"}