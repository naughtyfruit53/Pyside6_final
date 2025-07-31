"""
Organization management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.tenant import require_organization, TenantContext
from app.models.base import Organization, User
from app.schemas.base import (
    OrganizationCreate, OrganizationUpdate, OrganizationInDB,
    OrganizationLicenseCreate, OrganizationLicenseResponse,
    UserCreate, UserInDB, UserRole
)
from app.api.auth import get_current_user, get_current_active_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/license/create", response_model=OrganizationLicenseResponse, status_code=status.HTTP_201_CREATED)
async def create_organization_license(
    license_data: OrganizationLicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create organization license with auto-generated details (Super admin only)"""
    # Only super admins can create organization licenses
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create organization licenses"
        )
    
    try:
        import secrets
        import string
        import re
        
        # Generate subdomain from organization name
        subdomain_base = re.sub(r'[^a-zA-Z0-9]', '', license_data.organization_name.lower())
        subdomain_base = subdomain_base[:15] if len(subdomain_base) > 15 else subdomain_base
        
        # Ensure subdomain is unique
        counter = 0
        subdomain = subdomain_base
        while db.query(Organization).filter(Organization.subdomain == subdomain).first():
            counter += 1
            subdomain = f"{subdomain_base}{counter}"
        
        # Generate temporary password
        alphabet = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Check if organization name already exists
        existing_org = db.query(Organization).filter(
            Organization.name == license_data.organization_name
        ).first()
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )
        
        # Check if superadmin email already exists
        existing_user = db.query(User).filter(
            User.email == license_data.superadmin_email
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists in the system"
            )
        
        # Create organization with minimal required details
        org = Organization(
            name=license_data.organization_name,
            subdomain=subdomain,
            business_type="Other",
            primary_email=license_data.superadmin_email,
            primary_phone="+91-0000000000",  # Placeholder
            address1="To be updated",  # Placeholder
            city="To be updated",  # Placeholder
            state="To be updated",  # Placeholder
            pin_code="000000",  # Placeholder
            status="trial",
            plan_type="trial",
            max_users=5,
            storage_limit_gb=1,
            features={}
        )
        
        db.add(org)
        db.flush()  # Get the organization ID
        
        # Create superadmin user
        admin_user = User(
            organization_id=org.id,
            email=license_data.superadmin_email,
            username=license_data.superadmin_email.split("@")[0],
            hashed_password=get_password_hash(temp_password),
            full_name="Administrator",
            role=UserRole.ORG_ADMIN,
            is_active=True,
            must_change_password=True  # Force password change on first login
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(org)
        
        # TODO: Send confirmation email with login details
        # email_service.send_organization_license_created_email(
        #     license_data.superadmin_email,
        #     license_data.organization_name,
        #     subdomain,
        #     temp_password
        # )
        
        logger.info(f"Created organization license {org.name} with admin {admin_user.email}")
        
        return OrganizationLicenseResponse(
            message="Organization license created successfully",
            organization_id=org.id,
            organization_name=org.name,
            superadmin_email=license_data.superadmin_email,
            subdomain=subdomain,
            temp_password=temp_password
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating organization license: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating organization license"
        )

@router.post("/", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organization (Super admin only)"""
    # Only super admins can create organizations
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create organizations"
        )
    
    # Check if subdomain already exists
    existing_org = db.query(Organization).filter(
        Organization.subdomain == org_data.subdomain.lower()
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already exists"
        )
    
    # Check if organization name already exists
    existing_name = db.query(Organization).filter(
        Organization.name == org_data.name
    ).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already exists"
        )
    
    try:
        # Create organization
        org = Organization(
            name=org_data.name,
            subdomain=org_data.subdomain.lower(),
            business_type=org_data.business_type,
            industry=org_data.industry,
            website=org_data.website,
            description=org_data.description,
            primary_email=org_data.primary_email,
            primary_phone=org_data.primary_phone,
            address1=org_data.address1,
            address2=org_data.address2,
            city=org_data.city,
            state=org_data.state,
            pin_code=org_data.pin_code,
            country=org_data.country,
            gst_number=org_data.gst_number,
            pan_number=org_data.pan_number,
            cin_number=org_data.cin_number,
            status="trial",
            plan_type="trial",
            max_users=5,
            storage_limit_gb=1,
            features={}
        )
        
        db.add(org)
        db.flush()  # Get the organization ID
        
        # Create organization admin user
        admin_user = User(
            organization_id=org.id,
            email=org_data.admin_email,
            username=org_data.admin_email.split("@")[0],
            hashed_password=get_password_hash(org_data.admin_password),
            full_name=org_data.admin_full_name,
            role=UserRole.ORG_ADMIN,
            is_active=True,
            must_change_password=False
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(org)
        
        logger.info(f"Created organization {org.name} with admin {admin_user.email}")
        return org
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating organization"
        )

@router.get("/", response_model=List[OrganizationInDB])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List organizations (Super admin only)"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can list all organizations"
        )
    
    query = db.query(Organization)
    
    if status_filter:
        query = query.filter(Organization.status == status_filter)
    
    organizations = query.offset(skip).limit(limit).all()
    return organizations

@router.get("/current", response_model=OrganizationInDB)
async def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's organization"""
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org

@router.get("/{org_id}", response_model=OrganizationInDB)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization by ID"""
    # Super admins can access any organization
    # Regular users can only access their own organization
    if not current_user.is_super_admin and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org

@router.put("/{org_id}", response_model=OrganizationInDB)
async def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update organization"""
    # Super admins can update any organization
    # Org admins can only update their own organization
    if not current_user.is_super_admin:
        if current_user.organization_id != org_id or current_user.role not in [UserRole.ORG_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this organization"
            )
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    try:
        # Update fields
        update_data = org_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(org, field, value)
        
        db.commit()
        db.refresh(org)
        
        logger.info(f"Updated organization {org.name} by user {current_user.email}")
        return org
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating organization"
        )

@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete organization (Super admin only)"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can delete organizations"
        )
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check if organization has users
    user_count = db.query(User).filter(User.organization_id == org_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete organization with existing users"
        )
    
    try:
        db.delete(org)
        db.commit()
        
        logger.info(f"Deleted organization {org.name} by user {current_user.email}")
        return {"message": "Organization deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting organization"
        )

@router.get("/{org_id}/users", response_model=List[UserInDB])
async def list_organization_users(
    org_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List users in organization"""
    # Check access permissions
    if not current_user.is_super_admin and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    if not current_user.is_super_admin and current_user.role not in [UserRole.ORG_ADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to list users"
        )
    
    query = db.query(User).filter(User.organization_id == org_id)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/subdomain/{subdomain}", response_model=OrganizationInDB)
async def get_organization_by_subdomain(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Get organization by subdomain (public endpoint for tenant identification)"""
    org = db.query(Organization).filter(
        Organization.subdomain == subdomain.lower(),
        Organization.status == "active"
    ).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org
@router.post("/reset-data", status_code=status.HTTP_200_OK)
async def reset_organization_data(
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset organization data"""
    try:
        # Determine which organization(s) to reset
        if current_user.is_super_admin:
            # Super admin can reset all data or specific organization
            if organization_id:
                # Reset specific organization
                org = db.query(Organization).filter(Organization.id == organization_id).first()
                if not org:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found"
                    )
                reset_organization_tables(db, organization_id)
                logger.info(f"Super admin {current_user.email} reset data for organization {org.name}")
                return {"message": f"Data reset successfully for organization: {org.name}"}
            else:
                # Reset all organizations
                reset_all_data(db)
                logger.info(f"Super admin {current_user.email} reset all data")
                return {"message": "All data reset successfully"}
        
        elif current_user.role in [UserRole.ORG_ADMIN]:
            # Organization admin can only reset their own organization's data
            if not current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No organization associated with user"
                )
            
            org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
            reset_organization_tables(db, current_user.organization_id)
            logger.info(f"Org admin {current_user.email} reset data for their organization {org.name}")
            return {"message": f"Data reset successfully for your organization: {org.name}"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Only organization administrators and super administrators can reset data."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting data"
        )

def reset_organization_tables(db: Session, org_id: int):
    """Reset data for a specific organization, preserving table structure"""
    from app.models.base import Company, Vendor, Customer, Product, Stock, AuditLog, EmailNotification, PaymentTerm
    
    # Delete data for the organization (preserves table structure)
    db.query(EmailNotification).filter(EmailNotification.organization_id == org_id).delete()
    db.query(AuditLog).filter(AuditLog.organization_id == org_id).delete()  
    db.query(Stock).filter(Stock.organization_id == org_id).delete()
    db.query(Product).filter(Product.organization_id == org_id).delete()
    db.query(PaymentTerm).filter(PaymentTerm.organization_id == org_id).delete()
    db.query(Customer).filter(Customer.organization_id == org_id).delete()
    db.query(Vendor).filter(Vendor.organization_id == org_id).delete()
    db.query(Company).filter(Company.organization_id == org_id).delete()
    
    # Reset organization flags
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        org.company_details_completed = False
    
    db.commit()


@router.post("/reset-data")
async def reset_organization_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reset organization data (Organization Admin) or all data (Super Admin)"""
    from app.services.reset_service import ResetService
    
    try:
        if current_user.is_super_admin:
            # Super admin can reset all data
            result = ResetService.reset_all_data(db)
            return {
                "message": "All system data has been reset successfully",
                "details": result["deleted"]
            }
        elif current_user.role in ["org_admin", "admin"] and current_user.organization_id:
            # Organization admin can reset their organization data
            result = ResetService.reset_organization_data(db, current_user.organization_id)
            return {
                "message": "Organization data has been reset successfully", 
                "details": result["deleted"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to reset data"
            )
    except Exception as e:
        logger.error(f"Error resetting data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset data. Please try again."
        )


def reset_all_data(db: Session):
    """Reset all data except super admin user and organization structures"""
    from app.models.base import Company, Vendor, Customer, Product, Stock, AuditLog, EmailNotification, PaymentTerm
    
    # Delete all business data (preserves table structure)
    db.query(EmailNotification).delete()
    db.query(AuditLog).delete()
    db.query(Stock).delete()
    db.query(Product).delete()
    db.query(PaymentTerm).delete()
    db.query(Customer).delete()
    db.query(Vendor).delete()
    db.query(Company).delete()
    
    # Delete non-super-admin users and organizations
    db.query(User).filter(User.is_super_admin == False).delete()
    db.query(Organization).delete()
    db.commit()
    
    db.commit()