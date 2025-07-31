"""
Reset service for handling database reset operations
"""
from sqlalchemy.orm import Session
from app.models.base import (
    Organization, User, Company, Product, Customer, Vendor, 
    Stock, AuditLog, EmailNotification, PaymentTerm, OTPVerification
)
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class ResetService:
    """Service for handling data reset operations"""
    
    @staticmethod
    def reset_organization_data(db: Session, organization_id: int) -> dict:
        """
        Reset all data for a specific organization
        
        Args:
            db: Database session
            organization_id: ID of the organization to reset
            
        Returns:
            dict: Result with message and deleted counts
        """
        try:
            result = {"message": "Organization data reset completed", "deleted": {}}
            
            # Delete in reverse dependency order to avoid foreign key constraints
            
            # Delete email notifications
            deleted_notifications = db.query(EmailNotification).filter(
                EmailNotification.organization_id == organization_id
            ).delete()
            result["deleted"]["email_notifications"] = deleted_notifications
            
            # Delete audit logs  
            deleted_audit_logs = db.query(AuditLog).filter(
                AuditLog.organization_id == organization_id
            ).delete()
            result["deleted"]["audit_logs"] = deleted_audit_logs
            
            # Delete stock entries
            deleted_stock = db.query(Stock).filter(
                Stock.organization_id == organization_id
            ).delete()
            result["deleted"]["stock"] = deleted_stock
            
            # Delete payment terms
            deleted_payment_terms = db.query(PaymentTerm).filter(
                PaymentTerm.organization_id == organization_id
            ).delete()
            result["deleted"]["payment_terms"] = deleted_payment_terms
            
            # Delete products
            deleted_products = db.query(Product).filter(
                Product.organization_id == organization_id
            ).delete()
            result["deleted"]["products"] = deleted_products
            
            # Delete customers
            deleted_customers = db.query(Customer).filter(
                Customer.organization_id == organization_id
            ).delete()
            result["deleted"]["customers"] = deleted_customers
            
            # Delete vendors
            deleted_vendors = db.query(Vendor).filter(
                Vendor.organization_id == organization_id
            ).delete()
            result["deleted"]["vendors"] = deleted_vendors
            
            # Delete companies
            deleted_companies = db.query(Company).filter(
                Company.organization_id == organization_id
            ).delete()
            result["deleted"]["companies"] = deleted_companies
            
            # Delete organization users (except super admin)
            deleted_users = db.query(User).filter(
                User.organization_id == organization_id,
                User.is_super_admin == False
            ).delete()
            result["deleted"]["users"] = deleted_users
            
            # Reset organization settings to defaults
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            if organization:
                organization.company_details_completed = False
                
            db.commit()
            
            logger.info(f"Organization {organization_id} data reset completed: {result['deleted']}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting organization {organization_id} data: {str(e)}")
            raise e
    
    @staticmethod
    def reset_all_data(db: Session) -> dict:
        """
        Reset all data in the system (Super Admin only)
        
        Args:
            db: Database session
            
        Returns:
            dict: Result with message and deleted counts
        """
        try:
            result = {"message": "All system data reset completed", "deleted": {}}
            
            # Delete in reverse dependency order to avoid foreign key constraints
            
            # Delete OTP verifications
            deleted_otps = db.query(OTPVerification).delete()
            result["deleted"]["otp_verifications"] = deleted_otps
            
            # Delete email notifications
            deleted_notifications = db.query(EmailNotification).delete()
            result["deleted"]["email_notifications"] = deleted_notifications
            
            # Delete audit logs
            deleted_audit_logs = db.query(AuditLog).delete()
            result["deleted"]["audit_logs"] = deleted_audit_logs
            
            # Delete stock entries
            deleted_stock = db.query(Stock).delete()
            result["deleted"]["stock"] = deleted_stock
            
            # Delete payment terms
            deleted_payment_terms = db.query(PaymentTerm).delete()
            result["deleted"]["payment_terms"] = deleted_payment_terms
            
            # Delete products
            deleted_products = db.query(Product).delete()
            result["deleted"]["products"] = deleted_products
            
            # Delete customers
            deleted_customers = db.query(Customer).delete()
            result["deleted"]["customers"] = deleted_customers
            
            # Delete vendors
            deleted_vendors = db.query(Vendor).delete()
            result["deleted"]["vendors"] = deleted_vendors
            
            # Delete companies
            deleted_companies = db.query(Company).delete()
            result["deleted"]["companies"] = deleted_companies
            
            # Delete organization users (except super admin)
            deleted_users = db.query(User).filter(User.is_super_admin == False).delete()
            result["deleted"]["users"] = deleted_users
            
            # Reset all organizations to defaults
            organizations = db.query(Organization).all()
            for org in organizations:
                org.company_details_completed = False
            
            result["deleted"]["organizations_reset"] = len(organizations)
            
            db.commit()
            
            logger.info(f"All system data reset completed: {result['deleted']}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting all system data: {str(e)}")
            raise e