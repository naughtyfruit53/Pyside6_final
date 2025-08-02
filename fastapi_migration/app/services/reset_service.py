"""
Enhanced reset service for handling database reset operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any, Optional
from app.models.base import (
    Organization, User, Company, Product, Customer, Vendor, 
    Stock, EmailNotification, PaymentTerm, OTPVerification, PlatformUser
)
from app.core.audit import AuditLogger
from app.schemas.reset import (
    DataResetRequest, DataResetResponse, OrganizationDataResetResponse,
    DataResetType, ResetScope
)
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)


class ResetService:
    """Service for handling data reset operations"""
    
    @staticmethod
    def reset_organization_data(
        db: Session, 
        organization_id: int,
        admin_user: User,
        reset_request: DataResetRequest,
        request=None
    ) -> OrganizationDataResetResponse:
        """
        Reset data for a specific organization based on reset request
        
        Args:
            db: Database session
            organization_id: ID of the organization to reset
            admin_user: User performing the reset
            reset_request: Reset configuration
            request: HTTP request for audit logging
            
        Returns:
            OrganizationDataResetResponse: Result with message and deleted counts
        """
        try:
            # Verify organization exists
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            if not organization:
                raise ValueError(f"Organization {organization_id} not found")
            
            deletion_summary = {}
            data_types_reset = []
            total_deleted = 0
            errors = []
            
            # Reset data based on configuration
            if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_vouchers:
                try:
                    # Delete vouchers and related data (would include from vouchers module)
                    # For now, we'll track this as a placeholder
                    deletion_summary["vouchers"] = 0
                    data_types_reset.append("vouchers")
                except Exception as e:
                    errors.append(f"Failed to delete vouchers: {str(e)}")
            
            if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_stock:
                try:
                    deleted_stock = db.query(Stock).filter(
                        Stock.organization_id == organization_id
                    ).delete()
                    deletion_summary["stock"] = deleted_stock
                    total_deleted += deleted_stock
                    data_types_reset.append("stock")
                except Exception as e:
                    errors.append(f"Failed to delete stock: {str(e)}")
            
            if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_products:
                try:
                    deleted_products = db.query(Product).filter(
                        Product.organization_id == organization_id
                    ).delete()
                    deletion_summary["products"] = deleted_products
                    total_deleted += deleted_products
                    data_types_reset.append("products")
                except Exception as e:
                    errors.append(f"Failed to delete products: {str(e)}")
            
            if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_customers:
                try:
                    deleted_customers = db.query(Customer).filter(
                        Customer.organization_id == organization_id
                    ).delete()
                    deletion_summary["customers"] = deleted_customers
                    total_deleted += deleted_customers
                    data_types_reset.append("customers")
                except Exception as e:
                    errors.append(f"Failed to delete customers: {str(e)}")
            
            if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_vendors:
                try:
                    deleted_vendors = db.query(Vendor).filter(
                        Vendor.organization_id == organization_id
                    ).delete()
                    deletion_summary["vendors"] = deleted_vendors
                    total_deleted += deleted_vendors
                    data_types_reset.append("vendors")
                except Exception as e:
                    errors.append(f"Failed to delete vendors: {str(e)}")
            
            if reset_request.include_companies:
                try:
                    deleted_companies = db.query(Company).filter(
                        Company.organization_id == organization_id
                    ).delete()
                    deletion_summary["companies"] = deleted_companies
                    total_deleted += deleted_companies
                    data_types_reset.append("companies")
                except Exception as e:
                    errors.append(f"Failed to delete companies: {str(e)}")
            
            if reset_request.include_users:
                try:
                    # Delete non-admin users only
                    deleted_users = db.query(User).filter(
                        and_(
                            User.organization_id == organization_id,
                            User.is_super_admin == False,
                            User.role != "org_admin"
                        )
                    ).delete()
                    deletion_summary["users"] = deleted_users
                    total_deleted += deleted_users
                    data_types_reset.append("users")
                except Exception as e:
                    errors.append(f"Failed to delete users: {str(e)}")
            
            # Clean up notifications and OTP verifications
            try:
                deleted_notifications = db.query(EmailNotification).filter(
                    EmailNotification.organization_id == organization_id
                ).delete()
                deletion_summary["notifications"] = deleted_notifications
                total_deleted += deleted_notifications
                
                deleted_otps = db.query(OTPVerification).filter(
                    OTPVerification.email.in_(
                        db.query(User.email).filter(User.organization_id == organization_id)
                    )
                ).delete(synchronize_session=False)
                deletion_summary["otp_verifications"] = deleted_otps
                total_deleted += deleted_otps
                
            except Exception as e:
                errors.append(f"Failed to clean up notifications/OTPs: {str(e)}")
            
            # Reset organization settings if full reset
            if reset_request.reset_type == DataResetType.FULL_RESET:
                try:
                    organization.company_details_completed = False
                    data_types_reset.append("organization_settings")
                except Exception as e:
                    errors.append(f"Failed to reset organization settings: {str(e)}")
            
            db.commit()
            
            success = len(errors) == 0
            
            # Log the data reset operation
            AuditLogger.log_data_reset(
                db=db,
                admin_email=admin_user.email,
                admin_user_id=admin_user.id,
                organization_id=organization_id,
                success=success,
                ip_address=AuditLogger.get_client_ip(request) if request else None,
                user_agent=AuditLogger.get_user_agent(request) if request else None,
                reset_scope="ORGANIZATION",
                affected_organizations=[organization_id],
                details={
                    "reset_type": reset_request.reset_type,
                    "data_types_reset": data_types_reset,
                    "deletion_summary": deletion_summary,
                    "total_deleted": total_deleted,
                    "errors": errors
                }
            )
            
            logger.info(f"Organization {organization_id} data reset completed by {admin_user.email}")
            
            return OrganizationDataResetResponse(
                message=f"Data reset completed for organization {organization.name}",
                organization_id=organization_id,
                organization_name=organization.name,
                reset_type=reset_request.reset_type,
                data_types_reset=data_types_reset,
                total_records_deleted=total_deleted,
                deletion_summary=deletion_summary,
                success=success,
                errors=errors
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to reset organization {organization_id} data: {e}")
            
            # Log the failed operation
            AuditLogger.log_data_reset(
                db=db,
                admin_email=admin_user.email,
                admin_user_id=admin_user.id,
                organization_id=organization_id,
                success=False,
                error_message=str(e),
                ip_address=AuditLogger.get_client_ip(request) if request else None,
                user_agent=AuditLogger.get_user_agent(request) if request else None,
                reset_scope="ORGANIZATION",
                affected_organizations=[organization_id]
            )
            
            raise ValueError(f"Failed to reset organization data: {str(e)}")
    
    @staticmethod
    def reset_all_organizations_data(
        db: Session,
        admin_user: User,
        reset_request: DataResetRequest,
        request=None
    ) -> DataResetResponse:
        """
        Reset data for all organizations (super admin only)
        
        Args:
            db: Database session
            admin_user: Super admin user performing the reset
            reset_request: Reset configuration
            request: HTTP request for audit logging
            
        Returns:
            DataResetResponse: Result with summary of all resets
        """
        try:
            # Get all organizations
            organizations = db.query(Organization).all()
            if not organizations:
                raise ValueError("No organizations found")
            
            total_deleted = 0
            overall_deletion_summary = {}
            affected_organizations = []
            errors = []
            data_types_reset = []
            
            for org in organizations:
                try:
                    # Create individual reset request for each org
                    org_reset = ResetService.reset_organization_data(
                        db=db,
                        organization_id=org.id,
                        admin_user=admin_user,
                        reset_request=reset_request,
                        request=request
                    )
                    
                    affected_organizations.append(org.id)
                    total_deleted += org_reset.total_records_deleted
                    
                    # Merge deletion summaries
                    for key, value in org_reset.deletion_summary.items():
                        overall_deletion_summary[key] = overall_deletion_summary.get(key, 0) + value
                    
                    # Collect data types reset
                    data_types_reset.extend(org_reset.data_types_reset)
                    
                    if org_reset.errors:
                        errors.extend([f"Org {org.id}: {error}" for error in org_reset.errors])
                        
                except Exception as e:
                    errors.append(f"Failed to reset organization {org.id}: {str(e)}")
            
            # Remove duplicates from data_types_reset
            data_types_reset = list(set(data_types_reset))
            success = len(errors) == 0
            
            # Log the global data reset operation
            AuditLogger.log_data_reset(
                db=db,
                admin_email=admin_user.email,
                admin_user_id=admin_user.id,
                success=success,
                ip_address=AuditLogger.get_client_ip(request) if request else None,
                user_agent=AuditLogger.get_user_agent(request) if request else None,
                reset_scope="ALL_ORGANIZATIONS",
                affected_organizations=affected_organizations,
                details={
                    "reset_type": reset_request.reset_type,
                    "data_types_reset": data_types_reset,
                    "deletion_summary": overall_deletion_summary,
                    "total_deleted": total_deleted,
                    "organizations_affected_count": len(affected_organizations),
                    "errors": errors
                }
            )
            
            logger.info(f"Global data reset completed by {admin_user.email} - {len(affected_organizations)} organizations affected")
            
            return DataResetResponse(
                message=f"Data reset completed for all {len(affected_organizations)} organizations",
                scope=ResetScope.ALL_ORGANIZATIONS,
                reset_type=reset_request.reset_type,
                organizations_affected=affected_organizations,
                data_types_reset=data_types_reset,
                total_records_deleted=total_deleted,
                deletion_summary=overall_deletion_summary,
                success=success,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to reset all organizations data: {e}")
            
            # Log the failed operation
            AuditLogger.log_data_reset(
                db=db,
                admin_email=admin_user.email,
                admin_user_id=admin_user.id,
                success=False,
                error_message=str(e),
                ip_address=AuditLogger.get_client_ip(request) if request else None,
                user_agent=AuditLogger.get_user_agent(request) if request else None,
                reset_scope="ALL_ORGANIZATIONS"
            )
            
            raise ValueError(f"Failed to reset all organizations data: {str(e)}")
    
    @staticmethod
    def get_reset_preview(
        db: Session,
        organization_id: Optional[int],
        reset_request: DataResetRequest
    ) -> Dict[str, int]:
        """
        Get preview of what would be deleted without actually deleting
        
        Args:
            db: Database session
            organization_id: ID of organization (None for all orgs)
            reset_request: Reset configuration
            
        Returns:
            Dict with counts of records that would be deleted
        """
        preview = {}
        
        try:
            if organization_id:
                orgs_to_check = [organization_id]
            else:
                orgs_to_check = [org.id for org in db.query(Organization.id).all()]
            
            for org_id in orgs_to_check:
                if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_stock:
                    stock_count = db.query(Stock).filter(Stock.organization_id == org_id).count()
                    preview["stock"] = preview.get("stock", 0) + stock_count
                
                if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_products:
                    products_count = db.query(Product).filter(Product.organization_id == org_id).count()
                    preview["products"] = preview.get("products", 0) + products_count
                
                if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_customers:
                    customers_count = db.query(Customer).filter(Customer.organization_id == org_id).count()
                    preview["customers"] = preview.get("customers", 0) + customers_count
                
                if reset_request.reset_type == DataResetType.FULL_RESET or reset_request.include_vendors:
                    vendors_count = db.query(Vendor).filter(Vendor.organization_id == org_id).count()
                    preview["vendors"] = preview.get("vendors", 0) + vendors_count
                
                if reset_request.include_companies:
                    companies_count = db.query(Company).filter(Company.organization_id == org_id).count()
                    preview["companies"] = preview.get("companies", 0) + companies_count
                
                if reset_request.include_users:
                    users_count = db.query(User).filter(
                        and_(
                            User.organization_id == org_id,
                            User.is_super_admin == False,
                            User.role != "org_admin"
                        )
                    ).count()
                    preview["users"] = preview.get("users", 0) + users_count
            
            preview["total"] = sum(preview.values())
            return preview
            
        except Exception as e:
            logger.error(f"Failed to generate reset preview: {e}")
            return {"error": str(e)}
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