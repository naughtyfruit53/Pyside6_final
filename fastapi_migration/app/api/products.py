from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User, Product
from app.schemas.base import ProductCreate, ProductUpdate, ProductInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[ProductInDB])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all products"""
    query = db.query(Product)
    
    if active_only:
        query = query.filter(Product.is_active == True)
    
    if search:
        query = query.filter(
            Product.name.contains(search) |
            Product.hsn_code.contains(search) |
            Product.part_number.contains(search)
        )
    
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
    return product

@router.post("/", response_model=ProductInDB)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new product"""
    # Check if product name already exists
    existing_product = db.query(Product).filter(Product.name == product.name).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name already exists"
        )
    
    # Create new product
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    logger.info(f"Product {product.name} created by {current_user.email}")
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
    
    # Check name uniqueness if being updated
    if product_update.name and product_update.name != product.name:
        existing_product = db.query(Product).filter(Product.name == product_update.name).first()
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name already exists"
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
    current_user: User = Depends(get_current_active_user)
):
    """Delete product (soft delete by setting inactive)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Soft delete - set as inactive
    product.is_active = False
    db.commit()
    
    logger.info(f"Product {product.name} deactivated by {current_user.email}")
    return {"message": "Product deactivated successfully"}