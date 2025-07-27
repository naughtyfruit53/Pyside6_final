# api.auth.py (revised)

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_token
from app.core.config import settings
from app.core.tenant import get_organization_from_request, TenantContext
from app.models.base import User, Organization
from app.schemas.base import Token, UserLogin, UserInDB, UserRole
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
            "user_role": user.role
        }
        
    except HTTPException:
        # Handle failed login attempts
        if 'user' in locals() and user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                from datetime import datetime, timedelta
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
            "user_role": user.role
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