# Revised: app/services/email_service.py (Using Brevo API)

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.logging import log_email_operation
from app.models.base import User, OTPVerification
from app.models.vouchers import PurchaseVoucher, SalesVoucher, PurchaseOrder, SalesOrder
import logging

# Brevo (Sendinblue) import
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Assuming engine is defined in database.py; adjust if needed
from app.core.database import engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.brevo_api_key = getattr(settings, 'BREVO_API_KEY', None)
        self.from_email = getattr(settings, 'BREVO_FROM_EMAIL', None) or getattr(settings, 'EMAILS_FROM_EMAIL', 'naughtyfruit53@gmail.com')
        self.from_name = getattr(settings, 'BREVO_FROM_NAME', 'TRITIQ ERP')
        
        if self.brevo_api_key:
            try:
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = self.brevo_api_key
                self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
                logger.info("Brevo email service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Brevo API client: {e}")
                self.api_instance = None
        else:
            logger.warning("Brevo API key not configured - email functionality will be limited")
            self.api_instance = None
        
    def _validate_email_config(self) -> tuple[bool, str]:
        """Validate email configuration"""
        if not self.brevo_api_key:
            return False, "Brevo API key is missing"
        return True, "Email configuration is valid"
    
    def _send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Internal method to send an email via Brevo with enhanced error handling.
        Returns tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Validate configuration
            is_valid, error_msg = self._validate_email_config()
            if not is_valid:
                logger.warning(f"Email configuration invalid: {error_msg}")
                log_email_operation("send", to_email, False, error_msg)
                return False, error_msg
            
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": self.from_name, "email": self.from_email},
                subject=subject,
                text_content=body
            )
            if html_body:
                send_smtp_email.html_content = html_body
            
            self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {to_email}")
            log_email_operation("send", to_email, True)
            return True, None
            
        except ApiException as e:
            error_msg = f"Brevo API error: {str(e)}"
            logger.error(error_msg)
            log_email_operation("send", to_email, False, error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            log_email_operation("send", to_email, False, error_msg)
            return False, error_msg
    
    def load_email_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """
        Load and render email template with variables.
        Returns tuple of (plain_text, html_content)
        """
        try:
            template_path = Path(__file__).parent.parent / "templates" / "email" / f"{template_name}.html"
            
            if not template_path.exists():
                logger.warning(f"Email template not found: {template_path}")
                return self._generate_fallback_content(**kwargs)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Simple template variable replacement
            for key, value in kwargs.items():
                placeholder = f"{{{{{key}}}}}"
                html_content = html_content.replace(placeholder, str(value) if value is not None else "")
            
            # Generate plain text version from HTML (simplified)
            plain_text = self._html_to_plain(html_content, **kwargs)
            
            return plain_text, html_content
            
        except Exception as e:
            logger.error(f"Error loading email template {template_name}: {e}")
            return self._generate_fallback_content(**kwargs)
    
    def _html_to_plain(self, html_content: str, **kwargs) -> str:
        """Convert HTML to plain text (simplified version)"""
        import re
        
        # Remove HTML tags
        plain = re.sub('<[^<]+?>', '', html_content)
        
        # Clean up whitespace
        plain = re.sub(r'\s+', ' ', plain).strip()
        
        return plain
    
    def _generate_fallback_content(self, **kwargs) -> tuple[str, str]:
        """Generate fallback email content when template is not available"""
        user_name = kwargs.get('user_name', 'User')
        new_password = kwargs.get('new_password', '[PASSWORD]')
        reset_by = kwargs.get('reset_by', 'Administrator')
        
        plain_text = f"""
Dear {user_name},

Your password has been reset by a system administrator.

New Password: {new_password}

For security reasons, you will be required to change this password on your next login.

Reset by: {reset_by}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

If you did not request this password reset, please contact your system administrator immediately.

Best regards,
TRITIQ ERP Team
"""
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #007bff;">TRITIQ ERP - Password Reset</h2>
    <p>Dear {user_name},</p>
    <p>Your password has been reset by a system administrator.</p>
    <div style="background-color: #f8f9fa; border: 2px solid #007bff; padding: 15px; margin: 20px 0; text-align: center;">
        <strong>New Password: <span style="font-family: monospace; color: #007bff;">{new_password}</span></strong>
    </div>
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0;">
        <strong>⚠️ Important:</strong> You will be required to change this password on your next login.
    </div>
    <p><strong>Reset by:</strong> {reset_by}<br>
       <strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <p style="color: #d73527;"><strong>If you did not request this password reset, please contact your system administrator immediately.</strong></p>
    <p>Best regards,<br>TRITIQ ERP Team</p>
</body>
</html>
"""
        
        return plain_text, html_content
    
    def send_password_reset_email(self, 
                                  user_email: str, 
                                  user_name: str, 
                                  new_password: str, 
                                  reset_by: str,
                                  organization_name: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Send password reset email with template"""
        try:
            template_vars = {
                'user_name': user_name,
                'user_email': user_email,
                'new_password': new_password,
                'reset_by': reset_by,
                'organization_name': organization_name or 'Your Organization',
                'reset_date': datetime.now().strftime('%Y-%m-%d'),
                'reset_time': datetime.now().strftime('%H:%M:%S'),
                'sent_date': datetime.now().strftime('%Y-%m-%d'),
                'sent_time': datetime.now().strftime('%H:%M:%S'),
                'admin_contact': self.from_email
            }
            
            plain_text, html_content = self.load_email_template('password_reset', **template_vars)
            
            subject = "TRITIQ ERP - Password Reset Notification"
            
            return self._send_email(user_email, subject, plain_text, html_content)
            
        except Exception as e:
            error_msg = f"Error preparing password reset email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def send_otp_email(self, to_email: str, otp: str, purpose: str = "login") -> tuple[bool, Optional[str]]:
        """Send OTP via email with error handling"""
        try:
            subject = f"TRITIQ ERP - OTP for {purpose.title()}"
            body = f"""
Dear User,

Your OTP for {purpose} is: {otp}

This OTP is valid for 10 minutes only.

If you did not request this OTP, please ignore this email or contact support.

Best regards,
TRITIQ ERP Team
"""
            
            return self._send_email(to_email, subject, body)
            
        except Exception as e:
            error_msg = f"Error sending OTP email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_otp_verification(self, db: Session, email: str, purpose: str = "login") -> tuple[Optional[str], Optional[str]]:
        """
        Create OTP verification entry with enhanced error handling.
        Returns tuple of (otp: Optional[str], error_message: Optional[str])
        """
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
            success, error = self.send_otp_email(email, otp, purpose)
            if success:
                return otp, None
            else:
                # Rollback if email failed
                db.rollback()
                return None, error
                
        except Exception as e:
            error_msg = f"Failed to create OTP verification for {email}: {str(e)}"
            logger.error(error_msg)
            db.rollback()
            return None, error_msg
    
    def verify_otp(self, db: Session, email: str, otp: str, purpose: str = "login") -> tuple[bool, Optional[str]]:
        """
        Verify OTP with enhanced error handling.
        Returns tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Find valid OTP
            otp_verification = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.expires_at > datetime.utcnow(),
                OTPVerification.is_used == False
            ).first()
            
            if not otp_verification:
                return False, "Invalid or expired OTP"
            
            # Check attempts
            if otp_verification.attempts >= otp_verification.max_attempts:
                return False, "Maximum OTP attempts exceeded"
            
            # Increment attempts
            otp_verification.attempts += 1
            
            # Verify OTP
            if verify_password(otp, otp_verification.otp_hash):
                # Mark as used
                otp_verification.is_used = True
                otp_verification.used_at = datetime.utcnow()
                db.commit()
                return True, None
            else:
                db.commit()  # Save the incremented attempts
                return False, "Invalid OTP"
            
        except Exception as e:
            error_msg = f"Failed to verify OTP for {email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

# Global instance
email_service = EmailService()

def send_voucher_email(voucher_type: str, voucher_id: int, recipient_email: str, recipient_name: str) -> tuple[bool, Optional[str]]:
    """
    Send email for a voucher, fetching details from the database.
    Returns tuple of (success: bool, error_message: Optional[str])
    """
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
        
        if not voucher:
            error_msg = f"Voucher not found: {voucher_type} #{voucher_id}"
            logger.error(error_msg)
            return False, error_msg
        
        # Generate details string; adjust based on actual model fields
        details = (
            f"Voucher Number: {voucher.voucher_number}\n"
            f"Date: {voucher.voucher_date if hasattr(voucher, 'voucher_date') else voucher.date}\n"
            f"Total Amount: {voucher.total_amount}\n"
            f"Status: {voucher.status}\n"
        )
        
        subject = f"TRITIQ ERP - {voucher_type.replace('_', ' ').title()} #{voucher.voucher_number}"
        body = f"""
Dear {recipient_name},

A {voucher_type.replace('_', ' ')} has been created/updated.

Details:
{details}

Please login to your TRITIQ ERP account to view the complete details.

Best regards,
TRITIQ ERP Team
"""
        
        success, error = email_service._send_email(recipient_email, subject, body)
        return success, error
        
    except Exception as e:
        error_msg = f"Failed to send voucher email for {voucher_type} #{voucher_id}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        db.close()