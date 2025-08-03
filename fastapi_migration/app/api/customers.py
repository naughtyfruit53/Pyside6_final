# Revised api.customers.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin
from app.models.base import User, Customer
from app.schemas.base import CustomerCreate, CustomerUpdate, CustomerInDB, BulkImportResponse
from app.services.excel_service import CustomerExcelService, ExcelService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[CustomerInDB])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customers in current organization"""
    
    query = db.query(Customer)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to an organization")
        query = TenantQueryMixin.filter_by_tenant(query, Customer, org_id)
    
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    if search:
        search_filter = (
            Customer.name.contains(search) |
            Customer.contact_number.contains(search) |
            Customer.email.contains(search)
        )
        query = query.filter(search_filter)
    
    customers = query.offset(skip).limit(limit).all()
    return customers

@router.get("/{customer_id}", response_model=CustomerInDB)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(customer, current_user.organization_id)
    
    return customer

@router.post("/", response_model=CustomerInDB)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new customer"""
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to an organization to create customers")
    
    # Check if customer name already exists in organization
    existing_customer = db.query(Customer).filter(
        Customer.name == customer.name,
        Customer.organization_id == org_id
    ).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this name already exists in organization"
        )
    
    # Create new customer
    db_customer = Customer(
        organization_id=org_id,
        **customer.dict()
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    logger.info(f"Customer {customer.name} created in org {org_id} by {current_user.email}")
    return db_customer

@router.put("/{customer_id}", response_model=CustomerInDB)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update customer"""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(customer, current_user.organization_id)
    
    # Check name uniqueness if being updated
    if customer_update.name and customer_update.name != customer.name:
        existing_customer = db.query(Customer).filter(
            Customer.name == customer_update.name,
            Customer.organization_id == customer.organization_id
        ).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this name already exists in organization"
            )
    
    # Update customer
    for field, value in customer_update.dict(exclude_unset=True).items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    
    logger.info(f"Customer {customer.name} updated by {current_user.email}")
    return customer

@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete customer (admin only)"""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(customer, current_user.organization_id)
    
    # TODO: Check if customer has any associated transactions/vouchers
    # before allowing deletion
    
    db.delete(customer)
    db.commit()
    
    logger.info(f"Customer {customer.name} deleted by {current_user.email}")
    return {"message": "Customer deleted successfully"}

# Excel Import/Export/Template endpoints

@router.get("/template/excel")
async def download_customers_template(
    current_user: User = Depends(get_current_active_user)
):
    """Download Excel template for customers bulk import"""
    excel_data = CustomerExcelService.create_template()
    return ExcelService.create_streaming_response(excel_data, "customers_template.xlsx")

@router.get("/export/excel")
async def export_customers_excel(
    skip: int = 0,
    limit: int = 1000,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export customers to Excel"""
    
    # Get customers using the same logic as the list endpoint
    query = db.query(Customer)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to an organization")
        query = TenantQueryMixin.filter_by_tenant(query, Customer, org_id)
    
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    if search:
        search_filter = (
            Customer.name.contains(search) |
            Customer.contact_number.contains(search) |
            Customer.email.contains(search)
        )
        query = query.filter(search_filter)
    
    customers = query.offset(skip).limit(limit).all()
    
    # Convert to dict format for Excel export
    customers_data = []
    for customer in customers:
        customers_data.append({
            "name": customer.name,
            "contact_number": customer.contact_number,
            "email": customer.email or "",
            "address1": customer.address1,
            "address2": customer.address2 or "",
            "city": customer.city,
            "state": customer.state,
            "pin_code": customer.pin_code,
            "state_code": customer.state_code,
            "gst_number": customer.gst_number or "",
            "pan_number": customer.pan_number or "",
        })
    
    excel_data = CustomerExcelService.export_customers(customers_data)
    return ExcelService.create_streaming_response(excel_data, "customers_export.xlsx")

@router.post("/import/excel", response_model=BulkImportResponse)
async def import_customers_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import customers from Excel file"""
    
    org_id = current_user.organization_id
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to an organization to import customers")
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Parse Excel file
        records = await ExcelService.parse_excel_file(file, CustomerExcelService.REQUIRED_COLUMNS)
        
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
                customer_data = {
                    "name": record.get("Name", "").strip(),
                    "contact_number": record.get("Contact Number", "").strip(),
                    "email": record.get("Email", "").strip() or None,
                    "address1": record.get("Address Line 1", "").strip(),
                    "address2": record.get("Address Line 2", "").strip() or None,
                    "city": record.get("City", "").strip(),
                    "state": record.get("State", "").strip(),
                    "pin_code": record.get("Pin Code", "").strip(),
                    "state_code": record.get("State Code", "").strip(),
                    "gst_number": record.get("GST Number", "").strip() or None,
                    "pan_number": record.get("PAN Number", "").strip() or None,
                }
                
                # Validate required fields
                required_fields = ["name", "contact_number", "address1", "city", "state", "pin_code", "state_code"]
                for field in required_fields:
                    if not customer_data[field]:
                        errors.append(f"Row {i}: {field.replace('_', ' ').title()} is required")
                        continue
                
                if errors and errors[-1].startswith(f"Row {i}:"):
                    continue
                
                # Check if customer already exists
                existing_customer = db.query(Customer).filter(
                    Customer.name == customer_data["name"],
                    Customer.organization_id == org_id
                ).first()
                
                if existing_customer:
                    # Update existing customer
                    for field, value in customer_data.items():
                        setattr(existing_customer, field, value)
                    updated_count += 1
                    logger.info(f"Updated customer: {customer_data['name']}")
                else:
                    # Create new customer
                    new_customer = Customer(
                        organization_id=org_id,
                        **customer_data
                    )
                    db.add(new_customer)
                    created_count += 1
                    logger.info(f"Created customer: {customer_data['name']}")
                    
            except Exception as e:
                errors.append(f"Row {i}: Error processing record - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Customers import completed by {current_user.email}: "
                   f"{created_count} created, {updated_count} updated, {len(errors)} errors")
        
        return BulkImportResponse(
            message=f"Import completed successfully. {created_count} customers created, {updated_count} updated.",
            total_processed=len(records),
            created=created_count,
            updated=updated_count,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing import: {str(e)}"
        )