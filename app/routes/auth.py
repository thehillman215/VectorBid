"""
Authentication API routes for VectorBid
Handles user registration, login, token refresh, and logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from pydantic import BaseModel, EmailStr
import secrets
from datetime import datetime, timedelta, timezone
import jwt


router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# Simple models for authentication
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    airline: str
    base: str
    seat: str
    fleet: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str

# Simple JWT configuration
JWT_SECRET = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Register a new pilot account"""
    try:
        # Simple registration for now - create mock success response
        # In production, this would validate and store the user
        
        # Generate a simple pilot_id from email
        pilot_id = request.email.split('@')[0] + '_' + request.airline.lower()
        
        # Generate tokens (for demo purposes)
        token_data = {
            "sub": pilot_id,
            "email": request.email,
            "role": "pilot",
            "verified": False
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_access_token({"sub": pilot_id, "type": "refresh"})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user_id=pilot_id,
            role="pilot"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_session)
):
    """Authenticate user and return JWT tokens"""
    try:
        # Simple login for now - accept any email/password combo
        # In production, this would validate against database
        
        # Generate pilot_id from email
        pilot_id = request.email.split('@')[0] + '_pilot'
        
        # Generate tokens
        token_data = {
            "sub": pilot_id,
            "email": request.email,
            "role": "pilot",
            "verified": True
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_access_token({"sub": pilot_id, "type": "refresh"})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user_id=pilot_id,
            role="pilot"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
):
    """Refresh access token using refresh token"""
    try:
        # Verify the refresh token
        payload = verify_token(credentials.credentials)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # TODO: Verify user still exists and is active
        # For now, generate new tokens
        token_data = {
            "sub": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "pilot"),
            "verified": payload.get("verified", False)
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_access_token({"sub": user_id, "type": "refresh"})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user_id=user_id,
            role=payload.get("role", "pilot")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
):
    """Logout user and revoke token"""
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        
        # TODO: Add token to revocation list in database
        # For now, just return success
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
):
    """Get current user information"""
    try:
        # Verify the token
        payload = verify_token(credentials.credentials)
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # TODO: Fetch full user details from database
        # For now, return payload data
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "verified": payload.get("verified")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.get("/verify/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_session)):
    """Verify user email address"""
    # TODO: Implement email verification
    return {"message": "Email verification not implemented yet"}


@router.post("/forgot-password")
async def forgot_password(email: str, db: AsyncSession = Depends(get_session)):
    """Request password reset"""
    # TODO: Implement password reset
    return {"message": "Password reset not implemented yet"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_session)
):
    """Reset password using token"""
    # TODO: Implement password reset
    return {"message": "Password reset not implemented yet"}