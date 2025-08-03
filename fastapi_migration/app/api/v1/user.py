"""
User authentication dependencies and utilities
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.core.tenant import TenantContext
from app.models.base import User, Organization, PlatformUser
from app.schemas.user import UserRole, UserInDB

router = APIRouter(prefix="/users")


async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token with enhanced organization validation"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        email, organization_id, user_type = verify_token(token)
        if email is None:
            raise credentials_exception
            
        # Set organization context if available
        if organization_id:
            TenantContext.set_organization_id(organization_id)
            
    except Exception:
        raise credentials_exception
    
    # Find user based on type
    if user_type == "platform":
        # Platform user
        platform_user = db.query(PlatformUser).filter(PlatformUser.email == email).first()
        if platform_user is None:
            raise credentials_exception
        
        # Convert to User object for compatibility (platform users have no organization)
        user = User(
            id=platform_user.id,
            email=platform_user.email,
            username=platform_user.email,  # Use email as username for platform users
            full_name=platform_user.full_name,
            role=platform_user.role,
            organization_id=None,  # Platform users don't belong to any organization
            is_active=platform_user.is_active,
            created_at=platform_user.created_at,
            updated_at=platform_user.updated_at,
            last_login=platform_user.last_login,
            hashed_password=platform_user.hashed_password
        )
        
        # Set platform user flag and super admin status
        user.is_platform_user = True
        user.is_super_admin = (platform_user.role == "super_admin")
        
    else:
        # Organization user (including super admins stored as User with organization_id=None)
        if organization_id:
            user = db.query(User).filter(
                User.email == email,
                User.organization_id == organization_id
            ).first()
        else:
            # Handle super admin case (organization_id=None)
            user = db.query(User).filter(
                User.email == email,
                User.organization_id.is_(None)
            ).first()
        
        if user is None:
            raise credentials_exception
        
        user.is_platform_user = user.is_super_admin  # Treat super admins as platform users for permissions
     
    # Set user context
    TenantContext.set_user_id(user.id)
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user with organization validation"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user with admin privileges"""
    if (current_user.role not in [UserRole.ORG_ADMIN, UserRole.ADMIN] and 
        not getattr(current_user, 'is_platform_user', False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    return current_user


async def get_current_platform_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user with platform privileges"""
    if not getattr(current_user, 'is_platform_user', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required"
        )
    return current_user


# Backward compatibility alias
async def get_current_super_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user with super admin privileges (backward compatibility)"""
    return await get_current_platform_user(current_user)


def get_current_organization_id(current_user: User = Depends(get_current_active_user)) -> Optional[int]:
    """Get current organization ID from context or user"""
    org_id = TenantContext.get_organization_id()
    if org_id is not None:
        return org_id
    
    if current_user.organization_id:
        TenantContext.set_organization_id(current_user.organization_id)
        return current_user.organization_id
    
    if getattr(current_user, 'is_platform_user', False):
        # For platform users, organization ID can be None
        return None
    
    raise HTTPException(
        status_code=400,
        detail="No organization associated with user"
    )


def require_current_organization_id(current_user: User = Depends(get_current_active_user)) -> int:
    """Get current organization ID, raise error if not set"""
    org_id = get_current_organization_id(current_user)
    
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required for this operation"
        )
    
    return org_id


def validate_organization_access(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Organization:
    """Validate that current user has access to the specified organization"""
    
    # Platform users have access to all organizations
    if getattr(current_user, 'is_platform_user', False):
        org = db.query(Organization).filter(Organization.id == organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )
        return org
    
    # Organization users can only access their own organization
    if current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to organization {organization_id}"
        )
    
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found"
        )
    
    return org


# Enhanced dependency for tenant-scoped database queries
def get_tenant_db_session(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Session:
    """Get database session with tenant context set"""
    if current_user.organization_id:
        TenantContext.set_organization_id(current_user.organization_id)
    return db


@router.get("/me", response_model=UserInDB)
async def get_current_user_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user"""
    return current_user