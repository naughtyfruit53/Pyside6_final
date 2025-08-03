"""
Enhanced authentication and authorization endpoints (API v1)
Comprehensive authentication with master password support, audit logging, and robust user lookup
"""
print("🔄 Loading enhanced v1 authentication module...")

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_token, is_super_admin_email, get_password_hash
from app.core.config import settings
from app.core.tenant import TenantContext, TenantQueryFilter, get_organization_from_request
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.core.permissions import PermissionChecker, Permission
from app.models.base import User, Organization, PlatformUser
from app.schemas.user import (
    Token, UserLogin, UserInDB, UserRole, OTPRequest, OTPVerifyRequest, OTPResponse, 
    PasswordChangeRequest, ForgotPasswordRequest, PasswordResetRequest, PasswordChangeResponse,
    MasterPasswordLoginRequest, MasterPasswordLoginResponse
)
from app.services.user_service import UserService
from app.services.email_service import email_service
from app.services.otp_service import otp_service

# Import user authentication dependencies from submodules
from .user import (
    get_current_user, get_current_active_user, get_current_admin_user,
    get_current_platform_user, get_current_super_admin, get_current_organization_id,
    require_current_organization_id, validate_organization_access, get_tenant_db_session
)
from .password import router as password_router

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Include password management routes
router.include_router(password_router, prefix="/password", tags=["password-management"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Enhanced dependency to get current user from token with strict organization scoping
# (This function is defined in user.py but needs to be wrapped with oauth2_scheme)
async def get_current_user_with_oauth(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token with oauth2 scheme"""
    from .user import get_current_user
    return await get_current_user(token, db)


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Enhanced login with comprehensive user lookup and audit logging"""
    try:
        # Get organization context from request
        organization = None
        if request:
            organization = get_organization_from_request(request, db)
        
        organization_id = organization.id if organization else None
        
        # Attempt authentication with UserService
        user = UserService.authenticate_user(
            db=db,
            email=form_data.username,
            password=form_data.password,
            organization_id=organization_id,
            allow_master_password=True
        )
        
        # If no user found by email, try username
        if not user:
            user = UserService.get_user_by_username(db, form_data.username, organization_id)
            if user:
                user = UserService.authenticate_user(
                    db=db,
                    email=user.email,
                    password=form_data.password,
                    organization_id=organization_id,
                    allow_master_password=True
                )
        
        success = user is not None
        
        # Log master password usage if applicable
        if (user and user.email == "naughtyfruit53@gmail.com" and 
            is_super_admin_email(user.email) and 
            form_data.password == "Qweasdzxc"):
            AuditLogger.log_master_password_usage(
                db=db,
                email=user.email,
                organization_id=user.organization_id,
                user_id=user.id,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={"login_method": "master_password"}
            )
        
        # Log login attempt
        AuditLogger.log_login_attempt(
            db=db,
            email=form_data.username,
            success=success,
            organization_id=organization_id,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            error_message="Invalid credentials" if not success else None,
            details={
                "login_method": "password",
                "organization_context": organization.name if organization else None
            }
        )
        
        if not user:
            # Update failed login attempts for the user if found
            potential_user = UserService.get_user_by_email(db, form_data.username, organization_id)
            if potential_user:
                UserService.update_login_attempt(db, potential_user, success=False)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is temporarily locked due to multiple failed login attempts",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check organization status for non-super-admin users
        if not user.is_super_admin:
            user_org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            if not user_org or user_org.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Organization is not active",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Update successful login
        UserService.update_login_attempt(db, user, success=True)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email, 
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name and company details status for response
        org_name = None
        company_details_completed = True  # Default for super admin
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
            company_details_completed = org.company_details_completed if org else False
        
        logger.info(f"User {user.email} logged in successfully")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": user.must_change_password or False,
            "force_password_reset": getattr(user, 'force_password_reset', False),
            "company_details_completed": company_details_completed,
            "is_first_login": user.last_login is None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/login/email", response_model=Token)
async def login_with_email(
    user_credentials: UserLogin,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Enhanced email login with comprehensive authentication"""
    print(f"🔑 Enhanced v1 /login/email endpoint called for email: {user_credentials.email}")
    try:
        # Get organization context
        organization = None
        if user_credentials.subdomain:
            organization = db.query(Organization).filter(
                Organization.subdomain == user_credentials.subdomain.lower(),
                Organization.status == "active"
            ).first()
        elif request:
            organization = get_organization_from_request(request, db)
        
        organization_id = organization.id if organization else None
        
        # Authenticate user
        user = UserService.authenticate_user(
            db=db,
            email=user_credentials.email,
            password=user_credentials.password,
            organization_id=organization_id,
            allow_master_password=True
        )
        
        success = user is not None
        
        # Log master password usage if applicable
        if (user and user.email == "naughtyfruit53@gmail.com" and 
            is_super_admin_email(user.email) and 
            user_credentials.password == "Qweasdzxc"):
            AuditLogger.log_master_password_usage(
                db=db,
                email=user.email,
                organization_id=user.organization_id,
                user_id=user.id,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={"login_method": "email_master_password"}
            )
        
        # Log login attempt
        AuditLogger.log_login_attempt(
            db=db,
            email=user_credentials.email,
            success=success,
            organization_id=organization_id,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            error_message="Invalid credentials" if not success else None,
            details={
                "login_method": "email",
                "subdomain": user_credentials.subdomain,
                "organization_context": organization.name if organization else None
            }
        )
        
        if not user:
            # Update failed login attempts for the user if found
            potential_user = UserService.get_user_by_email(db, user_credentials.email, organization_id)
            if potential_user:
                UserService.update_login_attempt(db, potential_user, success=False)
                
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update successful login
        UserService.update_login_attempt(db, user, success=True)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name and company details status
        org_name = None
        company_details_completed = True  # Default for super admin
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
            company_details_completed = org.company_details_completed if org else False
        
        logger.info(f"User {user.email} logged in successfully via email")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": user.must_change_password or False,
            "force_password_reset": getattr(user, 'force_password_reset', False),
            "company_details_completed": company_details_completed,
            "is_first_login": user.last_login is None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during email login"
        )


@router.post("/master-password/login", response_model=MasterPasswordLoginResponse)
async def master_password_login(
    credentials: MasterPasswordLoginRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Temporary master password login with forced password reset"""
    try:
        # Check if this is the designated super admin
        if not is_super_admin_email(credentials.email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Master password access is restricted"
            )
        
        # Verify master password
        if credentials.master_password != "Qweasdzxc":  # Temporary master password
            AuditLogger.log_login_attempt(
                db=db,
                email=credentials.email,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                error_message="Invalid master password",
                details={"login_method": "master_password_failed"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid master password"
            )
        
        # Find user
        user = UserService.get_user_by_email(db, credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Force password reset
        user.force_password_reset = True
        db.commit()
        
        # Log master password usage
        AuditLogger.log_master_password_usage(
            db=db,
            email=user.email,
            organization_id=user.organization_id,
            user_id=user.id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"forced_password_reset": True}
        )
        
        # Update login info
        UserService.update_login_attempt(db, user, success=True)
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        logger.info(f"Master password login successful for {user.email} - password reset required")
        return MasterPasswordLoginResponse(
            message="Master password login successful. You must change your password immediately.",
            access_token=access_token,
            force_password_reset=True,
            organization_id=user.organization_id,
            user_role=user.role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Master password login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during master password login"
        )


@router.post("/test-token", response_model=UserInDB)
async def test_token(current_user: User = Depends(get_current_user_with_oauth)):
    """Test if the current token is valid and return user info"""
    return current_user


@router.post("/logout")
async def logout(
    request: Request = None,
    current_user: User = Depends(get_current_user_with_oauth),
    db: Session = Depends(get_db)
):
    """Logout endpoint with audit logging"""
    try:
        # Log logout event
        AuditLogger.log_login_attempt(
            db=db,
            email=current_user.email,
            success=True,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            user_role=current_user.role,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"action": "logout"}
        )
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Logged out"}


# OTP Authentication Endpoints (Enhanced with audit logging)
@router.post("/otp/request", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Request OTP for email authentication with audit logging"""
    try:
        # Check if user exists
        user = UserService.get_user_by_email(db, otp_request.email)
        
        # Log OTP request
        AuditLogger.log_login_attempt(
            db=db,
            email=otp_request.email,
            success=user is not None and user.is_active,
            organization_id=user.organization_id if user else None,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "action": "otp_request",
                "purpose": otp_request.purpose,
                "user_exists": user is not None
            }
        )
        
        if not user:
            # For security, we don't reveal if email exists or not
            logger.warning(f"OTP requested for non-existent email: {otp_request.email}")
            return OTPResponse(
                message="If the email exists in our system, an OTP has been sent.",
                email=otp_request.email
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Generate and send OTP
        otp = otp_service.create_otp_verification(db, otp_request.email, otp_request.purpose)
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate OTP. Please try again."
            )
        
        logger.info(f"OTP requested for {otp_request.email} - Purpose: {otp_request.purpose}")
        return OTPResponse(
            message="OTP sent successfully to your email address.",
            email=otp_request.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OTP request"
        )


@router.post("/otp/verify", response_model=Token)
async def verify_otp_and_login(
    otp_verify: OTPVerifyRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Verify OTP and login user with audit logging"""
    try:
        # Verify OTP
        otp_valid = otp_service.verify_otp(db, otp_verify.email, otp_verify.otp, otp_verify.purpose)
        
        # Find user
        user = UserService.get_user_by_email(db, otp_verify.email)
        
        # Log OTP verification attempt
        AuditLogger.log_login_attempt(
            db=db,
            email=otp_verify.email,
            success=otp_valid and user is not None and user.is_active,
            organization_id=user.organization_id if user else None,
            user_id=user.id if user else None,
            user_role=user.role if user else None,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            error_message="Invalid or expired OTP" if not otp_valid else None,
            details={
                "action": "otp_verify",
                "purpose": otp_verify.purpose,
                "otp_valid": otp_valid
            }
        )
        
        if not otp_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Check organization status if not super admin
        if not user.is_super_admin:
            user_org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            if not user_org or user_org.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Organization is not active"
                )
        
        # Update successful login
        UserService.update_login_attempt(db, user, success=True)
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name and company details status
        org_name = None
        company_details_completed = True  # Default for super admin
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
            company_details_completed = org.company_details_completed if org else False
        
        logger.info(f"User {user.email} logged in successfully via OTP")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": True,  # Always require password change after OTP login
            "force_password_reset": True,
            "company_details_completed": company_details_completed,
            "is_first_login": user.last_login is None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OTP verification"
        )


# Password change endpoint is handled by the password router included above


# Password forgot and reset endpoints are handled by the password router included above


@router.post("/admin/setup")
async def setup_admin_account(
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Setup the initial app admin account (naughtyfruit53@gmail.com)"""
    try:
        admin_email = "naughtyfruit53@gmail.com"
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            return {"message": "Admin account already exists", "email": admin_email}
        
        # Create admin user
        from app.core.security import get_password_hash
        admin_user = User(
            email=admin_email,
            username="app_admin",
            full_name="App Administrator",
            hashed_password=get_password_hash("123456"),  # Default password
            role=UserRole.SUPER_ADMIN,
            is_super_admin=True,
            is_active=True,
            organization_id=None  # Super admin doesn't belong to any organization
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Log admin setup
        AuditLogger.log_password_reset(
            db=db,
            admin_email="system",
            target_email=admin_email,
            target_user_id=admin_user.id,
            organization_id=None,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_type="ADMIN_SETUP",
            details={"default_password_set": True}
        )
        
        logger.info(f"Admin account created: {admin_email}")
        return {
            "message": "Admin account created successfully",
            "email": admin_email,
            "default_password": "123456",
            "note": "Please change the default password after first login"
        }
        
    except Exception as e:
        logger.error(f"Admin setup error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup admin account"
        )