"""
Master password authentication endpoints
Handles master password login functionality for admin access
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, is_super_admin_email
from app.core.config import settings
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.models.base import User, PlatformUser
from app.schemas.user import MasterPasswordLoginRequest, MasterPasswordLoginResponse
from app.services.user_service import UserService

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=MasterPasswordLoginResponse)
async def master_password_login(
    master_login: MasterPasswordLoginRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Enhanced master password login with comprehensive audit logging"""
    try:
        logger.info(f"Master password login attempt for email: {master_login.email}")
        
        # First check if this is a platform user (super admin)
        platform_user = None
        if is_super_admin_email(master_login.email):
            platform_user = db.query(PlatformUser).filter(
                PlatformUser.email == master_login.email,
                PlatformUser.is_active == True
            ).first()
            
            if platform_user and verify_password(master_login.master_password, platform_user.hashed_password):
                # Create access token for platform user
                access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={
                        "sub": platform_user.username,
                        "email": platform_user.email,
                        "is_platform_user": True,
                        "role": platform_user.role
                    },
                    expires_delta=access_token_expires
                )
                
                # Log successful master password login
                AuditLogger.log_master_password_usage(
                    db=db,
                    admin_email=platform_user.email,
                    admin_user_id=None,  # Platform users don't have regular user IDs
                    target_email=master_login.email,
                    target_user_id=None,
                    organization_id=None,  # Platform users are not organization-specific
                    success=True,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    action_type="PLATFORM_MASTER_LOGIN"
                )
                
                logger.info(f"Successful master password login for platform user: {platform_user.email}")
                
                return MasterPasswordLoginResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    user_type="platform_user",
                    user_id=None,
                    email=platform_user.email,
                    role=platform_user.role,
                    organization_id=None,
                    message="Platform user authenticated successfully"
                )
        
        # Look for organization user with master password access
        user = UserService.get_user_by_email(db, master_login.email)
        
        if not user:
            # Log failed attempt for non-existent user
            AuditLogger.log_master_password_usage(
                db=db,
                admin_email="unknown",
                admin_user_id=None,
                target_email=master_login.email,
                target_user_id=None,
                organization_id=None,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                action_type="MASTER_LOGIN_ATTEMPT",
                error_message="User not found"
            )
            
            logger.warning(f"Master password login attempt for non-existent email: {master_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or master password"
            )
        
        if not user.is_active:
            # Log failed attempt for inactive user
            AuditLogger.log_master_password_usage(
                db=db,
                admin_email=user.email,
                admin_user_id=user.id,
                target_email=master_login.email,
                target_user_id=user.id,
                organization_id=user.organization_id,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                action_type="MASTER_LOGIN_ATTEMPT",
                error_message="User account is inactive"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Check if user has master password set
        if not user.master_password_hash:
            # Log failed attempt - no master password
            AuditLogger.log_master_password_usage(
                db=db,
                admin_email=user.email,
                admin_user_id=user.id,
                target_email=master_login.email,
                target_user_id=user.id,
                organization_id=user.organization_id,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                action_type="MASTER_LOGIN_ATTEMPT",
                error_message="Master password not set for user"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Master password not configured for this account"
            )
        
        # Verify master password
        if not verify_password(master_login.master_password, user.master_password_hash):
            # Log failed master password attempt
            AuditLogger.log_master_password_usage(
                db=db,
                admin_email=user.email,
                admin_user_id=user.id,
                target_email=master_login.email,
                target_user_id=user.id,
                organization_id=user.organization_id,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                action_type="MASTER_LOGIN_ATTEMPT",
                error_message="Invalid master password"
            )
            
            logger.warning(f"Failed master password login for: {master_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or master password"
            )
        
        # Create access token with master password context
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.username,
                "email": user.email,
                "organization_id": user.organization_id,
                "master_access": True,  # Special flag for master password access
                "role": user.role
            },
            expires_delta=access_token_expires
        )
        
        # Log successful master password login
        AuditLogger.log_master_password_usage(
            db=db,
            admin_email=user.email,
            admin_user_id=user.id,
            target_email=master_login.email,
            target_user_id=user.id,
            organization_id=user.organization_id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            action_type="MASTER_LOGIN_SUCCESS"
        )
        
        logger.info(f"Successful master password login for: {user.email} (ID: {user.id})")
        
        return MasterPasswordLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_type="organization_user",
            user_id=user.id,
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            message="Master password authentication successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Master password login error for {master_login.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during master password login"
        )