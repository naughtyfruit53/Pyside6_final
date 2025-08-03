# Revised api/stock.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Stock, Product
from app.schemas.stock import (
    StockCreate, StockUpdate, StockInDB, StockWithProduct,
    BulkImportResponse, BulkImportError, StockAdjustment, StockAdjustmentResponse
)
from app.schemas.base import ProductCreate
from app.utils.excel_import import StockExcelImporter
from app.services.excel_service import StockExcelService, ExcelService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[StockWithProduct])
async def get_stock(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get stock information with product details"""
    query = db.query(Stock, Product).join(Product)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Stock, org_id)
    
    if product_id:
        query = query.filter(Stock.product_id == product_id)
    
    if low_stock_only:
        # Filter for products where stock quantity <= reorder level
        query = query.filter(Stock.quantity <= Product.reorder_level)
    
    stock_product_pairs = query.offset(skip).limit(limit).all()
    
    # Transform the results to include product information
    result = []
    for stock, product in stock_product_pairs:
        stock_with_product = StockWithProduct(
            id=stock.id,
            organization_id=stock.organization_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            unit=stock.unit,
            location=stock.location,
            last_updated=stock.last_updated,
            product_name=product.name,
            product_hsn_code=product.hsn_code,
            product_part_number=product.part_number,
            unit_price=product.unit_price,
            reorder_level=product.reorder_level
        )
        result.append(stock_with_product)
    
    return result

@router.get("/low-stock", response_model=List[StockWithProduct])
async def get_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with low stock (below reorder level) with product details"""
    query = db.query(Stock, Product).join(Product).filter(
        Stock.quantity <= Product.reorder_level
    )
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Stock, org_id)
    
    stock_product_pairs = query.all()
    
    # Transform the results to include product information
    result = []
    for stock, product in stock_product_pairs:
        stock_with_product = StockWithProduct(
            id=stock.id,
            organization_id=stock.organization_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            unit=stock.unit,
            location=stock.location,
            last_updated=stock.last_updated,
            product_name=product.name,
            product_hsn_code=product.hsn_code,
            product_part_number=product.part_number,
            unit_price=product.unit_price,
            reorder_level=product.reorder_level
        )
        result.append(stock_with_product)
    
    return result

@router.get("/product/{product_id}", response_model=StockInDB)
async def get_product_stock(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get stock for specific product"""
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    
    if not stock:
        # Return zero stock if no record exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Ensure tenant access for non-super-admin users
        if not current_user.is_super_admin:
            TenantQueryMixin.ensure_tenant_access(product, current_user.organization_id)
        
        return StockInDB(
            id=0,
            organization_id=product.organization_id,
            product_id=product_id,
            quantity=0.0,
            unit=product.unit,
            location="",
            last_updated=product.created_at
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(stock, current_user.organization_id)
    
    return stock

@router.post("/", response_model=StockInDB)
async def create_stock_entry(
    stock: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new stock entry"""
    org_id = require_current_organization_id()
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == stock.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Ensure tenant access for non-super-admin users
    if not current_user.is_super_admin:
        TenantQueryMixin.ensure_tenant_access(product, current_user.organization_id)
    
    # Check if stock entry already exists
    existing_stock = db.query(Stock).filter(
        Stock.product_id == stock.product_id,
        Stock.organization_id == org_id
    ).first()
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock entry already exists for this product. Use update endpoint."
        )
    
    # Create new stock entry
    db_stock = Stock(
        organization_id=org_id,
        **stock.dict()
    )
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    
    logger.info(f"Stock entry created for product {product.name} by {current_user.email}")
    return db_stock

@router.put("/product/{product_id}", response_model=StockInDB)
async def update_stock(
    product_id: int,
    stock_update: StockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update stock for a product"""
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    
    if not stock:
        # Create new stock entry if doesn't exist
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        stock = Stock(
            product_id=product_id,
            quantity=stock_update.quantity or 0.0,
            unit=stock_update.unit or product.unit,
            location=stock_update.location or ""
        )
        db.add(stock)
    else:
        # Update existing stock
        for field, value in stock_update.dict(exclude_unset=True).items():
            setattr(stock, field, value)
    
    db.commit()
    db.refresh(stock)
    
    logger.info(f"Stock updated for product ID {product_id} by {current_user.email}")
    return stock

@router.post("/adjust/{product_id}", response_model=StockAdjustmentResponse)
async def adjust_stock(
    product_id: int,
    adjustment: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enhanced stock quantity adjustment with detailed response"""
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    
    if not stock:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Create new stock entry with the adjustment
        previous_quantity = 0.0
        new_quantity = max(0, adjustment.quantity_change)
        
        stock = Stock(
            product_id=product_id,
            quantity=new_quantity,
            unit=product.unit,
            location=""
        )
        db.add(stock)
    else:
        # Adjust existing stock
        previous_quantity = stock.quantity
        new_quantity = stock.quantity + adjustment.quantity_change
        
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for this adjustment. Current: {previous_quantity}, Requested change: {adjustment.quantity_change}"
            )
        stock.quantity = new_quantity
    
    try:
        db.commit()
        db.refresh(stock)
        
        logger.info(f"Stock adjusted for product ID {product_id}: {adjustment.quantity_change:+.2f} - {adjustment.reason} by {current_user.email}")
        
        return StockAdjustmentResponse(
            message=f"Stock adjusted successfully. {adjustment.reason}",
            previous_quantity=previous_quantity,
            quantity_change=adjustment.quantity_change,
            new_quantity=new_quantity
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adjusting stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to adjust stock. Please try again."
        )

@router.post("/bulk", response_model=BulkImportResponse)
async def bulk_import_stock(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enhanced bulk import stock entries from Excel file with comprehensive validation"""
    org_id = require_current_organization_id()
    start_time = datetime.utcnow()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Parse Excel file using existing service
        records = await ExcelService.parse_excel_file(file, StockExcelService.REQUIRED_COLUMNS)
        
        if not records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data found in Excel file"
            )
        
        created_products = 0
        created_stocks = 0
        updated_stocks = 0
        skipped_records = 0
        detailed_errors = []
        warnings = []
        simple_errors = []
        
        for i, record in enumerate(records, 1):
            try:
                # Extract product and stock data with enhanced validation
                product_name = str(record.get("product_name", "")).strip()
                unit = str(record.get("unit", "")).strip()
                
                # Enhanced validation for required fields
                if not product_name:
                    detailed_errors.append(BulkImportError(
                        row=i,
                        field="product_name",
                        value="",
                        error="Product Name is required and cannot be empty",
                        error_code="REQUIRED_FIELD_MISSING"
                    ))
                    simple_errors.append(f"Row {i}: Product Name is required and cannot be empty")
                    skipped_records += 1
                    continue
                    
                if not unit:
                    detailed_errors.append(BulkImportError(
                        row=i,
                        field="unit",
                        value="",
                        error="Unit is required and cannot be empty",
                        error_code="REQUIRED_FIELD_MISSING"
                    ))
                    simple_errors.append(f"Row {i}: Unit is required and cannot be empty")
                    skipped_records += 1
                    continue
                
                # Enhanced quantity validation
                try:
                    quantity = float(record.get("quantity", 0))
                    if quantity < 0:
                        detailed_errors.append(BulkImportError(
                            row=i,
                            field="quantity",
                            value=str(record.get("quantity")),
                            error="Quantity cannot be negative",
                            error_code="INVALID_VALUE"
                        ))
                        simple_errors.append(f"Row {i}: Quantity cannot be negative")
                        skipped_records += 1
                        continue
                except (ValueError, TypeError):
                    detailed_errors.append(BulkImportError(
                        row=i,
                        field="quantity",
                        value=str(record.get("quantity")),
                        error=f"Invalid quantity value: {record.get('quantity')}",
                        error_code="INVALID_DATA_TYPE"
                    ))
                    simple_errors.append(f"Row {i}: Invalid data format - could not convert string to float: '{record.get('quantity')}'")
                    skipped_records += 1
                    continue
                
                # Log record details for debugging
                logger.debug(f"Processing row {i}: product_name={product_name}, unit={unit}, quantity={quantity}")
                
                # Check if product exists by name
                product = db.query(Product).filter(
                    Product.name == product_name,
                    Product.organization_id == org_id
                ).first()
                
                if not product:
                    # Create new product if not exists with enhanced validation
                    try:
                        # Validate and clean optional fields
                        hsn_code = str(record.get("hsn_code", "")).strip() or None
                        part_number = str(record.get("part_number", "")).strip() or None
                        
                        # Validate numeric fields
                        try:
                            unit_price = float(record.get("unit_price", 0))
                            if unit_price < 0:
                                warnings.append(f"Row {i}: Unit price is negative for '{product_name}', setting to 0")
                                unit_price = 0.0
                        except (ValueError, TypeError):
                            unit_price = 0.0
                            warnings.append(f"Row {i}: Invalid unit price for '{product_name}', setting to 0")
                        
                        try:
                            gst_rate = float(record.get("gst_rate", 18.0))
                            if gst_rate < 0 or gst_rate > 100:
                                warnings.append(f"Row {i}: Invalid GST rate for '{product_name}', setting to 18%")
                                gst_rate = 18.0
                        except (ValueError, TypeError):
                            gst_rate = 18.0
                            warnings.append(f"Row {i}: Invalid GST rate for '{product_name}', setting to 18%")
                        
                        try:
                            reorder_level = int(float(record.get("reorder_level", 10)))
                            if reorder_level < 0:
                                reorder_level = 10
                                warnings.append(f"Row {i}: Invalid reorder level for '{product_name}', setting to 10")
                        except (ValueError, TypeError):
                            reorder_level = 10
                            warnings.append(f"Row {i}: Invalid reorder level for '{product_name}', setting to 10")
                        
                        product_data = {
                            "name": product_name,
                            "hsn_code": hsn_code,
                            "part_number": part_number,
                            "unit": unit.upper(),
                            "unit_price": unit_price,
                            "gst_rate": gst_rate,
                            "reorder_level": reorder_level,
                            "is_active": True
                        }
                        
                        new_product = Product(
                            organization_id=org_id,
                            **product_data
                        )
                        db.add(new_product)
                        db.flush()  # Get the new product ID
                        product = new_product
                        created_products += 1
                        logger.info(f"Created new product: {product_name}")
                        
                    except Exception as e:
                        detailed_errors.append(BulkImportError(
                            row=i,
                            field="product_creation",
                            value=product_name,
                            error=f"Failed to create product: {str(e)}",
                            error_code="PRODUCT_CREATION_FAILED"
                        ))
                        simple_errors.append(f"Row {i}: Invalid product data - {str(e)}")
                        logger.error(f"Row {i}: Failed to create product - {str(e)}")
                        skipped_records += 1
                        continue
                
                # Handle stock with enhanced validation
                stock = db.query(Stock).filter(
                    Stock.product_id == product.id,
                    Stock.organization_id == org_id
                ).first()
                
                location = str(record.get("location", "")).strip() or ""
                
                stock_data = {
                    "quantity": quantity,
                    "unit": unit.upper(),
                    "location": location
                }
                
                if not stock:
                    # Create new stock entry
                    new_stock = Stock(
                        organization_id=org_id,
                        product_id=product.id,
                        **stock_data
                    )
                    db.add(new_stock)
                    created_stocks += 1
                    logger.info(f"Created stock entry for: {product_name}")
                else:
                    # Update existing stock
                    old_quantity = stock.quantity
                    for field, value in stock_data.items():
                        setattr(stock, field, value)
                    updated_stocks += 1
                    
                    if old_quantity != quantity:
                        warnings.append(f"Row {i}: Updated stock for '{product_name}' from {old_quantity} to {quantity}")
                    
                    logger.info(f"Updated stock for: {product_name}")
                    
            except Exception as e:
                detailed_errors.append(BulkImportError(
                    row=i,
                    error=f"Error processing record: {str(e)}",
                    error_code="PROCESSING_ERROR"
                ))
                simple_errors.append(f"Row {i}: Error processing record - {str(e)}")
                logger.error(f"Row {i}: Error processing record - {str(e)}")
                skipped_records += 1
                continue
        
        # Commit all changes
        db.commit()
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Stock import completed by {current_user.email}: "
                   f"{created_products} products created, {created_stocks} stocks created, "
                   f"{updated_stocks} stocks updated, {len(detailed_errors)} errors")
        
        message_parts = []
        if created_products > 0:
            message_parts.append(f"{created_products} products created")
        if created_stocks > 0:
            message_parts.append(f"{created_stocks} stock entries created")
        if updated_stocks > 0:
            message_parts.append(f"{updated_stocks} stock entries updated")
        if skipped_records > 0:
            message_parts.append(f"{skipped_records} records skipped")
        if detailed_errors:
            message_parts.append(f"{len(detailed_errors)} errors encountered")
        
        message = f"Import completed. {', '.join(message_parts)}." if message_parts else "Import completed successfully."
        
        return BulkImportResponse(
            message=message,
            total_processed=len(records),
            created=created_stocks,
            updated=updated_stocks,
            skipped=skipped_records,
            errors=simple_errors,
            detailed_errors=detailed_errors,
            warnings=warnings,
            processing_time_seconds=processing_time
        )
        
    except HTTPException as e:
        logger.error(f"HTTP error during stock import: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error importing stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during import processing: {str(e)}"
        )

@router.post("/import/excel", response_model=BulkImportResponse)
async def import_stock_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import stock entries from Excel file - alias for bulk import"""
    return await bulk_import_stock(file, db, current_user)

@router.get("/template/excel")
async def download_stock_template():
    """Download Excel template for stock bulk import"""
    excel_data = StockExcelService.create_template()
    return ExcelService.create_streaming_response(excel_data, "stock_template.xlsx")

@router.get("/export/excel")
async def export_stock_excel(
    skip: int = 0,
    limit: int = 1000,
    product_id: int = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export stock to Excel"""
    
    org_id = require_current_organization_id()
    
    # Get stock using the same logic as the list endpoint
    query = db.query(Stock).join(Product)
    
    # Apply tenant filtering
    query = TenantQueryMixin.filter_by_tenant(query, Stock, org_id)
    
    if product_id:
        query = query.filter(Stock.product_id == product_id)
    
    if low_stock_only:
        query = query.filter(Stock.quantity <= Product.reorder_level)
    
    stock_items = query.offset(skip).limit(limit).all()
    
    # Convert to dict format for Excel export
    stock_data = []
    for stock in stock_items:
        stock_data.append({
            "product_name": stock.product.name,
            "hsn_code": stock.product.hsn_code or "",
            "part_number": stock.product.part_number or "",
            "unit": stock.unit,
            "unit_price": stock.product.unit_price,
            "gst_rate": stock.product.gst_rate,
            "reorder_level": stock.product.reorder_level,
            "quantity": stock.quantity,
            "location": stock.location or "",
        })
    
    excel_data = StockExcelService.export_stock(stock_data)
    return ExcelService.create_streaming_response(excel_data, "stock_export.xlsx")