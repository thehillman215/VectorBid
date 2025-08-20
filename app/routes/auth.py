# app/routes/auth.py
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/signup")
async def serve_signup_page():
    """Signup page"""
    signup_path = Path(__file__).parent.parent / "static" / "pages" / "auth" / "signup.html"
    if signup_path.exists():
        return FileResponse(signup_path)
    return {"message": "Signup page coming soon"}

@router.get("/login")
async def serve_login_page():
    """Login page"""
    login_path = Path(__file__).parent.parent / "static" / "pages" / "auth" / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"message": "Login page coming soon"}