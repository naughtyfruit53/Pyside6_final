"""
Platform user authentication and management endpoints
For SaaS platform-level users (super admins, platform admins)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, timezone
import datetime as dt
from typing import Optional
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.models.base import PlatformUser
from app.schemas.base import (
    PlatformUserLogin, PlatformToken, PlatformUserCreate, PlatformUserUpdate, 
    PlatformUserInDB, PlatformUserRole
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependencies for platform user authentication - defined early to avoid circular imports
async def get_current_platform_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/platform/login")),
    db: Session = Depends(get_db)
) -> PlatformUser:
    """Get current platform user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        from app.core.security import verify_token
        email, _, user_type = verify_token(token)  # organization_id will be None for platform users
        if email is None or user_type != "platform":
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    # Find platform user
    platform_user = db.query(PlatformUser).filter(PlatformUser.email == email).first()
    
    if platform_user is None:
        raise credentials_exception
    
    return platform_user

async def get_current_active_platform_user(
    current_platform_user: PlatformUser = Depends(get_current_platform_user),
) -> PlatformUser:
    """Get current active platform user"""
    if not current_platform_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive platform user")
    return current_platform_user

async def get_current_platform_super_admin(
    current_platform_user: PlatformUser = Depends(get_current_active_platform_user),
) -> PlatformUser:
    """Get current platform user with super admin privileges"""
    if current_platform_user.role != PlatformUserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform super administrator access required"
        )
    return current_platform_user

# Platform-specific JWT creation
def create_platform_access_token(
    subject: str, 
    expires_delta: timedelta = None
) -> str:
    """Create access token for platform users (no organization_id)"""
    if expires_delta:
        expire = dt.datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = dt.datetime.now(tz=timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "user_type": "platform",  # Distinguish from organization users
        "organization_id": None   # Platform users have no organization
    }
    
    from jose import jwt
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=PlatformToken)
async def platform_login(
    user_credentials: PlatformUserLogin,
    db: Session = Depends(get_db)
):
    """Login endpoint for platform users"""
    try:
        # Find platform user by email
        platform_user = db.query(PlatformUser).filter(
            PlatformUser.email == user_credentials.email
        ).first()
        
        if not platform_user or not verify_password(user_credentials.password, platform_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not platform_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Platform user account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        from sqlalchemy.sql import func
        platform_user.last_login = func.now()
        db.commit()
        
        # Create platform-specific access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_platform_access_token(
            subject=platform_user.email,
            expires_delta=access_token_expires
        )
        
        logger.info(f"Platform user {platform_user.email} logged in successfully")
        return PlatformToken(
            access_token=access_token, 
            token_type="bearer",
            user_role=platform_user.role,
            user_type="platform"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Platform login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during platform login"
        )

@router.post("/create", response_model=PlatformUserInDB)
async def create_platform_user(
    user_data: PlatformUserCreate,
    db: Session = Depends(get_db),
    current_platform_user: PlatformUser = Depends(get_current_platform_super_admin)
):
    """Create a new platform user (super admin only)"""
    try:
        # Check if email already exists
        existing_user = db.query(PlatformUser).filter(
            PlatformUser.email == user_data.email
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new platform user
        hashed_password = get_password_hash(user_data.password)
        platform_user = PlatformUser(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        db.add(platform_user)
        db.commit()
        db.refresh(platform_user)
        
        logger.info(f"Platform user {user_data.email} created by {current_platform_user.email}")
        return platform_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Platform user creation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating platform user"
        )

@router.get("/me", response_model=PlatformUserInDB)
async def get_current_platform_user_info(
    current_platform_user: PlatformUser = Depends(get_current_active_platform_user)
):
    """Get current platform user info"""
    return current_platform_user

@router.post("/logout")
async def platform_logout():
    """Platform logout endpoint (client should discard token)"""
    return {"message": "Successfully logged out from platform"}

@router.post("/reset-all-data")
async def reset_all_platform_data(
    db: Session = Depends(get_db),
    current_platform_user = Depends(get_current_platform_super_admin)
):
    """Reset all system data (Platform Super Admin only)"""
    from app.services.reset_service import ResetService
    
    try:
        result = ResetService.reset_all_data(db)
        logger.info(f"Platform super admin {current_platform_user.email} reset all system data")
        return {
            "message": "All system data has been reset successfully",
            "details": result["deleted"]
        }
    except Exception as e:
        logger.error(f"Error resetting all data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset all data. Please try again."
        )