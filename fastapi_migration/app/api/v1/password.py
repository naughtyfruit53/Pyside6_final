"""
Password management endpoints for authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.models.base import User
from app.schemas.user import (
    PasswordChangeRequest, ForgotPasswordRequest, PasswordResetRequest, 
    PasswordChangeResponse, OTPResponse
)
from app.services.user_service import UserService
from app.services.otp_service import otp_service
from .user import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/change", response_model=PasswordChangeResponse)
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


@router.post("/forgot", response_model=OTPResponse)
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


@router.post("/reset", response_model=PasswordChangeResponse)
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