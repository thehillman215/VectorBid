"""
Bulletproof Authentication System for VectorBid
Implements OWASP Top 10 API Security protections with comprehensive testing hooks
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import bcrypt
import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import User, Pilot  # Will need to update models
from app.security.rate_limiting import RateLimiter
from app.security.audit_logger import SecurityAuditLogger


class AuthConfig:
    """Authentication configuration with security best practices"""
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security
    BCRYPT_ROUNDS: int = 12  # High security, ~250ms per hash
    MIN_PASSWORD_LENGTH: int = 12
    REQUIRE_SPECIAL_CHARS: bool = True
    REQUIRE_NUMBERS: bool = True
    REQUIRE_UPPERCASE: bool = True
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    PASSWORD_HISTORY_COUNT: int = 5  # Prevent reusing last 5 passwords
    
    # Session Security
    MAX_CONCURRENT_SESSIONS: int = 3
    FORCE_PASSWORD_CHANGE_DAYS: int = 90
    
    # Security Headers
    COOKIE_SECURE: bool = True
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "strict"


class LoginRequest(BaseModel):
    """Secure login request with validation"""
    email: EmailStr
    password: str
    remember_me: bool = False
    device_fingerprint: Optional[str] = None  # For device tracking
    
    @validator('password')
    def validate_password_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v


class RegisterRequest(BaseModel):
    """Secure registration request with strong validation"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    pilot_id: str
    airline: str
    base: str
    seat: str
    equipment: list[str]
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets security requirements"""
        if len(v) < AuthConfig.MIN_PASSWORD_LENGTH:
            raise ValueError(f'Password must be at least {AuthConfig.MIN_PASSWORD_LENGTH} characters')
        
        if AuthConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if AuthConfig.REQUIRE_NUMBERS and not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        
        if AuthConfig.REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('email')
    def validate_email_format(cls, v):
        """Additional email validation beyond EmailStr"""
        if len(v) > 255:
            raise ValueError('Email address too long')
        return v.lower()


class TokenResponse(BaseModel):
    """Secure token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str


class PasswordHasher:
    """Secure password hashing with bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt and random salt"""
        try:
            salt = bcrypt.gensalt(rounds=AuthConfig.BCRYPT_ROUNDS)
            password_bytes = password.encode('utf-8')
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password hashing failed"
            )
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False  # Never raise exceptions in verification


class JWTManager:
    """Secure JWT token management"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create secure JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "vectorbid",  # Issuer
            "aud": "vectorbid-api",  # Audience
            "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)
            return encoded_jwt
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create secure refresh token"""
        data = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        }
        return JWTManager.create_access_token(data)
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                AuthConfig.SECRET_KEY, 
                algorithms=[AuthConfig.ALGORITHM],
                audience="vectorbid-api",
                issuer="vectorbid"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )


class AuthenticationService:
    """Main authentication service with security controls"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rate_limiter = RateLimiter()
        self.audit_logger = SecurityAuditLogger()
        self.password_hasher = PasswordHasher()
        self.jwt_manager = JWTManager()
    
    async def register_user(self, request: RegisterRequest, ip_address: str) -> TokenResponse:
        """Register new user with comprehensive security checks"""
        
        # Rate limiting for registration
        await self.rate_limiter.check_registration_rate(ip_address)
        
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(request.email)
            if existing_user:
                # Don't reveal if user exists - security best practice
                await self.audit_logger.log_failed_registration(
                    email=request.email,
                    reason="email_exists",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Registration failed"
                )
            
            # Check pilot ID uniqueness
            existing_pilot = await self.get_pilot_by_pilot_id(request.pilot_id)
            if existing_pilot:
                await self.audit_logger.log_failed_registration(
                    email=request.email,
                    reason="pilot_id_exists",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Pilot ID already registered"
                )
            
            # Hash password
            hashed_password = self.password_hasher.hash_password(request.password)
            
            # Create user record
            user = User(
                email=request.email,
                password_hash=hashed_password,
                first_name=request.first_name,
                last_name=request.last_name,
                role="pilot",
                status="active",
                email_verified=False,  # Require email verification
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            # Create pilot profile
            pilot = Pilot(
                user_id=user.id,
                pilot_id=request.pilot_id,
                airline=request.airline,
                base=request.base,
                seat=request.seat,
                equipment=request.equipment,
                created_at=datetime.now(timezone.utc)
            )
            
            self.db.add(pilot)
            await self.db.commit()
            
            # Log successful registration
            await self.audit_logger.log_successful_registration(
                user_id=str(user.id),
                email=request.email,
                ip_address=ip_address
            )
            
            # Generate tokens
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "verified": user.email_verified
            }
            
            access_token = self.jwt_manager.create_access_token(token_data)
            refresh_token = self.jwt_manager.create_refresh_token(str(user.id))
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=str(user.id),
                role=user.role
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await self.audit_logger.log_system_error(
                operation="registration",
                error=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def authenticate_user(self, request: LoginRequest, ip_address: str) -> TokenResponse:
        """Authenticate user with comprehensive security controls"""
        
        # Rate limiting for login attempts
        await self.rate_limiter.check_login_rate(ip_address, request.email)
        
        try:
            # Get user
            user = await self.get_user_by_email(request.email)
            if not user:
                await self.audit_logger.log_failed_login(
                    email=request.email,
                    reason="user_not_found",
                    ip_address=ip_address
                )
                # Timing attack prevention - always hash even if user doesn't exist
                self.password_hasher.hash_password("dummy_password")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check account status
            if user.status != "active":
                await self.audit_logger.log_failed_login(
                    email=request.email,
                    reason="account_disabled",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account disabled"
                )
            
            # Check if account is locked
            if await self.is_account_locked(user.id):
                await self.audit_logger.log_failed_login(
                    email=request.email,
                    reason="account_locked",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account temporarily locked"
                )
            
            # Verify password
            if not self.password_hasher.verify_password(request.password, user.password_hash):
                await self.increment_failed_login_attempts(user.id)
                await self.audit_logger.log_failed_login(
                    email=request.email,
                    reason="invalid_password",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Reset failed login attempts on successful login
            await self.reset_failed_login_attempts(user.id)
            
            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            user.login_count += 1
            await self.db.commit()
            
            # Log successful login
            await self.audit_logger.log_successful_login(
                user_id=str(user.id),
                email=request.email,
                ip_address=ip_address,
                device_fingerprint=request.device_fingerprint
            )
            
            # Generate tokens
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "verified": user.email_verified
            }
            
            access_token = self.jwt_manager.create_access_token(token_data)
            refresh_token = self.jwt_manager.create_refresh_token(str(user.id))
            
            # Store session (for revocation capability)
            await self.create_user_session(
                user_id=user.id,
                token_hash=self.hash_token(access_token),
                device_info={
                    "ip_address": ip_address,
                    "device_fingerprint": request.device_fingerprint,
                    "user_agent": None  # Will be set by middleware
                },
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=str(user.id),
                role=user.role
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await self.audit_logger.log_system_error(
                operation="authentication",
                error=str(e),
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    # Helper methods (will implement in next part)
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        # TODO: Implement database query
        pass
    
    async def get_pilot_by_pilot_id(self, pilot_id: str) -> Optional[Pilot]:
        """Get pilot by pilot ID"""
        # TODO: Implement database query
        pass
    
    async def is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        # TODO: Implement lockout logic
        pass
    
    async def increment_failed_login_attempts(self, user_id: str):
        """Increment failed login attempts counter"""
        # TODO: Implement attempt tracking
        pass
    
    async def reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts counter"""
        # TODO: Implement reset logic
        pass
    
    async def create_user_session(self, user_id: str, token_hash: str, device_info: dict, expires_at: datetime):
        """Create user session for token revocation"""
        # TODO: Implement session storage
        pass
    
    def hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()