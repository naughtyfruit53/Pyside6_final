import smtplib
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.base import User, OTPVerification
import logging

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_otp_email(self, to_email: str, otp: str, purpose: str = "login") -> bool:
        """Send OTP via email"""
        try:
            # For demo purposes, we'll log the OTP instead of actually sending email
            # In production, implement actual SMTP sending
            logger.info(f"🔐 OTP for {to_email}: {otp} (Purpose: {purpose})")
            print(f"🔐 OTP for {to_email}: {otp} (Purpose: {purpose})")  # Console output for demo
            
            # In production, implement actual email sending:
            # subject = f"TRITIQ ERP - OTP for {purpose.title()}"
            # body = f"Your OTP for {purpose} is: {otp}\n\nThis OTP is valid for 10 minutes."
            # ... SMTP sending logic ...
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {e}")
            return False
    
    def create_otp_verification(self, db: Session, email: str, purpose: str = "login") -> Optional[str]:
        """Create OTP verification entry"""
        try:
            # Generate OTP
            otp = self.generate_otp()
            
            # Remove any existing OTP for this email and purpose
            db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose
            ).delete()
            
            # Create new OTP verification
            otp_verification = OTPVerification(
                email=email,
                otp_hash=get_password_hash(otp),  # Hash the OTP for security
                purpose=purpose,
                expires_at=datetime.utcnow() + timedelta(minutes=10),
                is_used=False
            )
            
            db.add(otp_verification)
            db.commit()
            
            # Send OTP email
            if self.send_otp_email(email, otp, purpose):
                return otp
            else:
                # Rollback if email failed
                db.rollback()
                return None
                
        except Exception as e:
            logger.error(f"Failed to create OTP verification for {email}: {e}")
            db.rollback()
            return None
    
    def verify_otp(self, db: Session, email: str, otp: str, purpose: str = "login") -> bool:
        """Verify OTP"""
        try:
            # Find valid OTP
            otp_verification = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.expires_at > datetime.utcnow(),
                OTPVerification.is_used == False
            ).first()
            
            if not otp_verification:
                return False
            
            # Check attempts
            if otp_verification.attempts >= otp_verification.max_attempts:
                return False
            
            # Increment attempts
            otp_verification.attempts += 1
            
            # Verify OTP
            if verify_password(otp, otp_verification.otp_hash):
                # Mark as used
                otp_verification.is_used = True
                otp_verification.used_at = datetime.utcnow()
                db.commit()
                return True
            else:
                db.commit()  # Save the incremented attempts
                return False
            
        except Exception as e:
            logger.error(f"Failed to verify OTP for {email}: {e}")
            return False

# Global instance
otp_service = OTPService()