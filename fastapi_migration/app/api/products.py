from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Product
from app.schemas.base import ProductCreate, ProductUpdate, ProductInDB, BulkImportResponse
from app.services.excel_service import ProductExcelService, ExcelService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[ProductInDB])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products in current organization"""
    
    query = db.query(Product)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Product, org_id)
    
    if active_only:
        query = query.filter(Product.is_active == True)
    
    if search:
        search_filter = (
            Product.name.contains(search) |
            Product.hsn_code.contains(search) |
            Product.part_number.contains(search)
        )
        query = query.filter(search_filter)
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductInDB)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(product, current_user.organization_id)
    
    return product

@router.post("/", response_model=ProductInDB)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new product"""
    
    org_id = require_current_organization_id()
    
    # Check if product name already exists in organization
    existing_product = db.query(Product).filter(
        Product.name == product.name,
        Product.organization_id == org_id
    ).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this name already exists in organization"
        )
    
    # Create new product
    db_product = Product(
        organization_id=org_id,
        **product.dict()
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    logger.info(f"Product {product.name} created in org {org_id} by {current_user.email}")
    return db_product

@router.put("/{product_id}", response_model=ProductInDB)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update product"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(product, current_user.organization_id)
    
    # Check name uniqueness if being updated
    if product_update.name and product_update.name != product.name:
        existing_product = db.query(Product).filter(
            Product.name == product_update.name,
            Product.organization_id == product.organization_id
        ).first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this name already exists in organization"
            )
    
    # Update product
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    logger.info(f"Product {product.name} updated by {current_user.email}")
    return product

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete product (admin only)"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(product, current_user.organization_id)
    
    # TODO: Check if product has any associated transactions/vouchers
    # before allowing deletion
    
    db.delete(product)
    db.commit()
    
    logger.info(f"Product {product.name} deleted by {current_user.email}")
    return {"message": "Product deleted successfully"}

# Excel Import/Export/Template endpoints

@router.get("/template/excel")
async def download_products_template(
    current_user: User = Depends(get_current_active_user)
):
    """Download Excel template for products bulk import"""
    excel_data = ProductExcelService.create_template()
    return ExcelService.create_streaming_response(excel_data, "products_template.xlsx")

@router.get("/export/excel")
async def export_products_excel(
    skip: int = 0,
    limit: int = 1000,
    search: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export products to Excel"""
    
    # Get products using the same logic as the list endpoint
    query = db.query(Product)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Product, org_id)
    
    if active_only:
        query = query.filter(Product.is_active == True)
    
    if search:
        search_filter = (
            Product.name.contains(search) |
            Product.hsn_code.contains(search) |
            Product.part_number.contains(search)
        )
        query = query.filter(search_filter)
    
    products = query.offset(skip).limit(limit).all()
    
    # Convert to dict format for Excel export
    products_data = []
    for product in products:
        products_data.append({
            "name": product.name,
            "hsn_code": product.hsn_code or "",
            "part_number": product.part_number or "",
            "unit": product.unit,
            "unit_price": product.unit_price,
            "gst_rate": product.gst_rate,
            "is_gst_inclusive": product.is_gst_inclusive,
            "reorder_level": product.reorder_level,
            "description": product.description or "",
            "is_manufactured": product.is_manufactured,
        })
    
    excel_data = ProductExcelService.export_products(products_data)
    return ExcelService.create_streaming_response(excel_data, "products_export.xlsx")

@router.post("/import/excel", response_model=BulkImportResponse)
async def import_products_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import products from Excel file"""
    
    org_id = require_current_organization_id()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Parse Excel file
        records = await ExcelService.parse_excel_file(file, ProductExcelService.REQUIRED_COLUMNS)
        
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
                product_data = {
                    "name": record.get("Name", "").strip(),
                    "hsn_code": record.get("HSN Code", "").strip(),
                    "part_number": record.get("Part Number", "").strip(),
                    "unit": record.get("Unit", "").strip(),
                    "unit_price": float(record.get("Unit Price", 0)),
                    "gst_rate": float(record.get("GST Rate", 0)),
                    "is_gst_inclusive": str(record.get("Is GST Inclusive", "")).upper() in ["TRUE", "YES", "1"],
                    "reorder_level": int(float(record.get("Reorder Level", 0))),
                    "description": record.get("Description", "").strip(),
                    "is_manufactured": str(record.get("Is Manufactured", "")).upper() in ["TRUE", "YES", "1"],
                }
                
                # Validate required fields
                if not product_data["name"]:
                    errors.append(f"Row {i}: Name is required")
                    continue
                    
                if not product_data["unit"]:
                    errors.append(f"Row {i}: Unit is required")
                    continue
                
                # Check if product already exists
                existing_product = db.query(Product).filter(
                    Product.name == product_data["name"],
                    Product.organization_id == org_id
                ).first()
                
                if existing_product:
                    # Update existing product
                    for field, value in product_data.items():
                        setattr(existing_product, field, value)
                    updated_count += 1
                    logger.info(f"Updated product: {product_data['name']}")
                else:
                    # Create new product
                    new_product = Product(
                        organization_id=org_id,
                        **product_data
                    )
                    db.add(new_product)
                    created_count += 1
                    logger.info(f"Created product: {product_data['name']}")
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Row {i}: Invalid data format - {str(e)}")
                continue
            except Exception as e:
                errors.append(f"Row {i}: Error processing record - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Products import completed by {current_user.email}: "
                   f"{created_count} created, {updated_count} updated, {len(errors)} errors")
        
        return BulkImportResponse(
            message=f"Import completed successfully. {created_count} products created, {updated_count} updated.",
            total_processed=len(records),
            created=created_count,
            updated=updated_count,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing import: {str(e)}"
        )