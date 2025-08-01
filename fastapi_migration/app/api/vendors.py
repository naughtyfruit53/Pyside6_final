from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import (
    get_current_active_user, get_current_admin_user, 
    require_current_organization_id, validate_organization_access,
    get_tenant_db_session
)
from app.core.tenant import TenantQueryFilter, TenantContext
from app.models.base import User, Vendor
from app.schemas.base import VendorCreate, VendorUpdate, VendorInDB, BulkImportResponse
from app.services.excel_service import VendorExcelService, ExcelService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[VendorInDB])
async def get_vendors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    organization_id: Optional[int] = None,  # Allow platform users to specify org
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vendors with strict organization-level filtering"""
    
    # Validate organization access for platform users
    if organization_id and getattr(current_user, 'is_platform_user', False):
        validate_organization_access(organization_id, current_user, db)
        target_org_id = organization_id
    else:
        # Regular users use their organization
        target_org_id = require_current_organization_id(current_user)
    
    # Create tenant-scoped query
    query = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    )
    
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
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vendor by ID with organization validation"""
    
    # Validate organization access
    if organization_id and getattr(current_user, 'is_platform_user', False):
        validate_organization_access(organization_id, current_user, db)
        target_org_id = organization_id
    else:
        target_org_id = require_current_organization_id(current_user)
    
    # Find vendor with organization filter
    vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(Vendor.id == vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found in organization {target_org_id}"
        )
    
    return vendor

@router.post("/", response_model=VendorInDB)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new vendor with organization validation"""
    
    # Validate and set organization_id
    vendor_data = vendor.dict()
    vendor_data = TenantQueryFilter.validate_organization_data(vendor_data, current_user)
    
    # Check for duplicate vendor name in organization
    existing_vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, vendor_data['organization_id'], current_user
    ).filter(Vendor.name == vendor_data['name']).first()
    
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with name '{vendor_data['name']}' already exists in this organization"
        )
    
    # Create vendor
    db_vendor = Vendor(**vendor_data)
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Created vendor {db_vendor.name} (ID: {db_vendor.id}) in organization {db_vendor.organization_id}")
    return db_vendor

@router.put("/{vendor_id}", response_model=VendorInDB)
async def update_vendor(
    vendor_id: int,
    vendor: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update vendor with organization validation"""
    
    # Get target organization
    target_org_id = require_current_organization_id(current_user)
    
    # Find existing vendor
    db_vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(Vendor.id == vendor_id).first()
    
    if not db_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found in organization {target_org_id}"
        )
    
    # Update vendor
    update_data = vendor.dict(exclude_unset=True)
    
    # Check for duplicate name if name is being updated
    if 'name' in update_data and update_data['name'] != db_vendor.name:
        existing_vendor = TenantQueryFilter.apply_organization_filter(
            db.query(Vendor), Vendor, target_org_id, current_user
        ).filter(
            Vendor.name == update_data['name'],
            Vendor.id != vendor_id
        ).first()
        
        if existing_vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with name '{update_data['name']}' already exists in this organization"
            )
    
    for field, value in update_data.items():
        setattr(db_vendor, field, value)
    
    db.commit()
    db.refresh(db_vendor)
    
    logger.info(f"Updated vendor {db_vendor.name} (ID: {db_vendor.id}) in organization {db_vendor.organization_id}")
    return db_vendor

@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)  # Require admin for deletion
):
    """Delete vendor with organization validation"""
    
    # Get target organization
    target_org_id = require_current_organization_id(current_user)
    
    # Find existing vendor
    db_vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(Vendor.id == vendor_id).first()
    
    if not db_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found in organization {target_org_id}"
        )
    
    # Soft delete by marking inactive
    db_vendor.is_active = False
    db.commit()
    
    logger.info(f"Deleted vendor {db_vendor.name} (ID: {db_vendor.id}) in organization {db_vendor.organization_id}")
    return {"message": f"Vendor {vendor_id} deleted successfully"}

@router.post("/search", response_model=List[VendorInDB])
async def search_vendors_for_dropdown(
    search_term: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search vendors for dropdown/autocomplete with organization filtering"""
    
    # Get target organization
    target_org_id = require_current_organization_id(current_user)
    
    # Search active vendors
    vendors = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(
        Vendor.is_active == True,
        Vendor.name.contains(search_term)
    ).limit(limit).all()
    
    return vendors
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

# Excel Import/Export/Template endpoints

@router.get("/template/excel")
async def download_vendors_template(
    current_user: User = Depends(get_current_active_user)
):
    """Download Excel template for vendors bulk import"""
    excel_data = VendorExcelService.create_template()
    return ExcelService.create_streaming_response(excel_data, "vendors_template.xlsx")

@router.get("/export/excel")
async def export_vendors_excel(
    skip: int = 0,
    limit: int = 1000,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export vendors to Excel"""
    
    # Get vendors using the same logic as the list endpoint
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
    
    # Convert to dict format for Excel export
    vendors_data = []
    for vendor in vendors:
        vendors_data.append({
            "name": vendor.name,
            "contact_number": vendor.contact_number,
            "email": vendor.email or "",
            "address1": vendor.address1,
            "address2": vendor.address2 or "",
            "city": vendor.city,
            "state": vendor.state,
            "pin_code": vendor.pin_code,
            "state_code": vendor.state_code,
            "gst_number": vendor.gst_number or "",
            "pan_number": vendor.pan_number or "",
        })
    
    excel_data = VendorExcelService.export_vendors(vendors_data)
    return ExcelService.create_streaming_response(excel_data, "vendors_export.xlsx")

@router.post("/import/excel", response_model=BulkImportResponse)
async def import_vendors_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import vendors from Excel file"""
    
    org_id = require_current_organization_id()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Parse Excel file
        records = await ExcelService.parse_excel_file(file, VendorExcelService.REQUIRED_COLUMNS)
        
        if not records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data found in Excel file"
            )
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for i, record in enumerate(records, 1):
            try:
                # Map Excel columns to model fields
                vendor_data = {
                    "name": record.get("name", "").strip(),
                    "contact_number": record.get("contact_number", "").strip(),
                    "email": record.get("email", "").strip() or None,
                    "address1": record.get("address_line_1", "").strip(),
                    "address2": record.get("address_line_2", "").strip() or None,
                    "city": record.get("city", "").strip(),
                    "state": record.get("state", "").strip(),
                    "pin_code": record.get("pin_code", "").strip(),
                    "state_code": record.get("state_code", "").strip(),
                    "gst_number": record.get("gst_number", "").strip() or None,
                    "pan_number": record.get("pan_number", "").strip() or None,
                }
                
                # Validate required fields
                required_fields = ["name", "contact_number", "address1", "city", "state", "pin_code", "state_code"]
                for field in required_fields:
                    if not vendor_data[field]:
                        errors.append(f"Row {i}: {field.replace('_', ' ').title()} is required")
                        continue
                
                if errors and errors[-1].startswith(f"Row {i}:"):
                    continue
                
                # Check if vendor already exists
                existing_vendor = db.query(Vendor).filter(
                    Vendor.name == vendor_data["name"],
                    Vendor.organization_id == org_id
                ).first()
                
                if existing_vendor:
                    # Update existing vendor
                    for field, value in vendor_data.items():
                        setattr(existing_vendor, field, value)
                    updated_count += 1
                    logger.info(f"Updated vendor: {vendor_data['name']}")
                else:
                    # Create new vendor
                    new_vendor = Vendor(
                        organization_id=org_id,
                        **vendor_data
                    )
                    db.add(new_vendor)
                    created_count += 1
                    logger.info(f"Created vendor: {vendor_data['name']}")
                    
            except Exception as e:
                errors.append(f"Row {i}: Error processing record - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Vendors import completed by {current_user.email}: "
                   f"{created_count} created, {updated_count} updated, {len(errors)} errors")
        
        return BulkImportResponse(
            message=f"Import completed successfully. {created_count} vendors created, {updated_count} updated.",
            total_processed=len(records),
            created=created_count,
            updated=updated_count,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing import: {str(e)}"
        )