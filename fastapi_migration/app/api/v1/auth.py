"""
Main authentication router that combines all authentication modules
"""
print("🔄 Loading enhanced v1 authentication module...")

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import UserInDB

# Import user authentication dependencies from submodules
from .user import (
    get_current_user, get_current_active_user, get_current_admin_user,
    get_current_platform_user, get_current_super_admin, get_current_organization_id,
    require_current_organization_id, validate_organization_access, get_tenant_db_session
)

# Import specialized auth modules
from .password import router as password_router
from .login import router as login_router
from .otp import router as otp_router
from .master_auth import router as master_auth_router
from .admin_setup import router as admin_setup_router

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Include all authentication sub-routes
router.include_router(password_router, prefix="/password", tags=["password-management"])
router.include_router(login_router, tags=["authentication"])
router.include_router(otp_router, prefix="/otp", tags=["otp-authentication"])
router.include_router(master_auth_router, prefix="/master-password", tags=["master-authentication"])
router.include_router(admin_setup_router, prefix="/admin", tags=["admin-setup"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Enhanced dependency to get current user from token with strict organization scoping
# (This function is defined in user.py but needs to be wrapped with oauth2_scheme)
async def get_current_user_with_oauth(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserInDB:
    """Get current user from JWT token with oauth2 scheme"""
    logger.info(f"Validating token: {token[:10]}...")  # Debug token prefix
    from .user import get_current_user
    return await get_current_user(token, db)


@router.post("/test-token", response_model=UserInDB)
async def test_token(current_user: UserInDB = Depends(get_current_active_user)):
    """Test endpoint to validate token and get user info"""
    return current_user


@router.post("/logout")
async def logout():
    """Logout endpoint (mainly for documentation - actual logout handled client-side)"""
    return {"message": "Logged out"}