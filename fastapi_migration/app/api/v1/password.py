"""
Password management endpoints for authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
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
    password_data: PasswordChangeRequest = Body(...),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password with audit logging"""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
   
    # Enhanced request logging (without exposing password)
    logger.info(f"🔐 Password change request from user {current_user.email} "
                f"(ID: {current_user.id}, Role: {current_user.role}) "
                f"from IP: {client_ip}")
    logger.info(f"🔍 User must_change_password: {current_user.must_change_password}, "
                f"force_password_reset: {current_user.force_password_reset}")
    logger.info(f"📝 Request payload: new_password=*****, current_password={'PROVIDED' if password_data.current_password else 'NOT_PROVIDED'}, confirm_password={'PROVIDED' if password_data.confirm_password else 'NOT_PROVIDED'}")
   
    try:
        # Handle mandatory password change (e.g., for super admin first login)
        if current_user.must_change_password:
            # For mandatory password changes, skip current password verification
            logger.info(f"✅ Processing mandatory password change for user {current_user.email} "
                       f"(super admin or force reset scenario)")
            # For mandatory password changes, confirm_password is required if provided
            if password_data.confirm_password is not None and password_data.new_password != password_data.confirm_password:
                logger.error(f"❌ Password confirmation mismatch for mandatory password change")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New passwords do not match"
                )
        else:
            logger.info(f"🔄 Processing normal password change for user {current_user.email}")
            # For normal password changes, require and verify current password
            if not password_data.current_password:
                logger.error(f"❌ Password change failed for {current_user.email}: "
                           f"Current password is required for normal users")
                # Log failed password change attempt
                AuditLogger.log_password_reset(
                    db=db,
                    admin_email=current_user.email,
                    target_email=current_user.email,
                    admin_user_id=current_user.id,
                    target_user_id=current_user.id,
                    organization_id=current_user.organization_id,
                    success=False,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    error_message="Current password is required for normal password change",
                    reset_type="SELF_PASSWORD_CHANGE"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required"
                )
           
            if not verify_password(password_data.current_password, current_user.hashed_password):
                logger.error(f"❌ Password change failed for {current_user.email}: "
                           f"Incorrect current password provided from IP: {client_ip}")
                # Log failed password change attempt
                AuditLogger.log_password_reset(
                    db=db,
                    admin_email=current_user.email,
                    target_email=current_user.email,
                    admin_user_id=current_user.id,
                    target_user_id=current_user.id,
                    organization_id=current_user.organization_id,
                    success=False,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    error_message="Current password is incorrect",
                    reset_type="SELF_PASSWORD_CHANGE"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
           
            # For normal password changes, validate confirm_password if provided
            if password_data.confirm_password is not None and password_data.new_password != password_data.confirm_password:
                logger.error(f"❌ Password confirmation mismatch for normal password change")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New passwords do not match"
                )
       
        logger.info(f"✅ Password validation successful, updating password for user {current_user.email}")
       
        # Update password
        logger.info(f"🔄 Updating password for user {current_user.email}")
        current_user.hashed_password = get_password_hash(password_data.new_password)
        current_user.must_change_password = False
        current_user.force_password_reset = False
       
        # Clear temporary password if exists
        UserService.clear_temporary_password(db, current_user)
       
        db.commit()
        logger.info(f"✅ Password successfully updated and flags cleared for user {current_user.email}")
       
        # Log successful password change
        AuditLogger.log_password_reset(
            db=db,
            admin_email=current_user.email,
            target_email=current_user.email,
            admin_user_id=current_user.id,
            target_user_id=current_user.id,
            organization_id=current_user.organization_id,
            success=True,
            ip_address=client_ip,
            user_agent=user_agent,
            reset_type="SELF_PASSWORD_CHANGE"
        )
       
        logger.info(f"🎉 Password change completed successfully for user {current_user.email}")
        return PasswordChangeResponse(message="Password changed successfully")
       
    except HTTPException as he:
        logger.error(f"❌ HTTP Exception during password change: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"💥 Unexpected error during password change for user {current_user.email}: "
                    f"{type(e).__name__}: {str(e)}")
        logger.error(f"🔍 Error details - IP: {client_ip}, User-Agent: {user_agent}")
        db.rollback()
       
        # Log the unexpected error
        AuditLogger.log_password_reset(
            db=db,
            admin_email=current_user.email,
            target_email=current_user.email,
            admin_user_id=current_user.id,
            target_user_id=current_user.id,
            organization_id=current_user.organization_id,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
            error_message=f"Unexpected error: {str(e)}",
            reset_type="SELF_PASSWORD_CHANGE"
        )
       
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )
@router.post("/forgot", response_model=OTPResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest = Body(...),
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
    reset_data: PasswordResetRequest = Body(...),
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