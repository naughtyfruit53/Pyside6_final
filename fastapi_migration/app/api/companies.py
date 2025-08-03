from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user, get_current_admin_user, require_current_organization_id
from app.core.tenant import TenantQueryMixin
from app.models.base import User, Company, Organization
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyInDB, CompanyResponse, CompanyErrorResponse
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
        companies = db.query(Company).all()
    else:
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
    
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    return company

@router.post("/", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create company details for current organization with enhanced validation"""
    
    org_id = require_current_organization_id()
    
    # Check if company already exists for this organization
    existing_company = db.query(Company).filter(Company.organization_id == org_id).first()
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company details already exist for this organization. Use update endpoint instead."
        )
    
    try:
        db_company = Company(
            organization_id=org_id,
            **company.model_dump()
        )
        db.add(db_company)
        
        # Mark organization as having completed company details
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            org.company_details_completed = True
        
        db.commit()
        db.refresh(db_company)
        
        logger.info(f"Company {company.name} created for org {org_id} by {current_user.email}")
        return db_company
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company. Please try again."
        )

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update company details with enhanced validation"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    try:
        for field, value in company_update.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        
        db.commit()
        db.refresh(company)
        
        logger.info(f"Company {company.name} updated by {current_user.email}")
        return company
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company. Please try again."
        )

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
    
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(company, current_user.organization_id)
    
    db.delete(company)
    db.commit()
    
    logger.info(f"Company {company.name} deleted by {current_user.email}")
    return {"message": "Company deleted successfully"}