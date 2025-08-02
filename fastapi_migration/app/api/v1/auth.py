"""
Enhanced authentication and authorization endpoints (API v1)
Comprehensive authentication with master password support, audit logging, and robust user lookup
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_token, is_super_admin_email
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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Enhanced dependency to get current user from token with strict organization scoping
async def get_current_user(
    token: str = Depends(oauth2_scheme),
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
async def test_token(current_user: User = Depends(get_current_user)):
    """Test if the current token is valid and return user info"""
    return current_user


@router.post("/logout")
async def logout(
    request: Request = None,
    current_user: User = Depends(get_current_user),
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


@router.post("/password/change", response_model=PasswordChangeResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password with audit logging"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            # Log failed password change attempt
            AuditLogger.log_password_reset(
                db=db,
                admin_email=current_user.email,
                target_email=current_user.email,
                admin_user_id=current_user.id,
                target_user_id=current_user.id,
                organization_id=current_user.organization_id,
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                error_message="Current password is incorrect",
                reset_type="SELF_PASSWORD_CHANGE"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        from app.core.security import get_password_hash
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.must_change_password = False
        current_user.force_password_reset = False
        
        # Clear temporary password if exists
        UserService.clear_temporary_password(db, current_user)
        
        db.commit()
        
        # Log successful password change
        AuditLogger.log_password_reset(
            db=db,
            admin_email=current_user.email,
            target_email=current_user.email,
            admin_user_id=current_user.id,
            target_user_id=current_user.id,
            organization_id=current_user.organization_id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_type="SELF_PASSWORD_CHANGE"
        )
        
        logger.info(f"Password changed for user {current_user.email}")
        return PasswordChangeResponse(message="Password changed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )


@router.post("/password/forgot", response_model=OTPResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Request password reset via OTP with audit logging"""
    try:
        # Check if user exists
        user = UserService.get_user_by_email(db, forgot_data.email)
        
        # Log forgot password request
        AuditLogger.log_password_reset(
            db=db,
            admin_email="system",
            target_email=forgot_data.email,
            target_user_id=user.id if user else None,
            organization_id=user.organization_id if user else None,
            success=user is not None and user.is_active,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            error_message="User not found or inactive" if not (user and user.is_active) else None,
            reset_type="FORGOT_PASSWORD_REQUEST"
        )
        
        if not user:
            # For security, we don't reveal if email exists or not
            logger.warning(f"Password reset requested for non-existent email: {forgot_data.email}")
            return OTPResponse(
                message="If the email exists in our system, a password reset OTP has been sent.",
                email=forgot_data.email
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Generate and send OTP for password reset
        otp = otp_service.create_otp_verification(db, forgot_data.email, "password_reset")
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate OTP. Please try again."
            )
        
        logger.info(f"Password reset OTP requested for {forgot_data.email}")
        return OTPResponse(
            message="Password reset OTP sent successfully to your email address.",
            email=forgot_data.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset request"
        )


@router.post("/password/reset", response_model=PasswordChangeResponse)
async def reset_password(
    reset_data: PasswordResetRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Reset password using OTP with audit logging"""
    try:
        # Verify OTP for password reset
        otp_valid = otp_service.verify_otp(db, reset_data.email, reset_data.otp, "password_reset")
        
        # Find user
        user = UserService.get_user_by_email(db, reset_data.email)
        
        # Log password reset attempt
        AuditLogger.log_password_reset(
            db=db,
            admin_email="system",
            target_email=reset_data.email,
            target_user_id=user.id if user else None,
            organization_id=user.organization_id if user else None,
            success=otp_valid and user is not None and user.is_active,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            error_message="Invalid OTP or user not found" if not (otp_valid and user) else None,
            reset_type="OTP_PASSWORD_RESET"
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
        
        # Update password
        from app.core.security import get_password_hash
        user.hashed_password = get_password_hash(reset_data.new_password)
        user.must_change_password = False
        user.force_password_reset = False
        
        # Reset failed login attempts and clear temporary password
        user.failed_login_attempts = 0
        user.locked_until = None
        UserService.clear_temporary_password(db, user)
        
        db.commit()
        
        logger.info(f"Password reset successfully for {user.email}")
        return PasswordChangeResponse(message="Password reset successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password reset"
        )