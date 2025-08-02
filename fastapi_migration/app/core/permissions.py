"""
Permission checking system for role-based access control
"""
from typing import Optional, List
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from app.models.base import User, Organization
from app.schemas.base import UserRole
from app.core.database import get_db
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
import logging

logger = logging.getLogger(__name__)


class Permission:
    """Permission constants"""
    
    # User management permissions
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    DELETE_USERS = "delete_users"
    
    # Password management permissions
    RESET_OWN_PASSWORD = "reset_own_password"
    RESET_ORG_PASSWORDS = "reset_org_passwords"
    RESET_ANY_PASSWORD = "reset_any_password"
    
    # Data management permissions
    RESET_OWN_DATA = "reset_own_data"
    RESET_ORG_DATA = "reset_org_data"
    RESET_ANY_DATA = "reset_any_data"
    
    # Organization management permissions
    MANAGE_ORGANIZATIONS = "manage_organizations"
    VIEW_ORGANIZATIONS = "view_organizations"
    CREATE_ORGANIZATIONS = "create_organizations"
    DELETE_ORGANIZATIONS = "delete_organizations"
    
    # Platform administration permissions
    PLATFORM_ADMIN = "platform_admin"
    SUPER_ADMIN = "super_admin"
    
    # Audit permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_ALL_AUDIT_LOGS = "view_all_audit_logs"


class PermissionChecker:
    """Service for checking user permissions"""
    
    # Role-based permission mapping
    ROLE_PERMISSIONS = {
        UserRole.SUPER_ADMIN: [
            Permission.MANAGE_USERS,
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.DELETE_USERS,
            Permission.RESET_OWN_PASSWORD,
            Permission.RESET_ORG_PASSWORDS,
            Permission.RESET_ANY_PASSWORD,
            Permission.RESET_OWN_DATA,
            Permission.RESET_ORG_DATA,
            Permission.RESET_ANY_DATA,
            Permission.MANAGE_ORGANIZATIONS,
            Permission.VIEW_ORGANIZATIONS,
            Permission.CREATE_ORGANIZATIONS,
            Permission.DELETE_ORGANIZATIONS,
            Permission.PLATFORM_ADMIN,
            Permission.SUPER_ADMIN,
            Permission.VIEW_AUDIT_LOGS,
            Permission.VIEW_ALL_AUDIT_LOGS,
        ],
        UserRole.ORG_ADMIN: [
            Permission.MANAGE_USERS,
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.DELETE_USERS,
            Permission.RESET_OWN_PASSWORD,
            Permission.RESET_ORG_PASSWORDS,
            Permission.RESET_OWN_DATA,
            Permission.RESET_ORG_DATA,
            Permission.VIEW_AUDIT_LOGS,
        ],
        UserRole.ADMIN: [
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.RESET_OWN_PASSWORD,
            Permission.VIEW_AUDIT_LOGS,
        ],
        UserRole.STANDARD_USER: [
            Permission.RESET_OWN_PASSWORD,
        ],
    }
    
    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        """Check if user has a specific permission"""
        if not user or not user.role:
            return False
        
        # Super admin always has all permissions
        if getattr(user, 'is_super_admin', False) or user.role == UserRole.SUPER_ADMIN:
            return True
        
        user_permissions = PermissionChecker.ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions
    
    @staticmethod
    def require_permission(
        permission: str,
        user: User,
        db: Session,
        request: Optional[Request] = None,
        organization_id: Optional[int] = None
    ) -> bool:
        """Require user to have specific permission, raise exception if not"""
        if not PermissionChecker.has_permission(user, permission):
            # Log permission denied event
            if db and request:
                AuditLogger.log_permission_denied(
                    db=db,
                    user_email=user.email,
                    attempted_action=permission,
                    user_id=user.id,
                    user_role=user.role,
                    organization_id=organization_id or user.organization_id,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details={"required_permission": permission}
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return True
    
    @staticmethod
    def can_access_organization(user: User, organization_id: int) -> bool:
        """Check if user can access specific organization data"""
        # Super admin can access any organization
        if getattr(user, 'is_super_admin', False) or user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Regular users can only access their own organization
        return user.organization_id == organization_id
    
    @staticmethod
    def require_organization_access(
        user: User,
        organization_id: int,
        db: Session,
        request: Optional[Request] = None
    ) -> bool:
        """Require user to have access to specific organization"""
        if not PermissionChecker.can_access_organization(user, organization_id):
            # Log permission denied event
            if db and request:
                AuditLogger.log_permission_denied(
                    db=db,
                    user_email=user.email,
                    attempted_action=f"access_organization_{organization_id}",
                    user_id=user.id,
                    user_role=user.role,
                    organization_id=user.organization_id,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details={"requested_organization_id": organization_id}
                )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to organization {organization_id}"
            )
        return True
    
    @staticmethod
    def can_reset_user_password(current_user: User, target_user: User) -> bool:
        """Check if current user can reset target user's password"""
        # Super admin can reset any password
        if getattr(current_user, 'is_super_admin', False) or current_user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Org admin can reset passwords within their organization
        if current_user.role == UserRole.ORG_ADMIN:
            return current_user.organization_id == target_user.organization_id
        
        # Users can only reset their own password
        return current_user.id == target_user.id
    
    @staticmethod
    def can_reset_organization_data(current_user: User, organization_id: int) -> bool:
        """Check if current user can reset organization data"""
        # Super admin can reset any organization data
        if getattr(current_user, 'is_super_admin', False) or current_user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Org admin can reset data for their own organization
        if current_user.role == UserRole.ORG_ADMIN:
            return current_user.organization_id == organization_id
        
        return False
    
    @staticmethod
    def get_accessible_organizations(user: User, db: Session) -> List[int]:
        """Get list of organization IDs user can access"""
        # Super admin can access all organizations
        if getattr(user, 'is_super_admin', False) or user.role == UserRole.SUPER_ADMIN:
            organizations = db.query(Organization.id).all()
            return [org.id for org in organizations]
        
        # Regular users can only access their own organization
        if user.organization_id:
            return [user.organization_id]
        
        return []


def require_permission(permission: str):
    """Decorator factory for requiring specific permissions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a placeholder - actual implementation would depend on FastAPI dependency injection
            # The real implementation should be used as a FastAPI dependency
            return func(*args, **kwargs)
        return wrapper
    return decorator


# FastAPI dependencies for permission checking
def require_super_admin(
    current_user: User = Depends(lambda: None),  # This will be properly injected
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """FastAPI dependency to require super admin access"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    PermissionChecker.require_permission(
        Permission.SUPER_ADMIN,
        current_user,
        db,
        request
    )
    return current_user


def require_org_admin(
    current_user: User = Depends(lambda: None),  # This will be properly injected
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """FastAPI dependency to require org admin access"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if not PermissionChecker.has_permission(current_user, Permission.RESET_ORG_PASSWORDS):
        PermissionChecker.require_permission(
            Permission.SUPER_ADMIN,
            current_user,
            db,
            request
        )
    
    return current_user


def require_password_reset_permission(
    current_user: User = Depends(lambda: None),  # This will be properly injected
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """FastAPI dependency to require password reset permissions"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if user has any password reset permission
    if not (
        PermissionChecker.has_permission(current_user, Permission.RESET_ORG_PASSWORDS) or
        PermissionChecker.has_permission(current_user, Permission.RESET_ANY_PASSWORD)
    ):
        PermissionChecker.require_permission(
            Permission.RESET_ORG_PASSWORDS,
            current_user,
            db,
            request
        )
    
    return current_user


def require_data_reset_permission(
    current_user: User = Depends(lambda: None),  # This will be properly injected
    db: Session = Depends(get_db),
    request: Request = None
) -> User:
    """FastAPI dependency to require data reset permissions"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if user has any data reset permission
    if not (
        PermissionChecker.has_permission(current_user, Permission.RESET_ORG_DATA) or
        PermissionChecker.has_permission(current_user, Permission.RESET_ANY_DATA)
    ):
        PermissionChecker.require_permission(
            Permission.RESET_ORG_DATA,
            current_user,
            db,
            request
        )
    
    return current_user