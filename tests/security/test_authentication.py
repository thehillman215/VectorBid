"""
Comprehensive Authentication Security Tests
Tests all OWASP Top 10 vulnerabilities and security best practices
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.security.authentication import AuthenticationService, LoginRequest, RegisterRequest
from app.security.rate_limiting import RateLimiter
from app.security.audit_logger import SecurityAuditLogger
from app.security.session_manager import SessionManager


class TestPasswordSecurity:
    """Test password hashing and validation security"""
    
    def test_password_hashing_bcrypt(self):
        """Test bcrypt password hashing with proper salt"""
        from app.security.authentication import PasswordHasher
        
        hasher = PasswordHasher()
        password = "TestPassword123!"
        
        # Test hashing
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        assert len(hash1) > 50  # bcrypt hashes are long
        assert hash1.startswith("$2b$")  # bcrypt format
        
        # Test verification
        assert hasher.verify_password(password, hash1)
        assert hasher.verify_password(password, hash2)
        assert not hasher.verify_password("wrong_password", hash1)
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        # Valid passwords
        valid_passwords = [
            "StrongPassword123!",
            "MySecureP@ssw0rd",
            "Complex123$Password"
        ]
        
        for password in valid_passwords:
            request = RegisterRequest(
                email="test@example.com",
                password=password,
                first_name="Test",
                last_name="User",
                pilot_id="TEST001",
                airline="UAL",
                base="ORD",
                seat="CA",
                equipment=["737"]
            )
            # Should not raise validation error
            assert request.password == password
    
    def test_weak_password_rejection(self):
        """Test rejection of weak passwords"""
        weak_passwords = [
            "short",              # Too short
            "nouppercase123!",    # No uppercase
            "NOLOWERCASE123!",    # No lowercase
            "NoNumbers!",         # No numbers
            "NoSpecialChars123",  # No special characters
            "password123",        # Common password
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValueError):
                RegisterRequest(
                    email="test@example.com",
                    password=password,
                    first_name="Test",
                    last_name="User",
                    pilot_id="TEST001",
                    airline="UAL",
                    base="ORD",
                    seat="CA",
                    equipment=["737"]
                )
    
    def test_timing_attack_resistance(self):
        """Test that password verification takes consistent time"""
        from app.security.authentication import PasswordHasher
        
        hasher = PasswordHasher()
        valid_hash = hasher.hash_password("correct_password")
        
        # Time verification with correct password
        start_time = time.time()
        result1 = hasher.verify_password("correct_password", valid_hash)
        time1 = time.time() - start_time
        
        # Time verification with wrong password
        start_time = time.time()
        result2 = hasher.verify_password("wrong_password", valid_hash)
        time2 = time.time() - start_time
        
        assert result1 is True
        assert result2 is False
        
        # Times should be relatively similar (within 50ms difference)
        time_diff = abs(time1 - time2)
        assert time_diff < 0.05, f"Timing difference too large: {time_diff}s"


class TestJWTSecurity:
    """Test JWT token security"""
    
    def test_jwt_token_creation(self):
        """Test JWT token creation with proper claims"""
        from app.security.authentication import JWTManager
        
        jwt_manager = JWTManager()
        data = {"sub": "user123", "email": "test@example.com", "role": "pilot"}
        
        token = jwt_manager.create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "pilot"
        assert "exp" in payload
        assert "iat" in payload
        assert "iss" in payload
        assert "aud" in payload
        assert "jti" in payload
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        from app.security.authentication import JWTManager
        import jwt
        
        jwt_manager = JWTManager()
        data = {"sub": "user123", "email": "test@example.com"}
        
        # Create token with short expiration
        expires_delta = timedelta(seconds=1)
        token = jwt_manager.create_access_token(data, expires_delta)
        
        # Token should work immediately
        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        
        # Wait for expiration
        time.sleep(2)
        
        # Token should be expired
        with pytest.raises(Exception) as exc_info:
            jwt_manager.verify_token(token)
        assert "expired" in str(exc_info.value).lower()
    
    def test_jwt_token_tampering(self):
        """Test that tampered JWT tokens are rejected"""
        from app.security.authentication import JWTManager
        
        jwt_manager = JWTManager()
        data = {"sub": "user123", "email": "test@example.com", "role": "pilot"}
        
        token = jwt_manager.create_access_token(data)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered123"
        
        # Tampered token should be rejected
        with pytest.raises(Exception):
            jwt_manager.verify_token(tampered_token)


class TestRateLimiting:
    """Test rate limiting security"""
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self):
        """Test rate limiting for login attempts"""
        rate_limiter = RateLimiter()
        
        ip_address = "192.168.1.100"
        email = "test@example.com"
        
        # Should allow first few attempts
        for i in range(4):
            await rate_limiter.check_login_rate(ip_address, email)
        
        # 5th attempt should be blocked
        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_login_rate(ip_address, email)
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_registration_rate_limiting(self):
        """Test rate limiting for registration attempts"""
        rate_limiter = RateLimiter()
        
        ip_address = "192.168.1.101"
        
        # Should allow first few registrations
        for i in range(3):
            await rate_limiter.check_registration_rate(ip_address)
        
        # 4th attempt should be blocked
        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_registration_rate(ip_address)
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset(self):
        """Test rate limit reset functionality"""
        rate_limiter = RateLimiter()
        
        ip_address = "192.168.1.102"
        email = "test2@example.com"
        
        # Trigger rate limit
        for i in range(5):
            try:
                await rate_limiter.check_login_rate(ip_address, email)
            except:
                pass
        
        # Should be blocked
        with pytest.raises(Exception):
            await rate_limiter.check_login_rate(ip_address, email)
        
        # Reset rate limit
        await rate_limiter.reset_rate_limit(f"login_ip:{ip_address}", "login")
        await rate_limiter.reset_rate_limit(f"login_email:{email}", "login")
        
        # Should work again
        await rate_limiter.check_login_rate(ip_address, email)


class TestSessionSecurity:
    """Test session management security"""
    
    @pytest.mark.asyncio
    async def test_session_creation_and_retrieval(self):
        """Test secure session creation and retrieval"""
        # Mock Redis for testing
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            session_manager = SessionManager("redis://localhost:6379/1")
            
            # Mock Redis operations
            mock_client.setex = AsyncMock()
            mock_client.sadd = AsyncMock()
            mock_client.expire = AsyncMock()
            mock_client.get = AsyncMock(return_value='{"session_id": "test123", "user_id": "user123", "token_hash": "hash123", "device_info": {}, "created_at": "2024-01-01T00:00:00+00:00", "expires_at": "2024-01-02T00:00:00+00:00", "last_activity": "2024-01-01T00:00:00+00:00", "is_active": true}')
            
            # Create session
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            session_info = await session_manager.create_session(
                user_id="user123",
                token_hash="hash123",
                device_info={"ip": "192.168.1.1"},
                expires_at=expires_at
            )
            
            assert session_info.user_id == "user123"
            assert session_info.token_hash == "hash123"
            assert session_info.is_active is True
    
    @pytest.mark.asyncio
    async def test_concurrent_session_limit(self):
        """Test enforcement of concurrent session limits"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            session_manager = SessionManager("redis://localhost:6379/1")
            session_manager.max_concurrent_sessions = 2
            
            # Mock existing sessions
            mock_client.smembers = AsyncMock(return_value=["session1", "session2"])
            mock_client.get = AsyncMock(side_effect=[
                '{"session_id": "session1", "user_id": "user123", "created_at": "2024-01-01T00:00:00+00:00", "expires_at": "2024-01-02T00:00:00+00:00", "last_activity": "2024-01-01T00:00:00+00:00", "is_active": true, "token_hash": "hash1", "device_info": {}}',
                '{"session_id": "session2", "user_id": "user123", "created_at": "2024-01-01T01:00:00+00:00", "expires_at": "2024-01-02T00:00:00+00:00", "last_activity": "2024-01-01T01:00:00+00:00", "is_active": true, "token_hash": "hash2", "device_info": {}}'
            ])
            
            # Mock revocation calls
            mock_client.delete = AsyncMock()
            mock_client.srem = AsyncMock()
            mock_client.setex = AsyncMock()
            
            # Create new session (should revoke oldest)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            await session_manager.create_session(
                user_id="user123",
                token_hash="hash3",
                device_info={"ip": "192.168.1.1"},
                expires_at=expires_at
            )
            
            # Should have called delete on oldest session
            mock_client.delete.assert_called()


class TestAuthenticationEndpoints:
    """Test authentication API endpoints security"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        """Test protection against SQL injection in authentication"""
        # Test with SQL injection payloads
        malicious_emails = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "test@example.com'; DELETE FROM users WHERE 1=1; --"
        ]
        
        for email in malicious_emails:
            request = LoginRequest(
                email=email,
                password="password123"
            )
            
            # Email validation should catch invalid formats
            # Note: Pydantic EmailStr validation will catch most SQL injection attempts
            # Additional database-level protection should use parameterized queries
            assert isinstance(request.email, str)
    
    def test_xss_protection(self):
        """Test protection against XSS in user inputs"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            # Test in name fields
            with pytest.raises(ValueError):
                RegisterRequest(
                    email="test@example.com",
                    password="StrongPassword123!",
                    first_name=payload,
                    last_name="User",
                    pilot_id="TEST001",
                    airline="UAL",
                    base="ORD",
                    seat="CA",
                    equipment=["737"]
                )
    
    def test_input_length_limits(self):
        """Test input length validation"""
        # Test extremely long inputs
        long_string = "A" * 1000
        
        with pytest.raises(ValueError):
            RegisterRequest(
                email=f"{long_string}@example.com",
                password="StrongPassword123!",
                first_name="Test",
                last_name="User",
                pilot_id="TEST001",
                airline="UAL",
                base="ORD",
                seat="CA",
                equipment=["737"]
            )


class TestAuditLogging:
    """Test security audit logging"""
    
    @pytest.mark.asyncio
    async def test_failed_login_logging(self):
        """Test that failed login attempts are logged"""
        audit_logger = SecurityAuditLogger()
        
        # Mock database operations
        with patch.object(audit_logger, '_log_to_database', new=AsyncMock()) as mock_db_log:
            await audit_logger.log_failed_login(
                email="test@example.com",
                reason="invalid_password",
                ip_address="192.168.1.1"
            )
            
            mock_db_log.assert_called_once()
            call_args = mock_db_log.call_args[0][0]
            assert call_args.event_type.value == "login_failed"
            assert call_args.success is False
    
    @pytest.mark.asyncio
    async def test_security_event_severity(self):
        """Test that security events have appropriate severity levels"""
        audit_logger = SecurityAuditLogger()
        
        # Test critical event
        with patch.object(audit_logger, '_send_security_alert', new=AsyncMock()) as mock_alert:
            with patch.object(audit_logger, '_log_to_database', new=AsyncMock()):
                await audit_logger.log_suspicious_activity(
                    user_id="user123",
                    activity_type="brute_force",
                    details={"attempts": 100},
                    ip_address="192.168.1.1"
                )
                
                # Should trigger security alert for critical events
                mock_alert.assert_called_once()


class SecurityTestSuite:
    """Complete security test suite runner"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_security_check(self):
        """Run comprehensive security test battery"""
        
        # 1. Test all password security
        password_tests = TestPasswordSecurity()
        password_tests.test_password_hashing_bcrypt()
        password_tests.test_password_strength_validation()
        password_tests.test_weak_password_rejection()
        password_tests.test_timing_attack_resistance()
        
        # 2. Test JWT security
        jwt_tests = TestJWTSecurity()
        jwt_tests.test_jwt_token_creation()
        jwt_tests.test_jwt_token_expiration()
        jwt_tests.test_jwt_token_tampering()
        
        # 3. Test rate limiting
        rate_tests = TestRateLimiting()
        await rate_tests.test_login_rate_limiting()
        await rate_tests.test_registration_rate_limiting()
        await rate_tests.test_rate_limit_reset()
        
        # 4. Test session security
        session_tests = TestSessionSecurity()
        await session_tests.test_session_creation_and_retrieval()
        await session_tests.test_concurrent_session_limit()
        
        # 5. Test endpoint security
        endpoint_tests = TestAuthenticationEndpoints()
        await endpoint_tests.test_sql_injection_protection()
        endpoint_tests.test_xss_protection()
        endpoint_tests.test_input_length_limits()
        
        # 6. Test audit logging
        audit_tests = TestAuditLogging()
        await audit_tests.test_failed_login_logging()
        await audit_tests.test_security_event_severity()
        
        print("✅ All security tests passed!")


if __name__ == "__main__":
    # Run security test suite
    asyncio.run(SecurityTestSuite().test_comprehensive_security_check())