from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User, Vendor
from app.schemas.base import VendorCreate, VendorUpdate, VendorInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[VendorInDB])
async def get_vendors(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all vendors"""
    query = db.query(Vendor)
    
    if active_only:
        query = query.filter(Vendor.is_active == True)
    
    if search:
        query = query.filter(
            Vendor.name.contains(search) |
            Vendor.contact_number.contains(search) |
            Vendor.email.contains(search)
        )
    
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
    return vendor

@router.post("/", response_model=VendorInDB)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new vendor"""
    # Check if vendor name already exists
    existing_vendor = db.query(Vendor).filter(Vendor.name == vendor.name).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor name already exists"
        )
    
    # Create new vendor
    db_vendor = Vendor(**vendor.dict())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Vendor {vendor.name} created by {current_user.email}")
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
    
    # Check name uniqueness if being updated
    if vendor_update.name and vendor_update.name != vendor.name:
        existing_vendor = db.query(Vendor).filter(Vendor.name == vendor_update.name).first()
        if existing_vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor name already exists"
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
    current_user: User = Depends(get_current_active_user)
):
    """Delete vendor (soft delete by setting inactive)"""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Soft delete - set as inactive
    vendor.is_active = False
    db.commit()
    
    logger.info(f"Vendor {vendor.name} deactivated by {current_user.email}")
    return {"message": "Vendor deactivated successfully"}