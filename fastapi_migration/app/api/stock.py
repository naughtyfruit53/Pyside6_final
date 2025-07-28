# app/api/stock.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User, Stock, Product
from app.schemas.base import StockCreate, StockUpdate, StockInDB, ProductCreate
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
    low_stock_items = db.query(Stock).join(Product).filter(
        Stock.quantity <= Product.reorder_level
    ).all()
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
        return StockInDB(
            id=0,
            product_id=product_id,
            quantity=0.0,
            unit=product.unit,
            location="",
            last_updated=product.created_at
        )
    return stock

@router.post("/", response_model=StockInDB)
async def create_stock_entry(
    stock: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new stock entry"""
    # Check if product exists
    product = db.query(Product).filter(Product.id == stock.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if stock entry already exists
    existing_stock = db.query(Stock).filter(Stock.product_id == stock.product_id).first()
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock entry already exists for this product. Use update endpoint."
        )
    
    # Create new stock entry
    db_stock = Stock(**stock.dict())
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

@router.post("/bulk")
async def bulk_import_stock(
    stock_items: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk import stock entries, creating products if they don't exist"""
    created_products = 0
    created_stocks = 0
    updated_stocks = 0
    
    for item in stock_items:
        # Check if product exists by name (assuming name is unique)
        product = db.query(Product).filter(Product.name == item.get('product_name')).first()
        
        if not product:
            # Create new product if not exists
            if not item.get('product_name'):
                logger.warning(f"Skipping item without product_name: {item}")
                continue
                
            new_product = Product(
                name=item['product_name'],
                hsn_code=item.get('hsn_code', ''),
                unit=item.get('unit', 'PCS'),
                unit_price=item.get('unit_price', 0.0),
                gst_rate=item.get('gst_rate', 18.0),
                reorder_level=item.get('reorder_level', 10),
                is_active=True
            )
            db.add(new_product)
            db.flush()  # Get the new product ID
            product = new_product
            created_products += 1
            logger.info(f"Created new product: {new_product.name}")
        
        # Handle stock
        stock = db.query(Stock).filter(Stock.product_id == product.id).first()
        
        if not stock:
            # Create new stock
            stock = Stock(
                product_id=product.id,
                quantity=item.get('quantity', 0.0),
                unit=item.get('unit', product.unit),
                location=item.get('location', '')
            )
            db.add(stock)
            created_stocks += 1
        else:
            # Update existing stock
            stock.quantity = item.get('quantity', stock.quantity)
            stock.unit = item.get('unit', stock.unit)
            stock.location = item.get('location', stock.location)
            updated_stocks += 1
        
        # Update product details if provided
        if 'hsn_code' in item:
            product.hsn_code = item['hsn_code']
        if 'unit_price' in item:
            product.unit_price = item['unit_price']
        if 'gst_rate' in item:
            product.gst_rate = item['gst_rate']
        if 'reorder_level' in item:
            product.reorder_level = item['reorder_level']
    
    db.commit()
    
    logger.info(f"Bulk import completed by {current_user.email}: "
                f"{created_products} products created, "
                f"{created_stocks} stocks created, "
                f"{updated_stocks} stocks updated")
    
    return {
        "message": "Bulk import completed successfully",
        "created_products": created_products,
        "created_stocks": created_stocks,
        "updated_stocks": updated_stocks,
        "total_processed": len(stock_items)
    }