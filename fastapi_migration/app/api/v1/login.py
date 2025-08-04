"""
Standard login authentication endpoints
Handles username/password and email/password authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.core.tenant import get_organization_from_request
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.models.base import User
from app.schemas.user import Token, UserLogin
from app.services.user_service import UserService

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request = None,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Enhanced login with comprehensive organization isolation, audit logging, and account lockout protection"""
    
    # Extract organization information from request headers
    organization_context = get_organization_from_request(request)
    organization_id = organization_context.organization_id if organization_context else None
    organization_name = organization_context.organization_name if organization_context else None
    
    try:
        # Try to find user by username first, then by email if username fails
        user = UserService.get_user_by_username(db, form_data.username, organization_id)
        lookup_method = "username"
        
        if not user:
            user = UserService.get_user_by_email(db, form_data.username, organization_id)
            lookup_method = "email"
        
        # Account lockout check (even if user doesn't exist, to prevent enumeration)
        if user and UserService.is_account_locked(user):
            logger.warning(f"Login attempt for locked account: {form_data.username}")
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email if user else form_data.username,
                success=False,
                organization_id=user.organization_id if user else organization_id,
                user_id=user.id if user else None,
                user_role=user.role if user else None,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "account_locked",
                    "lookup_method": lookup_method,
                    "failed_attempts": user.failed_login_attempts if user else 0
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts. Please try again later or contact support."
            )
        
        # Verify password and user validity
        if not user or not verify_password(form_data.password, user.hashed_password):
            # Increment failed login attempts for existing users
            if user:
                UserService.increment_failed_login_attempts(db, user)
            
            # Log failed login attempt
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email if user else form_data.username,
                success=False,
                organization_id=user.organization_id if user else organization_id,
                user_id=user.id if user else None,
                user_role=user.role if user else None,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "invalid_credentials",
                    "lookup_method": lookup_method,
                    "user_exists": user is not None,
                    "failed_attempts": user.failed_login_attempts if user else 0
                }
            )
            
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email,
                success=False,
                organization_id=user.organization_id,
                user_id=user.id,
                user_role=user.role,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "inactive_account",
                    "lookup_method": lookup_method
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account"
            )
        
        # Organization validation
        if organization_id and user.organization_id != organization_id:
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email,
                success=False,
                organization_id=user.organization_id,
                user_id=user.id,
                user_role=user.role,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "organization_mismatch",
                    "lookup_method": lookup_method,
                    "expected_org": organization_id,
                    "user_org": user.organization_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to the specified organization"
            )
        
        # Reset failed login attempts on successful login
        UserService.reset_failed_login_attempts(db, user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Log successful login
        AuditLogger.log_login_attempt(
            db=db,
            email=user.email,
            success=True,
            organization_id=user.organization_id,
            user_id=user.id,
            user_role=user.role,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "lookup_method": lookup_method,
                "organization_name": organization_name
            }
        )
        
        logger.info(f"Successful login for {user.email} (ID: {user.id}) in organization {user.organization_id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "must_change_password": user.must_change_password
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/login/email", response_model=Token)
async def login_with_email(
    user_login: UserLogin,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Enhanced email-based login with organization isolation and audit logging"""
    
    # Extract organization information from request headers
    organization_context = get_organization_from_request(request)
    organization_id = organization_context.organization_id if organization_context else None
    organization_name = organization_context.organization_name if organization_context else None
    
    try:
        # Find user by email
        user = UserService.get_user_by_email(db, user_login.email, organization_id)
        
        # Account lockout check
        if user and UserService.is_account_locked(user):
            logger.warning(f"Login attempt for locked email account: {user_login.email}")
            AuditLogger.log_login_attempt(
                db=db,
                email=user_login.email,
                success=False,
                organization_id=user.organization_id if user else organization_id,
                user_id=user.id if user else None,
                user_role=user.role if user else None,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "account_locked",
                    "lookup_method": "email",
                    "failed_attempts": user.failed_login_attempts if user else 0
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts. Please try again later or contact support."
            )
        
        # Verify password and user validity
        if not user or not verify_password(user_login.password, user.hashed_password):
            # Increment failed login attempts for existing users
            if user:
                UserService.increment_failed_login_attempts(db, user)
            
            # Log failed login attempt
            AuditLogger.log_login_attempt(
                db=db,
                email=user_login.email,
                success=False,
                organization_id=user.organization_id if user else organization_id,
                user_id=user.id if user else None,
                user_role=user.role if user else None,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "invalid_credentials",
                    "lookup_method": "email",
                    "user_exists": user is not None,
                    "failed_attempts": user.failed_login_attempts if user else 0
                }
            )
            
            logger.warning(f"Failed email login attempt for: {user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email,
                success=False,
                organization_id=user.organization_id,
                user_id=user.id,
                user_role=user.role,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "inactive_account",
                    "lookup_method": "email"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user account"
            )
        
        # Organization validation
        if organization_id and user.organization_id != organization_id:
            AuditLogger.log_login_attempt(
                db=db,
                email=user.email,
                success=False,
                organization_id=user.organization_id,
                user_id=user.id,
                user_role=user.role,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={
                    "reason": "organization_mismatch",
                    "lookup_method": "email",
                    "expected_org": organization_id,
                    "user_org": user.organization_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to the specified organization"
            )
        
        # Reset failed login attempts on successful login
        UserService.reset_failed_login_attempts(db, user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Log successful login
        AuditLogger.log_login_attempt(
            db=db,
            email=user.email,
            success=True,
            organization_id=user.organization_id,
            user_id=user.id,
            user_role=user.role,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "lookup_method": "email",
                "organization_name": organization_name
            }
        )
        
        logger.info(f"Successful email login for {user.email} (ID: {user.id}) in organization {user.organization_id}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "email": user.email,
            "organization_id": user.organization_id,
            "must_change_password": user.must_change_password
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email login error for {user_login.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during email login"
        )