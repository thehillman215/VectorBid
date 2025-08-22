"""
Rate Limiting for Authentication Security
Prevents brute force attacks and API abuse
"""
import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict, deque

from fastapi import HTTPException, status
import redis.asyncio as redis


@dataclass
class RateLimit:
    """Rate limit configuration"""
    max_attempts: int
    window_seconds: int
    lockout_seconds: int = 0


class RateLimiter:
    """Advanced rate limiter with Redis backend and memory fallback"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize rate limiter with optional Redis backend"""
        self.redis_client = None
        self.memory_store: Dict[str, deque] = defaultdict(deque)
        self.lockouts: Dict[str, float] = {}
        
        # Rate limit configurations
        self.limits = {
            "login": RateLimit(max_attempts=5, window_seconds=300, lockout_seconds=900),  # 5 attempts per 5min, 15min lockout
            "registration": RateLimit(max_attempts=3, window_seconds=3600),  # 3 registrations per hour
            "password_reset": RateLimit(max_attempts=3, window_seconds=1800),  # 3 resets per 30min
            "api_general": RateLimit(max_attempts=100, window_seconds=60),  # 100 requests per minute
            "contract_upload": RateLimit(max_attempts=10, window_seconds=3600),  # 10 uploads per hour
        }
        
        # Try to connect to Redis
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                print(f"Redis connection failed, using memory store: {e}")
    
    async def check_rate_limit(self, key: str, limit_type: str) -> None:
        """Check if request is within rate limit"""
        limit = self.limits.get(limit_type)
        if not limit:
            return  # No limit configured
        
        # Check if currently locked out
        if await self._is_locked_out(key, limit_type):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again later.",
                headers={"Retry-After": str(limit.lockout_seconds)}
            )
        
        # Check rate limit
        current_attempts = await self._get_attempts(key, limit_type, limit.window_seconds)
        
        if current_attempts >= limit.max_attempts:
            # Apply lockout if configured
            if limit.lockout_seconds > 0:
                await self._apply_lockout(key, limit_type, limit.lockout_seconds)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {limit.max_attempts} attempts per {limit.window_seconds} seconds.",
                headers={"Retry-After": str(limit.lockout_seconds or limit.window_seconds)}
            )
        
        # Record this attempt
        await self._record_attempt(key, limit_type)
    
    async def check_login_rate(self, ip_address: str, email: str) -> None:
        """Check rate limits for login attempts"""
        # Check both IP-based and email-based rate limits
        await self.check_rate_limit(f"login_ip:{ip_address}", "login")
        await self.check_rate_limit(f"login_email:{email}", "login")
    
    async def check_registration_rate(self, ip_address: str) -> None:
        """Check rate limits for registration attempts"""
        await self.check_rate_limit(f"registration:{ip_address}", "registration")
    
    async def check_password_reset_rate(self, email: str) -> None:
        """Check rate limits for password reset attempts"""
        await self.check_rate_limit(f"password_reset:{email}", "password_reset")
    
    async def check_api_rate(self, user_id: str) -> None:
        """Check general API rate limits"""
        await self.check_rate_limit(f"api:{user_id}", "api_general")
    
    async def check_contract_upload_rate(self, user_id: str) -> None:
        """Check contract upload rate limits"""
        await self.check_rate_limit(f"contract_upload:{user_id}", "contract_upload")
    
    async def _is_locked_out(self, key: str, limit_type: str) -> bool:
        """Check if key is currently locked out"""
        lockout_key = f"lockout:{limit_type}:{key}"
        
        if self.redis_client:
            try:
                lockout_until = await self.redis_client.get(lockout_key)
                if lockout_until:
                    return float(lockout_until) > time.time()
            except Exception:
                pass  # Fall back to memory store
        
        # Memory store fallback
        lockout_until = self.lockouts.get(lockout_key)
        if lockout_until:
            if lockout_until > time.time():
                return True
            else:
                # Lockout expired, clean up
                del self.lockouts[lockout_key]
        
        return False
    
    async def _apply_lockout(self, key: str, limit_type: str, lockout_seconds: int) -> None:
        """Apply lockout for specified duration"""
        lockout_key = f"lockout:{limit_type}:{key}"
        lockout_until = time.time() + lockout_seconds
        
        if self.redis_client:
            try:
                await self.redis_client.setex(lockout_key, lockout_seconds, str(lockout_until))
                return
            except Exception:
                pass  # Fall back to memory store
        
        # Memory store fallback
        self.lockouts[lockout_key] = lockout_until
    
    async def _get_attempts(self, key: str, limit_type: str, window_seconds: int) -> int:
        """Get number of attempts within the time window"""
        attempts_key = f"attempts:{limit_type}:{key}"
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if self.redis_client:
            try:
                # Use Redis sorted set for time-based counting
                await self.redis_client.zremrangebyscore(attempts_key, 0, window_start)
                count = await self.redis_client.zcard(attempts_key)
                return count
            except Exception:
                pass  # Fall back to memory store
        
        # Memory store fallback
        attempts = self.memory_store[attempts_key]
        
        # Remove old attempts
        while attempts and attempts[0] < window_start:
            attempts.popleft()
        
        return len(attempts)
    
    async def _record_attempt(self, key: str, limit_type: str) -> None:
        """Record an attempt with current timestamp"""
        attempts_key = f"attempts:{limit_type}:{key}"
        current_time = time.time()
        
        if self.redis_client:
            try:
                # Add to Redis sorted set with current timestamp as score
                await self.redis_client.zadd(attempts_key, {str(current_time): current_time})
                # Set expiration to prevent infinite growth
                limit = self.limits[limit_type]
                await self.redis_client.expire(attempts_key, limit.window_seconds * 2)
                return
            except Exception:
                pass  # Fall back to memory store
        
        # Memory store fallback
        attempts = self.memory_store[attempts_key]
        attempts.append(current_time)
        
        # Prevent memory growth
        if len(attempts) > 1000:
            attempts.popleft()
    
    async def reset_rate_limit(self, key: str, limit_type: str) -> None:
        """Reset rate limit for a key (e.g., after successful login)"""
        attempts_key = f"attempts:{limit_type}:{key}"
        lockout_key = f"lockout:{limit_type}:{key}"
        
        if self.redis_client:
            try:
                await self.redis_client.delete(attempts_key, lockout_key)
                return
            except Exception:
                pass
        
        # Memory store fallback
        if attempts_key in self.memory_store:
            del self.memory_store[attempts_key]
        if lockout_key in self.lockouts:
            del self.lockouts[lockout_key]
    
    async def get_rate_limit_info(self, key: str, limit_type: str) -> Dict[str, any]:
        """Get current rate limit status for debugging/monitoring"""
        limit = self.limits.get(limit_type)
        if not limit:
            return {"error": "Unknown limit type"}
        
        current_attempts = await self._get_attempts(key, limit_type, limit.window_seconds)
        is_locked = await self._is_locked_out(key, limit_type)
        
        return {
            "limit_type": limit_type,
            "max_attempts": limit.max_attempts,
            "window_seconds": limit.window_seconds,
            "current_attempts": current_attempts,
            "remaining_attempts": max(0, limit.max_attempts - current_attempts),
            "is_locked_out": is_locked,
            "lockout_seconds": limit.lockout_seconds if is_locked else 0
        }
    
    async def cleanup_expired_entries(self) -> None:
        """Clean up expired entries from memory store"""
        current_time = time.time()
        
        # Clean up attempts
        for key, attempts in list(self.memory_store.items()):
            if attempts and current_time - attempts[-1] > 86400:  # 24 hours
                del self.memory_store[key]
        
        # Clean up lockouts
        for key, lockout_until in list(self.lockouts.items()):
            if lockout_until < current_time:
                del self.lockouts[key]


# Background task for cleanup
async def rate_limiter_cleanup_task(rate_limiter: RateLimiter):
    """Background task to clean up expired rate limit entries"""
    while True:
        try:
            await rate_limiter.cleanup_expired_entries()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Rate limiter cleanup error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes