# Revised api/stock.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Stock, Product
from app.schemas.stock import StockCreate, StockUpdate, StockInDB, BulkImportResponse
from app.schemas.base import ProductCreate
from app.services.excel_service import StockExcelService, ExcelService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[StockInDB])
async def get_stock(
    skip: int = 0,
    limit: int = 100,
    product_id: int = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get stock information"""
    query = db.query(Stock).join(Product)
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Stock, org_id)
    
    if product_id:
        query = query.filter(Stock.product_id == product_id)
    
    if low_stock_only:
        # Filter for products where stock quantity <= reorder level
        query = query.filter(Stock.quantity <= Product.reorder_level)
    
    stock_items = query.offset(skip).limit(limit).all()
    return stock_items

@router.get("/low-stock", response_model=List[StockInDB])
async def get_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with low stock (below reorder level)"""
    query = db.query(Stock).join(Product).filter(
        Stock.quantity <= Product.reorder_level
    )
    
    # Apply tenant filtering for non-super-admin users
    if not current_user.is_super_admin:
        org_id = require_current_organization_id()
        query = TenantQueryMixin.filter_by_tenant(query, Stock, org_id)
    
    low_stock_items = query.all()
    return low_stock_items

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

@router.post("/adjust/{product_id}")
async def adjust_stock(
    product_id: int,
    quantity_change: float,
    reason: str = "Manual adjustment",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Adjust stock quantity (positive to add, negative to subtract)"""
    stock = db.query(Stock).filter(Stock.product_id == product_id).first()
    
    if not stock:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Create new stock entry with the adjustment
        stock = Stock(
            product_id=product_id,
            quantity=max(0, quantity_change),  # Don't allow negative stock
            unit=product.unit,
            location=""
        )
        db.add(stock)
    else:
        # Adjust existing stock
        new_quantity = stock.quantity + quantity_change
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock for this adjustment"
            )
        stock.quantity = new_quantity
    
    db.commit()
    db.refresh(stock)
    
    logger.info(f"Stock adjusted for product ID {product_id}: {quantity_change:+.2f} - {reason} by {current_user.email}")
    return {"message": f"Stock adjusted by {quantity_change:+.2f}", "new_quantity": stock.quantity}

@router.post("/bulk", response_model=BulkImportResponse)
async def bulk_import_stock(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk import stock entries from Excel file, creating products if they don't exist"""
    org_id = require_current_organization_id()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are allowed"
        )
    
    try:
        # Parse Excel file
        records = await ExcelService.parse_excel_file(file, StockExcelService.REQUIRED_COLUMNS)
        
        if not records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data found in Excel file"
            )
        
        created_products = 0
        created_stocks = 0
        updated_stocks = 0
        errors = []
        
        for i, record in enumerate(records, 1):
            try:
                # Extract product and stock data
                product_name = str(record.get("product_name", "")).strip()
                unit = str(record.get("unit", "")).strip()
                quantity = float(record.get("quantity", 0))
                
                # Validate required fields
                if not product_name:
                    errors.append(f"Row {i}: Product Name is required")
                    continue
                    
                if not unit:
                    errors.append(f"Row {i}: Unit is required")
                    continue
                
                # Log record details for debugging
                logger.debug(f"Processing row {i}: product_name={product_name}, unit={unit}, quantity={quantity}")
                
                # Check if product exists by name
                product = db.query(Product).filter(
                    Product.name == product_name,
                    Product.organization_id == org_id
                ).first()
                
                if not product:
                    # Create new product if not exists
                    try:
                        product_data = {
                            "name": product_name,
                            "hsn_code": str(record.get("hsn_code", "")).strip(),
                            "part_number": str(record.get("part_number", "")).strip(),
                            "unit": unit,
                            "unit_price": float(record.get("unit_price", 0)),
                            "gst_rate": float(record.get("gst_rate", 18.0)),
                            "reorder_level": int(float(record.get("reorder_level", 10))),
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
                        
                    except (ValueError, TypeError) as e:
                        errors.append(f"Row {i}: Invalid product data - {str(e)}")
                        logger.error(f"Row {i}: Failed to create product - {str(e)}")
                        continue
                
                # Handle stock
                stock = db.query(Stock).filter(
                    Stock.product_id == product.id,
                    Stock.organization_id == org_id
                ).first()
                
                stock_data = {
                    "quantity": quantity,
                    "unit": unit,
                    "location": str(record.get("location", "")).strip()
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
                    for field, value in stock_data.items():
                        setattr(stock, field, value)
                    updated_stocks += 1
                    logger.info(f"Updated stock for: {product_name}")
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Row {i}: Invalid data format - {str(e)}")
                logger.error(f"Row {i}: Invalid data format - {str(e)}")
                continue
            except Exception as e:
                errors.append(f"Row {i}: Error processing record - {str(e)}")
                logger.error(f"Row {i}: Error processing record - {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Stock import completed by {current_user.email}: "
                   f"{created_products} products created, {created_stocks} stocks created, "
                   f"{updated_stocks} stocks updated, {len(errors)} errors")
        
        message_parts = []
        if created_products > 0:
            message_parts.append(f"{created_products} products created")
        if created_stocks > 0:
            message_parts.append(f"{created_stocks} stock entries created")
        if updated_stocks > 0:
            message_parts.append(f"{updated_stocks} stock entries updated")
        if errors:
            message_parts.append(f"{len(errors)} errors encountered")
        
        message = f"Import completed. {', '.join(message_parts)}."
        
        return BulkImportResponse(
            message=message,
            total_processed=len(records),
            created=created_stocks,
            updated=updated_stocks,
            errors=errors
        )
        
    except HTTPException as e:
        logger.error(f"HTTP error during stock import: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error importing stock: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing import: {str(e)}"
        )

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