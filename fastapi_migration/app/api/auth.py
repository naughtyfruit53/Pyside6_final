"""
Authentication and authorization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional  # Added missing import
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_token
from app.core.config import settings
from app.core.tenant import TenantContext, TenantQueryMixin, get_organization_from_request  # Import shared tenant utils
from app.models.base import User, Organization
from app.schemas.base import Token, UserLogin, UserInDB, UserRole, OTPRequest, OTPVerifyRequest, OTPResponse, PasswordChangeRequest, ForgotPasswordRequest, PasswordResetRequest, PasswordChangeResponse
from app.services.email_service import email_service
from app.services.otp_service import otp_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Dependency to get current user from token
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        email, organization_id = verify_token(token)
        if email is None:
            raise credentials_exception
            
        # Set organization context if available
        if organization_id:
            TenantContext.set_organization_id(organization_id)
            
    except Exception:
        raise credentials_exception
    
    # Find user
    if organization_id:
        user = db.query(User).filter(
            User.email == email,
            User.organization_id == organization_id
        ).first()
    else:
        # For super admin
        user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        raise credentials_exception
    
    # Set user context
    TenantContext.set_user_id(user.id)
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user with admin privileges"""
    if current_user.role not in [UserRole.ORG_ADMIN, UserRole.ADMIN] and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin access required."
        )
    return current_user

async def get_current_super_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user with super admin privileges"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super administrator access required"
        )
    return current_user

# Moved from tenant.py to break circular import
def get_current_organization_id(current_user: User = Depends(get_current_active_user)) -> Optional[int]:
    """Get current organization ID from context or user"""
    org_id = TenantContext.get_organization_id()
    if org_id is not None:
        return org_id
    
    if current_user.organization_id:
        TenantContext.set_organization_id(current_user.organization_id)
        return current_user.organization_id
    
    if current_user.is_super_admin:
        # For super admins, organization ID can be None
        return None
    
    raise HTTPException(
        status_code=400,
        detail="No organization associated with user"
    )

def require_current_organization_id(current_user: User = Depends(get_current_active_user)) -> int:
    """Get current organization ID, raise error if not set or for super admin without specification"""
    org_id = get_current_organization_id(current_user)
    
    if org_id is None:
        if current_user.is_super_admin:
            raise HTTPException(
                status_code=400,
                detail="Super admin must specify organization ID"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="No organization context available"
            )
    
    return org_id

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Login with email and password to get access token"""
    try:
        # Get organization context from request
        organization = None
        if request:
            organization = get_organization_from_request(request, db)
        
        # Find user by email
        user = None
        if organization:
            # Find user within specific organization
            user = db.query(User).filter(
                User.email == form_data.username,
                User.organization_id == organization.id
            ).first()
        else:
            # For super admin login, find across all organizations
            user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            # Fallback to username if email not found
            if organization:
                user = db.query(User).filter(
                    User.username == form_data.username,
                    User.organization_id == organization.id
                ).first()
            else:
                user = db.query(User).filter(User.username == form_data.username).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
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
        
        # Reset failed login attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
        
        # Update last login
        from sqlalchemy.sql import func
        user.last_login = func.now()
        db.commit()
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email, 
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name for response
        org_name = None
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
        
        logger.info(f"User {user.email} logged in successfully")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": user.must_change_password or False,
            "is_first_login": user.last_login is None
        }
        
    except HTTPException:
        # Handle failed login attempts
        if 'user' in locals() and user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
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
    """Login with email and password"""
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
        
        # Find user
        user = None
        if organization:
            user = db.query(User).filter(
                User.email == user_credentials.email,
                User.organization_id == organization.id
            ).first()
        else:
            # For super admin login
            user = db.query(User).filter(User.email == user_credentials.email).first()
        
        if not user or not verify_password(user_credentials.password, user.hashed_password):
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
        
        # Update last login
        from sqlalchemy.sql import func
        user.last_login = func.now()
        db.commit()
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name
        org_name = None
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
        
        logger.info(f"User {user.email} logged in successfully via email")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": user.must_change_password or False,
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

@router.post("/test-token", response_model=UserInDB)
async def test_token(current_user: User = Depends(get_current_user)):
    """Test if the current token is valid and return user info"""
    return current_user

@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Successfully logged out"}

# OTP Authentication Endpoints
@router.post("/otp/request", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    """Request OTP for email authentication"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == otp_request.email).first()
        if not user:
            # For security, we don't reveal if email exists or not
            logger.warning(f"OTP requested for non-existent email: {otp_request.email}")
            # Still return success message
            return OTPResponse(
                message="If the email exists in our system, an OTP has been sent.",
                email=otp_request.email
            )
        
        # Check if user is active
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
    db: Session = Depends(get_db)
):
    """Verify OTP and login user"""
    try:
        # Verify OTP
        if not otp_service.verify_otp(db, otp_verify.email, otp_verify.otp, otp_verify.purpose):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Find user
        user = db.query(User).filter(User.email == otp_verify.email).first()
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
        
        # Reset failed login attempts on successful OTP login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
        
        # Update last login
        from sqlalchemy.sql import func
        user.last_login = func.now()
        db.commit()
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.email,
            organization_id=user.organization_id,
            expires_delta=access_token_expires
        )
        
        # Get organization name
        org_name = None
        if user.organization_id:
            org = db.query(Organization).filter(Organization.id == user.organization_id).first()
            org_name = org.name if org else None
        
        logger.info(f"User {user.email} logged in successfully via OTP")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "organization_id": user.organization_id,
            "organization_name": org_name,
            "user_role": user.role,
            "must_change_password": True,  # Always require password change after OTP login
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

@router.post("/admin/setup")
async def setup_admin_account(
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

@router.post("/password/change", response_model=PasswordChangeResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        from app.core.security import get_password_hash
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.must_change_password = False
        
        db.commit()
        
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
    db: Session = Depends(get_db)
):
    """Request password reset via OTP"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == forgot_data.email).first()
        if not user:
            # For security, we don't reveal if email exists or not
            logger.warning(f"Password reset requested for non-existent email: {forgot_data.email}")
            return OTPResponse(
                message="If the email exists in our system, a password reset OTP has been sent.",
                email=forgot_data.email
            )
        
        # Check if user is active
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
    db: Session = Depends(get_db)
):
    """Reset password using OTP"""
    try:
        # Verify OTP for password reset
        if not otp_service.verify_otp(db, reset_data.email, reset_data.otp, "password_reset"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Find user
        user = db.query(User).filter(User.email == reset_data.email).first()
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
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        
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