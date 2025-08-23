"""
Authentication Dependencies

FastAPI dependencies for route protection and role-based access control.
"""

import logging
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# JWT settings (in production, use environment variables)
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token and return current user.
    
    Args:
        credentials: Bearer token from request header
    
    Returns:
        User information from token
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_id,
            "email": email,
            "role": role or "pilot",
        }
        
    except PyJWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin_role(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require admin role for access.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information if admin
    
    Raises:
        HTTPException: If user is not an admin
    """
    
    if current_user.get("role") != "admin":
        logger.warning(
            f"Non-admin user {current_user.get('email')} attempted to access admin route"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


async def require_pilot_role(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require pilot role for access.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information if pilot or admin
    
    Raises:
        HTTPException: If user lacks appropriate role
    """
    
    role = current_user.get("role")
    if role not in ["pilot", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pilot access required",
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    
    Args:
        credentials: Optional bearer token
    
    Returns:
        User information or None
    """
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None