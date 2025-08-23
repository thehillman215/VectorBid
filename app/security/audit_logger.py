"""
Security Audit Logging System
Comprehensive logging for security events and compliance
"""
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session


class SecurityEventType(str, Enum):
    """Security event types for categorization"""
    
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTRATION_SUCCESS = "registration_success"
    REGISTRATION_FAILED = "registration_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_SUCCESS = "password_reset_success"
    EMAIL_VERIFICATION = "email_verification"
    
    # Authorization Events
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    ROLE_CHANGE = "role_change"
    
    # Session Events
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    CONCURRENT_SESSION_LIMIT = "concurrent_session_limit"
    
    # Data Access Events
    CONTRACT_UPLOAD = "contract_upload"
    CONTRACT_ACCESS = "contract_access"
    CONTRACT_MODIFICATION = "contract_modification"
    CONTRACT_DELETION = "contract_deletion"
    RULE_ACCESS = "rule_access"
    PILOT_DATA_ACCESS = "pilot_data_access"
    
    # Security Events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    
    # System Events
    SYSTEM_ERROR = "system_error"
    CONFIGURATION_CHANGE = "configuration_change"
    BACKUP_CREATED = "backup_created"
    MAINTENANCE_MODE = "maintenance_mode"


class SeverityLevel(str, Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: SecurityEventType
    severity: SeverityLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    success: bool
    timestamp: datetime
    session_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    error_message: Optional[str] = None


class SecurityAuditLogger:
    """Comprehensive security audit logging system"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        
        # Security event severity mapping
        self.severity_mapping = {
            SecurityEventType.LOGIN_SUCCESS: SeverityLevel.LOW,
            SecurityEventType.LOGIN_FAILED: SeverityLevel.MEDIUM,
            SecurityEventType.REGISTRATION_SUCCESS: SeverityLevel.LOW,
            SecurityEventType.REGISTRATION_FAILED: SeverityLevel.MEDIUM,
            SecurityEventType.PASSWORD_CHANGE: SeverityLevel.MEDIUM,
            SecurityEventType.ACCESS_DENIED: SeverityLevel.HIGH,
            SecurityEventType.RATE_LIMIT_EXCEEDED: SeverityLevel.HIGH,
            SecurityEventType.BRUTE_FORCE_ATTEMPT: SeverityLevel.CRITICAL,
            SecurityEventType.ACCOUNT_LOCKED: SeverityLevel.HIGH,
            SecurityEventType.SUSPICIOUS_ACTIVITY: SeverityLevel.CRITICAL,
            SecurityEventType.SYSTEM_ERROR: SeverityLevel.MEDIUM,
        }
    
    async def log_event(self, event: SecurityEvent) -> None:
        """Log security event to database and external systems"""
        try:
            # Log to database
            await self._log_to_database(event)
            
            # Log to structured logging for external SIEM
            await self._log_to_structured_logger(event)
            
            # Check for critical events requiring immediate alerts
            if event.severity == SeverityLevel.CRITICAL:
                await self._send_security_alert(event)
                
        except Exception as e:
            # Never let logging failures break the application
            print(f"Security logging failed: {e}")
    
    async def log_successful_login(self, user_id: str, email: str, ip_address: str, 
                                 device_fingerprint: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> None:
        """Log successful login event"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SeverityLevel.LOW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "device_fingerprint": device_fingerprint,
                "authentication_method": "password"
            },
            success=True,
            timestamp=datetime.now(timezone.utc)
        )
        await self.log_event(event)
    
    async def log_failed_login(self, email: str, reason: str, ip_address: str,
                             user_agent: Optional[str] = None) -> None:
        """Log failed login attempt"""
        # Determine severity based on reason
        severity = SeverityLevel.HIGH if reason == "brute_force" else SeverityLevel.MEDIUM
        
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            severity=severity,
            user_id=None,  # User not authenticated
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "failure_reason": reason,
                "authentication_method": "password"
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=f"Login failed: {reason}"
        )
        await self.log_event(event)
    
    async def log_successful_registration(self, user_id: str, email: str, ip_address: str,
                                        user_agent: Optional[str] = None) -> None:
        """Log successful user registration"""
        event = SecurityEvent(
            event_type=SecurityEventType.REGISTRATION_SUCCESS,
            severity=SeverityLevel.LOW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "registration_method": "email_password"
            },
            success=True,
            timestamp=datetime.now(timezone.utc)
        )
        await self.log_event(event)
    
    async def log_failed_registration(self, email: str, reason: str, ip_address: str,
                                    user_agent: Optional[str] = None) -> None:
        """Log failed registration attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.REGISTRATION_FAILED,
            severity=SeverityLevel.MEDIUM,
            user_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "email": email,
                "failure_reason": reason
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=f"Registration failed: {reason}"
        )
        await self.log_event(event)
    
    async def log_contract_upload(self, user_id: str, contract_id: str, airline: str,
                                ip_address: str, success: bool, 
                                error_message: Optional[str] = None) -> None:
        """Log contract upload attempt"""
        event = SecurityEvent(
            event_type=SecurityEventType.CONTRACT_UPLOAD,
            severity=SeverityLevel.MEDIUM,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=None,
            details={
                "contract_id": contract_id,
                "airline": airline,
                "upload_method": "web_form"
            },
            success=success,
            timestamp=datetime.now(timezone.utc),
            entity_type="contract",
            entity_id=contract_id,
            error_message=error_message
        )
        await self.log_event(event)
    
    async def log_access_denied(self, user_id: Optional[str], resource: str, 
                              required_permission: str, ip_address: str,
                              user_agent: Optional[str] = None) -> None:
        """Log access denied event"""
        event = SecurityEvent(
            event_type=SecurityEventType.ACCESS_DENIED,
            severity=SeverityLevel.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "resource": resource,
                "required_permission": required_permission,
                "access_method": "api_request"
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=f"Access denied to {resource}"
        )
        await self.log_event(event)
    
    async def log_rate_limit_exceeded(self, identifier: str, limit_type: str, 
                                    ip_address: str, user_id: Optional[str] = None) -> None:
        """Log rate limit exceeded event"""
        event = SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=SeverityLevel.HIGH,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=None,
            details={
                "identifier": identifier,
                "limit_type": limit_type,
                "rate_limit_window": "variable"
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=f"Rate limit exceeded: {limit_type}"
        )
        await self.log_event(event)
    
    async def log_suspicious_activity(self, user_id: Optional[str], activity_type: str,
                                    details: Dict[str, Any], ip_address: str,
                                    user_agent: Optional[str] = None) -> None:
        """Log suspicious activity for security monitoring"""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SeverityLevel.CRITICAL,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "activity_type": activity_type,
                **details
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=f"Suspicious activity detected: {activity_type}"
        )
        await self.log_event(event)
    
    async def log_system_error(self, operation: str, error: str, ip_address: str,
                             user_id: Optional[str] = None) -> None:
        """Log system errors for security monitoring"""
        event = SecurityEvent(
            event_type=SecurityEventType.SYSTEM_ERROR,
            severity=SeverityLevel.MEDIUM,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=None,
            details={
                "operation": operation,
                "error_type": type(error).__name__ if hasattr(error, '__name__') else "unknown"
            },
            success=False,
            timestamp=datetime.now(timezone.utc),
            error_message=error
        )
        await self.log_event(event)
    
    async def _log_to_database(self, event: SecurityEvent) -> None:
        """Log event to database audit_log table"""
        if not self.db_session:
            # Get database session if not provided
            async with get_session() as db:
                await self._insert_audit_record(db, event)
        else:
            await self._insert_audit_record(self.db_session, event)
    
    async def _insert_audit_record(self, db: AsyncSession, event: SecurityEvent) -> None:
        """Insert audit record into database"""
        try:
            # Create audit log record (matches database schema)
            audit_record = {
                "id": str(uuid.uuid4()),
                "user_id": event.user_id,
                "action": event.event_type.value,
                "entity_type": event.entity_type or "security_event",
                "entity_id": event.entity_id,
                "old_values": None,
                "new_values": event.details,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "success": event.success,
                "error_message": event.error_message,
                "metadata": {
                    "severity": event.severity.value,
                    "event_type": event.event_type.value,
                    "session_id": event.session_id
                },
                "created_at": event.timestamp
            }
            
            # Insert using raw SQL to avoid ORM complexity in logging
            from sqlalchemy import text
            query = text("""
                INSERT INTO audit_log (
                    id, user_id, action, entity_type, entity_id, old_values, 
                    new_values, ip_address, user_agent, success, error_message, 
                    metadata, created_at
                ) VALUES (
                    :id, :user_id, :action, :entity_type, :entity_id, :old_values,
                    :new_values, :ip_address, :user_agent, :success, :error_message,
                    :metadata, :created_at
                )
            """)
            
            await db.execute(query, audit_record)
            await db.commit()
            
        except Exception as e:
            print(f"Database audit logging failed: {e}")
            # Don't raise - logging failures should never break the application
    
    async def _log_to_structured_logger(self, event: SecurityEvent) -> None:
        """Log to structured logger for external SIEM integration"""
        import logging
        
        # Create structured log entry
        log_data = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "success": event.success,
            "details": event.details,
            "error_message": event.error_message,
            "session_id": event.session_id,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id
        }
        
        # Log with appropriate level based on severity
        logger = logging.getLogger("vectorbid.security")
        
        if event.severity == SeverityLevel.CRITICAL:
            logger.critical(json.dumps(log_data))
        elif event.severity == SeverityLevel.HIGH:
            logger.error(json.dumps(log_data))
        elif event.severity == SeverityLevel.MEDIUM:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
    
    async def _send_security_alert(self, event: SecurityEvent) -> None:
        """Send immediate alert for critical security events"""
        # TODO: Implement alerting (email, Slack, PagerDuty, etc.)
        print(f"🚨 CRITICAL SECURITY EVENT: {event.event_type.value}")
        print(f"   User: {event.user_id}")
        print(f"   IP: {event.ip_address}")
        print(f"   Details: {event.details}")
        print(f"   Time: {event.timestamp}")
    
    async def get_security_events(self, user_id: Optional[str] = None, 
                                event_type: Optional[SecurityEventType] = None,
                                severity: Optional[SeverityLevel] = None,
                                hours: int = 24) -> list[Dict[str, Any]]:
        """Get recent security events for monitoring"""
        # TODO: Implement database query to retrieve security events
        # This would be used by security monitoring dashboards
        pass