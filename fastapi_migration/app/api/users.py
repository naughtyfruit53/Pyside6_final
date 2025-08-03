from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user, get_current_admin_user, get_current_super_admin, get_current_organization_id, require_current_organization_id  # Updated import
from app.core.tenant import TenantQueryMixin  # Keep for TenantQueryMixin
from app.models.base import User, Organization
from app.schemas.base import UserCreate, UserUpdate, UserInDB, UserRole
from app.core.security import get_password_hash
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[UserInDB])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get users in current organization (admin only)"""
    
    query = db.query(User)
    
    # Super admins can see all users across organizations
    if current_user.is_super_admin:
        if active_only:
            query = query.filter(User.is_active == True)
    else:
        # Regular admins only see users in their organization
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, User, org_id)
        if active_only:
            query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserInDB)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user info"""
    return current_user

@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID"""
    # Users can view their own info, admins can view users in their org
    if current_user.id == user_id:
        return current_user
    
    if current_user.role not in [UserRole.ORG_ADMIN, UserRole.ADMIN] and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(user, current_user.organization_id)
    
    return user

@router.post("/", response_model=UserInDB)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create new user (admin only)"""
    
    # Determine organization for new user
    if current_user.is_super_admin and user.organization_id:
        org_id = user.organization_id
        # Verify organization exists
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization not found"
            )
    else:
        org_id = require_current_organization_id()
    
    # Check if email already exists in the organization
    existing_user = db.query(User).filter(
        User.email == user.email,
        User.organization_id == org_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this organization"
        )
    
    # Check if username already exists in the organization
    existing_username = db.query(User).filter(
        User.username == user.username,
        User.organization_id == org_id
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken in this organization"
        )
    
    # Check user limits for the organization
    if not current_user.is_super_admin:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        user_count = db.query(User).filter(
            User.organization_id == org_id,
            User.is_active == True
        ).count()
        
        if user_count >= org.max_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum user limit ({org.max_users}) reached for this organization"
            )
    
    # Validate role permissions
    if user.role == UserRole.ORG_ADMIN and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create organization administrators"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        organization_id=org_id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
        department=user.department,
        designation=user.designation,
        employee_id=user.employee_id,
        phone=user.phone,
        is_active=user.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User {user.email} created in org {org_id} by {current_user.email}")
    return db_user

@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user"""
    # Users can update their own info, admins can update users in their org
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    is_self_update = current_user.id == user_id
    is_admin = current_user.role in [UserRole.ORG_ADMIN, UserRole.ADMIN] or current_user.is_super_admin
    
    if not is_self_update and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(user, current_user.organization_id)
    
    # Restrict self-update fields for non-admin users
    if is_self_update and not is_admin:
        # Allow only basic updates for self
        allowed_fields = {"email", "username", "full_name", "phone", "department", "designation"}
        update_data = user_update.dict(exclude_unset=True)
        if not all(field in allowed_fields for field in update_data.keys()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update administrative fields"
            )
    
    # Check role update permissions
    if user_update.role:
        if user_update.role == UserRole.ORG_ADMIN and not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super administrators can assign organization administrator role"
            )
    
    # Check email uniqueness if being updated
    if user_update.email and user_update.email != user.email:
        existing_email = db.query(User).filter(
            User.email == user_update.email,
            User.organization_id == user.organization_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this organization"
            )
    
    # Check username uniqueness if being updated
    if user_update.username and user_update.username != user.username:
        existing_username = db.query(User).filter(
            User.username == user_update.username,
            User.organization_id == user.organization_id
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken in this organization"
            )
    
    # Update user
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User {user.email} updated by {current_user.email}")
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete user (admin only)"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(user, current_user.organization_id)
    
    # Prevent deleting the last admin in an organization
    if user.role == UserRole.ORG_ADMIN and not current_user.is_super_admin:
        admin_count = db.query(User).filter(
            User.organization_id == user.organization_id,
            User.role == UserRole.ORG_ADMIN,
            User.is_active == True
        ).count()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last organization administrator"
            )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User {user.email} deleted by {current_user.email}")
    return {"message": "User deleted successfully"}

@router.get("/organization/{org_id}", response_model=List[UserInDB])
async def get_organization_users(
    org_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Get users in specific organization (super admin only)"""
    
    query = db.query(User).filter(User.organization_id == org_id)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    return users