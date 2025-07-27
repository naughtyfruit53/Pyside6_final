from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Company
from app.schemas.base import CompanyCreate, CompanyUpdate, CompanyInDB, UserRole
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[CompanyInDB])
async def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get companies in current organization"""
    
    if current_user.is_super_admin:
        # Super admin can see all companies across organizations
        companies = db.query(Company).all()
    else:
        # Regular users see only companies in their organization
        org_id = require_current_organization_id()
        query = db.query(Company)
        companies = TenantQueryMixin.filter_by_tenant(query, Company, org_id).all()
    
    return companies

@router.get("/current", response_model=CompanyInDB)
async def get_current_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current organization's company details"""
    
    if current_user.is_super_admin:
        # Super admin needs to specify organization
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super admin must specify organization ID"
        )
    
    org_id = require_current_organization_id()
    company = db.query(Company).filter(Company.organization_id == org_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company details not found. Please set up company information."
        )
    return company

@router.get("/{company_id}", response_model=CompanyInDB)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get company by ID"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    return company

@router.post("/", response_model=CompanyInDB)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create company details for current organization"""
    
    org_id = require_current_organization_id()
    
    # Check if company already exists for this organization
    existing_company = db.query(Company).filter(Company.organization_id == org_id).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company details already exist for this organization. Use update endpoint instead."
        )
    
    # Create new company
    db_company = Company(
        organization_id=org_id,
        **company.dict()
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    logger.info(f"Company {company.name} created for org {org_id} by {current_user.email}")
    return db_company

@router.put("/{company_id}", response_model=CompanyInDB)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update company details"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    # Update company
    for field, value in company_update.dict(exclude_unset=True).items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    logger.info(f"Company {company.name} updated by {current_user.email}")
    return company

@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete company (admin only)"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    db.delete(company)
    db.commit()
    
    logger.info(f"Company {company.name} deleted by {current_user.email}")
    return {"message": "Company deleted successfully"}