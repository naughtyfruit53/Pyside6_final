"""
Admin setup endpoints
Handles admin account setup and initialization
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.services.user_service import UserService

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/setup")
async def setup_admin_account(
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Setup initial admin account if none exists
    This is a one-time setup endpoint for initial system configuration
    """
    try:
        # Check if any admin users already exist
        existing_admin = UserService.has_existing_admin(db)
        
        if existing_admin:
            # Log attempted admin setup when admin already exists
            AuditLogger.log_admin_action(
                db=db,
                admin_email="unknown",
                action="ADMIN_SETUP_ATTEMPT",
                success=False,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details={"reason": "Admin already exists"}
            )
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Admin account already exists"
            )
        
        # Create initial admin account
        admin_user = UserService.create_initial_admin(db)
        
        # Log successful admin setup
        AuditLogger.log_admin_action(
            db=db,
            admin_email=admin_user.email,
            action="ADMIN_SETUP_SUCCESS",
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "admin_id": admin_user.id,
                "admin_username": admin_user.username,
                "organization_id": admin_user.organization_id
            }
        )
        
        logger.info(f"Initial admin account created: {admin_user.email}")
        
        return {
            "message": "Admin account setup completed successfully",
            "admin_email": admin_user.email,
            "admin_username": admin_user.username,
            "organization_id": admin_user.organization_id,
            "next_steps": [
                "Login with the provided credentials",
                "Change the default password",
                "Configure organization settings",
                "Create additional user accounts"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during admin setup"
        )