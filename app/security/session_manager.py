"""
Session Management with Redis Backend
Handles JWT token lifecycle, revocation, and concurrent session limits
"""
import json
import time
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

import redis.asyncio as redis
from fastapi import HTTPException, status


@dataclass
class SessionInfo:
    """Session information structure"""
    session_id: str
    user_id: str
    token_hash: str
    device_info: Dict[str, any]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool = True


class SessionManager:
    """Redis-backed session management with security controls"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize session manager with Redis backend"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Session manager initialization failed: {e}"
            )
        
        # Session configuration
        self.max_concurrent_sessions = 3
        self.session_timeout_hours = 24
        self.activity_update_interval = 300  # Update activity every 5 minutes
        
        # Redis key prefixes
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.token_blacklist_prefix = "blacklist:"
        self.activity_prefix = "activity:"
    
    async def create_session(self, user_id: str, token_hash: str, 
                           device_info: Dict[str, any], 
                           expires_at: datetime) -> SessionInfo:
        """Create new user session with concurrent session limit enforcement"""
        try:
            session_id = self._generate_session_id()
            current_time = datetime.now(timezone.utc)
            
            # Check concurrent session limit
            await self._enforce_session_limit(user_id)
            
            # Create session info
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                token_hash=token_hash,
                device_info=device_info,
                created_at=current_time,
                expires_at=expires_at,
                last_activity=current_time,
                is_active=True
            )
            
            # Store session in Redis
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self._serialize_session(session_info)
            
            # Calculate TTL based on expiration
            ttl_seconds = int((expires_at - current_time).total_seconds())
            
            await self.redis_client.setex(session_key, ttl_seconds, session_data)
            
            # Add to user's session list
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            await self.redis_client.sadd(user_sessions_key, session_id)
            await self.redis_client.expire(user_sessions_key, ttl_seconds)
            
            # Store token hash for revocation checking
            token_key = f"token:{token_hash}"
            await self.redis_client.setex(token_key, ttl_seconds, session_id)
            
            return session_info
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Session creation failed: {e}"
            )
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session by session ID"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = await self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            session_info = self._deserialize_session(session_data)
            
            # Check if session is expired
            if session_info.expires_at < datetime.now(timezone.utc):
                await self.revoke_session(session_id)
                return None
            
            return session_info
            
        except Exception as e:
            print(f"Session retrieval failed: {e}")
            return None
    
    async def get_session_by_token(self, token_hash: str) -> Optional[SessionInfo]:
        """Get session by token hash"""
        try:
            # Check if token is blacklisted
            if await self.is_token_blacklisted(token_hash):
                return None
            
            # Get session ID from token hash
            token_key = f"token:{token_hash}"
            session_id = await self.redis_client.get(token_key)
            
            if not session_id:
                return None
            
            return await self.get_session(session_id)
            
        except Exception as e:
            print(f"Session retrieval by token failed: {e}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update last activity time for session"""
        try:
            session_info = await self.get_session(session_id)
            if not session_info:
                return False
            
            current_time = datetime.now(timezone.utc)
            
            # Only update if significant time has passed (rate limiting)
            time_diff = (current_time - session_info.last_activity).total_seconds()
            if time_diff < self.activity_update_interval:
                return True
            
            # Update session
            session_info.last_activity = current_time
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self._serialize_session(session_info)
            
            # Preserve original TTL
            ttl = await self.redis_client.ttl(session_key)
            if ttl > 0:
                await self.redis_client.setex(session_key, ttl, session_data)
            
            return True
            
        except Exception as e:
            print(f"Session activity update failed: {e}")
            return False
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session"""
        try:
            # Get session info before deletion
            session_info = await self.get_session(session_id)
            if not session_info:
                return False
            
            # Remove session
            session_key = f"{self.session_prefix}{session_id}"
            await self.redis_client.delete(session_key)
            
            # Remove from user's session list
            user_sessions_key = f"{self.user_sessions_prefix}{session_info.user_id}"
            await self.redis_client.srem(user_sessions_key, session_id)
            
            # Blacklist the token
            await self.blacklist_token(session_info.token_hash)
            
            # Remove token mapping
            token_key = f"token:{session_info.token_hash}"
            await self.redis_client.delete(token_key)
            
            return True
            
        except Exception as e:
            print(f"Session revocation failed: {e}")
            return False
    
    async def revoke_user_sessions(self, user_id: str, except_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user (except optionally one)"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = await self.redis_client.smembers(user_sessions_key)
            
            revoked_count = 0
            for session_id in session_ids:
                if except_session_id and session_id == except_session_id:
                    continue
                
                if await self.revoke_session(session_id):
                    revoked_count += 1
            
            return revoked_count
            
        except Exception as e:
            print(f"User session revocation failed: {e}")
            return 0
    
    async def blacklist_token(self, token_hash: str, ttl_seconds: int = 86400) -> bool:
        """Add token to blacklist (for logout/revocation)"""
        try:
            blacklist_key = f"{self.token_blacklist_prefix}{token_hash}"
            await self.redis_client.setex(blacklist_key, ttl_seconds, "revoked")
            return True
        except Exception as e:
            print(f"Token blacklisting failed: {e}")
            return False
    
    async def is_token_blacklisted(self, token_hash: str) -> bool:
        """Check if token is blacklisted"""
        try:
            blacklist_key = f"{self.token_blacklist_prefix}{token_hash}"
            result = await self.redis_client.get(blacklist_key)
            return result is not None
        except Exception as e:
            print(f"Token blacklist check failed: {e}")
            return False  # Fail open for availability
    
    async def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = await self.redis_client.smembers(user_sessions_key)
            
            sessions = []
            for session_id in session_ids:
                session_info = await self.get_session(session_id)
                if session_info and session_info.is_active:
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            print(f"User session retrieval failed: {e}")
            return []
    
    async def get_session_stats(self, user_id: str) -> Dict[str, any]:
        """Get session statistics for monitoring"""
        try:
            sessions = await self.get_user_sessions(user_id)
            current_time = datetime.now(timezone.utc)
            
            active_sessions = [s for s in sessions if s.is_active]
            recent_activity = [s for s in active_sessions 
                             if (current_time - s.last_activity).total_seconds() < 3600]
            
            return {
                "total_sessions": len(sessions),
                "active_sessions": len(active_sessions),
                "recent_activity_sessions": len(recent_activity),
                "oldest_session": min([s.created_at for s in sessions]) if sessions else None,
                "newest_session": max([s.created_at for s in sessions]) if sessions else None,
                "devices": list(set([s.device_info.get("user_agent", "unknown") for s in sessions]))
            }
            
        except Exception as e:
            print(f"Session stats retrieval failed: {e}")
            return {}
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (background task)"""
        try:
            cleanup_count = 0
            
            # Get all session keys
            session_pattern = f"{self.session_prefix}*"
            async for key in self.redis_client.scan_iter(match=session_pattern):
                session_data = await self.redis_client.get(key)
                if session_data:
                    try:
                        session_info = self._deserialize_session(session_data)
                        if session_info.expires_at < datetime.now(timezone.utc):
                            session_id = key.replace(self.session_prefix, "")
                            await self.revoke_session(session_id)
                            cleanup_count += 1
                    except Exception:
                        # Invalid session data, remove it
                        await self.redis_client.delete(key)
                        cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            print(f"Session cleanup failed: {e}")
            return 0
    
    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum concurrent sessions per user"""
        sessions = await self.get_user_sessions(user_id)
        active_sessions = [s for s in sessions if s.is_active]
        
        if len(active_sessions) >= self.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            await self.revoke_session(oldest_session.session_id)
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _serialize_session(self, session_info: SessionInfo) -> str:
        """Serialize session info for Redis storage"""
        data = asdict(session_info)
        # Convert datetime objects to ISO strings
        data["created_at"] = session_info.created_at.isoformat()
        data["expires_at"] = session_info.expires_at.isoformat()
        data["last_activity"] = session_info.last_activity.isoformat()
        return json.dumps(data)
    
    def _deserialize_session(self, session_data: str) -> SessionInfo:
        """Deserialize session info from Redis storage"""
        data = json.loads(session_data)
        # Convert ISO strings back to datetime objects
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        data["last_activity"] = datetime.fromisoformat(data["last_activity"])
        return SessionInfo(**data)
    
    def hash_token(self, token: str) -> str:
        """Create hash of JWT token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()


# Background cleanup task
async def session_cleanup_task(session_manager: SessionManager):
    """Background task to clean up expired sessions"""
    import asyncio
    
    while True:
        try:
            cleaned_count = await session_manager.cleanup_expired_sessions()
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} expired sessions")
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Session cleanup task error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes