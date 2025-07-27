import smtplib
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.base import User, OTPVerification
from app.models.vouchers import PurchaseVoucher, SalesVoucher, PurchaseOrder, SalesOrder
import logging

# Assuming engine is defined in database.py; adjust if needed
from app.core.database import engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Internal method to send an email via SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # For demo purposes, log instead of sending
            logger.info(f"Sending email to {to_email}: Subject: {subject}\nBody: {body}")
            print(f"Sending email to {to_email}: Subject: {subject}\nBody: {body}")  # Console output for demo
            
            # In production, uncomment and use actual SMTP sending:
            # server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            # server.starttls()
            # server.login(self.smtp_username, self.smtp_password)
            # server.sendmail(self.smtp_username, to_email, msg.as_string())
            # server.quit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_otp_email(self, to_email: str, otp: str, purpose: str = "login") -> bool:
        """Send OTP via email"""
        subject = f"TRITIQ ERP - OTP for {purpose.title()}"
        body = f"Your OTP for {purpose} is: {otp}\n\nThis OTP is valid for 10 minutes."
        return self._send_email(to_email, subject, body)
    
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
email_service = EmailService()

def send_voucher_email(voucher_type: str, voucher_id: int, recipient_email: str, recipient_name: str):
    """Send email for a voucher, fetching details from the database."""
    db = SessionLocal()
    try:
        voucher = None
        details = ""
        
        if voucher_type == "purchase_voucher":
            voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
        elif voucher_type == "sales_voucher":
            voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
        elif voucher_type == "purchase_order":
            voucher = db.query(PurchaseOrder).filter(PurchaseOrder.id == voucher_id).first()
        elif voucher_type == "sales_order":
            voucher = db.query(SalesOrder).filter(SalesOrder.id == voucher_id).first()
        
        if voucher:
            # Generate details string; adjust based on actual model fields
            details = (
                f"Voucher Number: {voucher.voucher_number}\n"
                f"Date: {voucher.voucher_date}\n"
                f"Total Amount: {voucher.total_amount}\n"
                f"Status: {voucher.status}\n"
            )
            # Add more fields as needed, e.g., items summary if desired
        
        subject = f"TRITIQ ERP - {voucher_type.replace('_', ' ').title()} #{voucher_id}"
        body = (
            f"Dear {recipient_name},\n\n"
            f"A {voucher_type.replace('_', ' ')} has been created/updated with ID #{voucher_id}.\n\n"
            f"Details:\n{details}\n\n"
            f"Best regards,\nTRITIQ ERP Team"
        )
        
        email_service._send_email(recipient_email, subject, body)
    except Exception as e:
        logger.error(f"Failed to send voucher email for {voucher_type} #{voucher_id}: {e}")
    finally:
        db.close()