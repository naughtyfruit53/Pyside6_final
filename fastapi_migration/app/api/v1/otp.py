"""
OTP (One-Time Password) authentication endpoints
Handles OTP request and verification for secure authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.models.base import User
from app.schemas.user import (
    Token, OTPRequest, OTPVerifyRequest, OTPResponse
)
from app.services.user_service import UserService
from app.services.otp_service import otp_service

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/request", response_model=OTPResponse)
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


@router.post("/verify", response_model=Token)
async def verify_otp(
    otp_verify: OTPVerifyRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Verify OTP and generate access token with audit logging"""
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
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "email": user.email, "organization_id": user.organization_id},
            expires_delta=access_token_expires
        )
        
        logger.info(f"OTP verified for {user.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OTP verification"
        )