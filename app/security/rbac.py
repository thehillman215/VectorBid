"""
Role-Based Access Control (RBAC) System
Implements fine-grained permissions for VectorBid resources
"""
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.security.authentication import JWTManager
from app.security.session_manager import SessionManager
from app.security.audit_logger import SecurityAuditLogger


class Role(str, Enum):
    """System roles with hierarchical permissions"""
    ADMIN = "admin"              # Full system access
    APPROVER = "approver"        # Can approve contracts
    PILOT = "pilot"              # Basic pilot access
    READONLY = "readonly"        # Read-only access


class Permission(str, Enum):
    """Fine-grained permissions"""
    
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Pilot Profile Management
    PILOT_READ_OWN = "pilot:read:own"
    PILOT_UPDATE_OWN = "pilot:update:own"
    PILOT_READ_ALL = "pilot:read:all"
    PILOT_UPDATE_ALL = "pilot:update:all"
    
    # Contract Management
    CONTRACT_CREATE = "contract:create"
    CONTRACT_READ = "contract:read"
    CONTRACT_UPDATE = "contract:update"
    CONTRACT_DELETE = "contract:delete"
    CONTRACT_APPROVE = "contract:approve"
    CONTRACT_UPLOAD = "contract:upload"
    
    # Rule Management
    RULE_CREATE = "rule:create"
    RULE_READ = "rule:read"
    RULE_UPDATE = "rule:update"
    RULE_DELETE = "rule:delete"
    
    # PBS Operations
    PBS_GENERATE = "pbs:generate"
    PBS_OPTIMIZE = "pbs:optimize"
    PBS_EXPORT = "pbs:export"
    PBS_VALIDATE = "pbs:validate"
    
    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_METRICS = "system:metrics"
    SYSTEM_BACKUP = "system:backup"
    
    # Audit and Security
    AUDIT_READ = "audit:read"
    SECURITY_MANAGE = "security:manage"


@dataclass
class UserContext:
    """User context for authorization decisions"""
    user_id: str
    email: str
    role: Role
    permissions: Set[Permission]
    is_verified: bool
    airline: Optional[str] = None
    pilot_id: Optional[str] = None


class RolePermissionMatrix:
    """Defines role-based permission mappings"""
    
    # Role hierarchy (higher roles inherit lower role permissions)
    ROLE_HIERARCHY = {
        Role.ADMIN: [Role.APPROVER, Role.PILOT, Role.READONLY],
        Role.APPROVER: [Role.PILOT, Role.READONLY],
        Role.PILOT: [Role.READONLY],
        Role.READONLY: []
    }
    
    # Base permissions for each role
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.PILOT_READ_ALL,
            Permission.PILOT_UPDATE_ALL,
            Permission.CONTRACT_CREATE,
            Permission.CONTRACT_READ,
            Permission.CONTRACT_UPDATE,
            Permission.CONTRACT_DELETE,
            Permission.CONTRACT_APPROVE,
            Permission.RULE_CREATE,
            Permission.RULE_READ,
            Permission.RULE_UPDATE,
            Permission.RULE_DELETE,
            Permission.PBS_GENERATE,
            Permission.PBS_OPTIMIZE,
            Permission.PBS_EXPORT,
            Permission.PBS_VALIDATE,
            Permission.SYSTEM_CONFIG,
            Permission.SYSTEM_LOGS,
            Permission.SYSTEM_METRICS,
            Permission.SYSTEM_BACKUP,
            Permission.AUDIT_READ,
            Permission.SECURITY_MANAGE,
        },
        Role.APPROVER: {
            Permission.CONTRACT_READ,
            Permission.CONTRACT_APPROVE,
            Permission.CONTRACT_UPDATE,
            Permission.RULE_READ,
            Permission.PBS_GENERATE,
            Permission.PBS_OPTIMIZE,
            Permission.PBS_VALIDATE,
            Permission.AUDIT_READ,
        },
        Role.PILOT: {
            Permission.PILOT_READ_OWN,
            Permission.PILOT_UPDATE_OWN,
            Permission.CONTRACT_CREATE,
            Permission.CONTRACT_READ,
            Permission.CONTRACT_UPLOAD,
            Permission.RULE_READ,
            Permission.PBS_GENERATE,
            Permission.PBS_OPTIMIZE,
            Permission.PBS_EXPORT,
            Permission.PBS_VALIDATE,
        },
        Role.READONLY: {
            Permission.CONTRACT_READ,
            Permission.RULE_READ,
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role: Role) -> Set[Permission]:
        """Get all permissions for a role (including inherited)"""
        permissions = set()
        
        # Add direct permissions
        permissions.update(cls.ROLE_PERMISSIONS.get(role, set()))
        
        # Add inherited permissions
        for inherited_role in cls.ROLE_HIERARCHY.get(role, []):
            permissions.update(cls.ROLE_PERMISSIONS.get(inherited_role, set()))
        
        return permissions


class AccessControl:
    """Main access control service"""
    
    def __init__(self, session_manager: SessionManager, audit_logger: SecurityAuditLogger):
        self.session_manager = session_manager
        self.audit_logger = audit_logger
        self.jwt_manager = JWTManager()
        self.security = HTTPBearer(auto_error=False)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> UserContext:
        """Get current authenticated user context"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Verify JWT token
            token_payload = self.jwt_manager.verify_token(credentials.credentials)
            
            # Check session validity
            token_hash = self.session_manager.hash_token(credentials.credentials)
            session_info = await self.session_manager.get_session_by_token(token_hash)
            
            if not session_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update session activity
            await self.session_manager.update_session_activity(session_info.session_id)
            
            # Get user permissions
            role = Role(token_payload.get("role", "readonly"))
            permissions = RolePermissionMatrix.get_role_permissions(role)
            
            return UserContext(
                user_id=token_payload["sub"],
                email=token_payload["email"],
                role=role,
                permissions=permissions,
                is_verified=token_payload.get("verified", False),
                airline=token_payload.get("airline"),
                pilot_id=token_payload.get("pilot_id")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def require_permission(self, required_permission: Permission, user_context: UserContext, 
                               resource_context: Optional[Dict[str, any]] = None) -> None:
        """Check if user has required permission for resource"""
        
        # Check basic permission
        if required_permission not in user_context.permissions:
            await self.audit_logger.log_access_denied(
                user_id=user_context.user_id,
                resource=f"permission:{required_permission.value}",
                required_permission=required_permission.value,
                ip_address="unknown"  # Will be set by middleware
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Apply resource-specific access control
        await self._check_resource_access(required_permission, user_context, resource_context)
    
    async def _check_resource_access(self, permission: Permission, user_context: UserContext,
                                   resource_context: Optional[Dict[str, any]]) -> None:
        """Apply resource-specific access control rules"""
        
        if not resource_context:
            return
        
        # Pilot can only access their own data (unless admin/approver)
        if permission in [Permission.PILOT_READ_OWN, Permission.PILOT_UPDATE_OWN]:
            resource_pilot_id = resource_context.get("pilot_id")
            if (resource_pilot_id and 
                resource_pilot_id != user_context.pilot_id and 
                user_context.role not in [Role.ADMIN, Role.APPROVER]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to resource"
                )
        
        # Contract access control by airline
        if "contract" in permission.value:
            resource_airline = resource_context.get("airline")
            if (resource_airline and 
                user_context.airline and 
                resource_airline != user_context.airline and 
                user_context.role not in [Role.ADMIN, Role.APPROVER]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to airline-specific resource"
                )
        
        # Email verification requirement for sensitive operations
        sensitive_permissions = [
            Permission.CONTRACT_UPLOAD,
            Permission.CONTRACT_CREATE,
            Permission.PBS_EXPORT
        ]
        if permission in sensitive_permissions and not user_context.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required for this operation"
            )


# Dependency functions for FastAPI
async def get_current_user(
    access_control: AccessControl = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> UserContext:
    """FastAPI dependency to get current user"""
    return await access_control.get_current_user(credentials)


def require_role(required_role: Role):
    """FastAPI dependency to require specific role"""
    async def role_checker(user_context: UserContext = Depends(get_current_user)) -> UserContext:
        if user_context.role.value not in [role.value for role in RolePermissionMatrix.ROLE_HIERARCHY.get(required_role, [required_role])]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return user_context
    return role_checker


def require_permission(required_permission: Permission, resource_context: Optional[Dict[str, any]] = None):
    """FastAPI dependency to require specific permission"""
    async def permission_checker(
        user_context: UserContext = Depends(get_current_user),
        access_control: AccessControl = Depends()
    ) -> UserContext:
        await access_control.require_permission(required_permission, user_context, resource_context)
        return user_context
    return permission_checker


def require_verified_email():
    """FastAPI dependency to require verified email"""
    async def verification_checker(user_context: UserContext = Depends(get_current_user)) -> UserContext:
        if not user_context.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required"
            )
        return user_context
    return verification_checker


def require_same_airline(resource_airline: str):
    """FastAPI dependency to require same airline access"""
    async def airline_checker(user_context: UserContext = Depends(get_current_user)) -> UserContext:
        if (user_context.airline != resource_airline and 
            user_context.role not in [Role.ADMIN, Role.APPROVER]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to airline-specific resource"
            )
        return user_context
    return airline_checker


# Example usage decorators for route protection
class RequirePermissions:
    """Class-based permission requirements for cleaner route decoration"""
    
    @staticmethod
    def admin_only():
        return require_role(Role.ADMIN)
    
    @staticmethod
    def approver_or_admin():
        return require_role(Role.APPROVER)
    
    @staticmethod
    def authenticated():
        return Depends(get_current_user)
    
    @staticmethod
    def verified_email():
        return require_verified_email()
    
    @staticmethod
    def contract_read():
        return require_permission(Permission.CONTRACT_READ)
    
    @staticmethod
    def contract_upload():
        return require_permission(Permission.CONTRACT_UPLOAD)
    
    @staticmethod
    def pbs_generate():
        return require_permission(Permission.PBS_GENERATE)
    
    @staticmethod
    def system_admin():
        return require_permission(Permission.SYSTEM_CONFIG)