import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from jinja2 import Template
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.base import EmailNotification
from datetime import datetime

logger = logging.getLogger(__name__)

# Email templates
VOUCHER_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{voucher_type_display}} - {{voucher_number}}</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #0D47A1; margin: 0;">TRITIQ ERP</h1>
            <p style="color: #666; margin: 5px 0;">Enterprise Resource Planning System</p>
        </div>
        
        <h2 style="color: #333; border-bottom: 2px solid #0D47A1; padding-bottom: 10px;">{{voucher_type_display}}</h2>
        
        <div style="margin: 20px 0;">
            <p>Dear {{recipient_name}},</p>
            <p>Please find attached the {{voucher_type_display}} details:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; background-color: #f8f9fa; font-weight: bold;">Voucher Number:</td>
                    <td style="padding: 8px;">{{voucher_number}}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f8f9fa; font-weight: bold;">Date:</td>
                    <td style="padding: 8px;">{{voucher_date}}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f8f9fa; font-weight: bold;">Total Amount:</td>
                    <td style="padding: 8px;">₹{{total_amount}}</td>
                </tr>
                {% if notes %}
                <tr>
                    <td style="padding: 8px; background-color: #f8f9fa; font-weight: bold;">Notes:</td>
                    <td style="padding: 8px;">{{notes}}</td>
                </tr>
                {% endif %}
            </table>
        </div>
        
        <div style="margin: 30px 0; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
            <p style="margin: 0; color: #0D47A1;">
                <strong>Thank you for your business!</strong><br>
                For any queries, please contact us at {{company_email}} or {{company_phone}}.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
            <p>This email was generated automatically by TRITIQ ERP System</p>
            <p>{{company_name}} • {{company_address}}</p>
        </div>
    </div>
</body>
</html>
"""

async def send_voucher_email(
    voucher_type: str,
    voucher_id: int,
    recipient_email: str,
    recipient_name: str = "",
    custom_subject: Optional[str] = None,
    custom_message: Optional[str] = None
):
    """Send voucher email notification"""
    db = SessionLocal()
    email_notification = None
    
    try:
        # Create email notification record
        email_notification = EmailNotification(
            to_email=recipient_email,
            subject=custom_subject or f"TRITIQ ERP - {voucher_type.replace('_', ' ').title()}",
            body=custom_message or f"Please find attached {voucher_type.replace('_', ' ')} details.",
            voucher_type=voucher_type,
            voucher_id=voucher_id,
            status="pending"
        )
        db.add(email_notification)
        db.commit()
        db.refresh(email_notification)
        
        # Get voucher details
        voucher_data = await get_voucher_data(voucher_type, voucher_id, db)
        if not voucher_data:
            raise Exception(f"Voucher not found: {voucher_type} {voucher_id}")
        
        # Prepare email content
        template = Template(VOUCHER_EMAIL_TEMPLATE)
        html_content = template.render(
            voucher_type_display=voucher_type.replace('_', ' ').title(),
            recipient_name=recipient_name or "Valued Customer",
            voucher_number=voucher_data.get('voucher_number', 'N/A'),
            voucher_date=voucher_data.get('date', datetime.now()).strftime('%d-%m-%Y'),
            total_amount=f"{voucher_data.get('total_amount', 0):.2f}",
            notes=voucher_data.get('notes', ''),
            company_name="TRITIQ Corporation",
            company_email="info@tritiq.com",
            company_phone="+91-XXXXXXXXXX",
            company_address="Business Address"
        )
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_notification.subject
        msg['From'] = settings.EMAILS_FROM_EMAIL or "noreply@tritiq.com"
        msg['To'] = recipient_email
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        await send_email(msg)
        
        # Update notification status
        email_notification.status = "sent"
        email_notification.sent_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Email sent successfully to {recipient_email} for {voucher_type} {voucher_id}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        
        if email_notification:
            email_notification.status = "failed"
            email_notification.error_message = str(e)
            db.commit()
        
        raise e
    
    finally:
        db.close()

async def get_voucher_data(voucher_type: str, voucher_id: int, db):
    """Get voucher data based on type"""
    try:
        if voucher_type == "purchase_voucher":
            from app.models.vouchers import PurchaseVoucher
            voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
        elif voucher_type == "sales_voucher":
            from app.models.vouchers import SalesVoucher
            voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
        elif voucher_type == "purchase_order":
            from app.models.vouchers import PurchaseOrder
            voucher = db.query(PurchaseOrder).filter(PurchaseOrder.id == voucher_id).first()
        elif voucher_type == "sales_order":
            from app.models.vouchers import SalesOrder
            voucher = db.query(SalesOrder).filter(SalesOrder.id == voucher_id).first()
        else:
            return None
        
        if voucher:
            return {
                'voucher_number': voucher.voucher_number,
                'date': voucher.date,
                'total_amount': voucher.total_amount,
                'notes': voucher.notes
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting voucher data: {e}")
        return None

async def send_email(message: MIMEMultipart):
    """Send email using SMTP"""
    try:
        if settings.SENDGRID_API_KEY:
            # Use SendGrid
            await send_email_sendgrid(message)
        else:
            # Use SMTP
            await send_email_smtp(message)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

async def send_email_smtp(message: MIMEMultipart):
    """Send email using SMTP"""
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            text = message.as_string()
            server.sendmail(
                message['From'],
                [message['To']],
                text
            )
        logger.info(f"Email sent via SMTP to {message['To']}")
        
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        raise

async def send_email_sendgrid(message: MIMEMultipart):
    """Send email using SendGrid"""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        
        # Convert MIMEMultipart to SendGrid format
        mail = Mail(
            from_email=message['From'],
            to_emails=message['To'],
            subject=message['Subject']
        )
        
        # Get HTML content
        for part in message.walk():
            if part.get_content_type() == "text/html":
                mail.content = part.get_payload()
                break
        
        response = sg.send(mail)
        logger.info(f"Email sent via SendGrid to {message['To']}, status: {response.status_code}")
        
    except Exception as e:
        logger.error(f"SendGrid send failed: {e}")
        raise

# Background task for bulk email sending
async def send_bulk_emails(email_list: list):
    """Send emails in bulk"""
    for email_data in email_list:
        try:
            await send_voucher_email(**email_data)
        except Exception as e:
            logger.error(f"Failed to send bulk email: {e}")
            continue