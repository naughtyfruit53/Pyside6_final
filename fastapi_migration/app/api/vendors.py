from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.auth import (
    get_current_active_user, get_current_admin_user, 
    require_current_organization_id, validate_organization_access
)
from app.core.tenant import TenantQueryFilter
from app.models.base import User, Vendor
from app.schemas.base import VendorCreate, VendorUpdate, VendorInDB, BulkImportResponse
from app.services.excel_service import VendorExcelService, ExcelService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Vendor CRUD Endpoints ---

@router.get("/", response_model=List[VendorInDB])
async def get_vendors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get vendors with strict organization-level filtering"""
    # Platform user can specify org, regular users use their own
    if organization_id and getattr(current_user, 'is_platform_user', False):
        validate_organization_access(organization_id, current_user, db)
        target_org_id = organization_id
    else:
        target_org_id = require_current_organization_id(current_user)
    
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
    if organization_id and getattr(current_user, 'is_platform_user', False):
        validate_organization_access(organization_id, current_user, db)
        target_org_id = organization_id
    else:
        target_org_id = require_current_organization_id(current_user)
    
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
    target_org_id = require_current_organization_id(current_user)
    db_vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found in organization {target_org_id}"
        )
    update_data = vendor.dict(exclude_unset=True)
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
    current_user: User = Depends(get_current_admin_user)
):
    """Delete vendor with organization validation (admin only)"""
    target_org_id = require_current_organization_id(current_user)
    db_vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {vendor_id} not found in organization {target_org_id}"
        )
    # Soft delete (recommended): mark as inactive
    db_vendor.is_active = False
    db.commit()
    logger.info(f"Deleted vendor {db_vendor.name} (ID: {db_vendor.id}) in organization {db_vendor.organization_id}")
    return {"message": f"Vendor {vendor_id} deleted successfully"}

# --- Search for Dropdown/Autocomplete ---

@router.post("/search", response_model=List[VendorInDB])
async def search_vendors_for_dropdown(
    search_term: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search vendors for dropdown/autocomplete with organization filtering"""
    target_org_id = require_current_organization_id(current_user)
    vendors = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, target_org_id, current_user
    ).filter(
        Vendor.is_active == True,
        Vendor.name.contains(search_term)
    ).limit(limit).all()
    return vendors

# --- Excel Import/Export/Template endpoints ---

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
    target_org_id = require_current_organization_id(current_user)
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
    org_id = require_current_organization_id(current_user)
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    try:
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
                        break
                if errors and errors[-1].startswith(f"Row {i}:"):
                    continue
                # Check if vendor already exists
                existing_vendor = db.query(Vendor).filter(
                    Vendor.name == vendor_data["name"],
                    Vendor.organization_id == org_id
                ).first()
                if existing_vendor:
                    for field, value in vendor_data.items():
                        setattr(existing_vendor, field, value)
                    updated_count += 1
                    logger.info(f"Updated vendor: {vendor_data['name']}")
                else:
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