from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Vendor
from app.schemas.base import VendorCreate, VendorUpdate, VendorInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[VendorInDB])
async def get_vendors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vendors in current organization"""
    
    query = db.query(Vendor)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Vendor, org_id)
    
    if active_only:
        query = query.filter(Vendor.is_active == True)
    
    if search:
        search_filter = (
            Vendor.name.contains(search) |
            Vendor.contact_number.contains(search) |
            Vendor.email.contains(search)
        )
        query = query.filter(search_filter)
    
    vendors = query.offset(skip).limit(limit).all()
    return vendors

@router.get("/{vendor_id}", response_model=VendorInDB)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vendor by ID"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(vendor, current_user.organization_id)
    
    return vendor

@router.post("/", response_model=VendorInDB)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new vendor"""
    
    org_id = require_current_organization_id()
    
    # Check if vendor name already exists in organization
    existing_vendor = db.query(Vendor).filter(
        Vendor.name == vendor.name,
        Vendor.organization_id == org_id
    ).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor with this name already exists in organization"
        )
    
    # Create new vendor
    db_vendor = Vendor(
        organization_id=org_id,
        **vendor.dict()
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Vendor {vendor.name} created in org {org_id} by {current_user.email}")
    return db_vendor

@router.put("/{vendor_id}", response_model=VendorInDB)
async def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update vendor"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(vendor, current_user.organization_id)
    
    # Check name uniqueness if being updated
    if vendor_update.name and vendor_update.name != vendor.name:
        existing_vendor = db.query(Vendor).filter(
            Vendor.name == vendor_update.name,
            Vendor.organization_id == vendor.organization_id
        ).first()
        if existing_vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor with this name already exists in organization"
            )
    
    # Update vendor
    for field, value in vendor_update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    
    logger.info(f"Vendor {vendor.name} updated by {current_user.email}")
    return vendor

@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete vendor (admin only)"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(vendor, current_user.organization_id)
    
    # TODO: Check if vendor has any associated transactions/vouchers
    # before allowing deletion
    
    db.delete(vendor)
    db.commit()
    
    logger.info(f"Vendor {vendor.name} deleted by {current_user.email}")
    return {"message": "Vendor deleted successfully"}
