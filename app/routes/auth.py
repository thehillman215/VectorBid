# app/routes/auth.py
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import User

router = APIRouter()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    airline: str
    base: str
    seat: str
    equipment: list[str] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    airline: str
    base: str
    seat: str
    subscription_tier: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Password utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, "your-secret-key", algorithm="HS256")

# Page routes
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

# API endpoints
@router.post("/api/signup", response_model=Token)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Create new user account"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    
    new_user = User(
        id=user_id,
        email=user_data.email,
        hashed_password=hashed_pw,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        airline=user_data.airline,
        base=user_data.base,
        seat=user_data.seat,
        equipment=user_data.equipment,
        created_at=datetime.utcnow(),
        is_active=True,
        subscription_tier="free"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/dashboard")
async def serve_dashboard_page():
    """Dashboard page"""
    dashboard_path = Path(__file__).parent.parent / "static" / "pages" / "dashboard" / "index.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return {"message": "Dashboard coming soon"}

@router.get("/api/me", response_model=UserResponse)
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user profile"""
    # For demo purposes, return a sample user
    # In production, this would extract user from JWT token
    return UserResponse(
        id="demo-user-id",
        email="demo@example.com",
        first_name="Demo",
        last_name="User",
        airline="UAL",
        base="SFO",
        seat="CA",
        subscription_tier="free"
    )