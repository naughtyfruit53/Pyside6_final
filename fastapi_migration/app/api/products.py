from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Product
from app.schemas.base import ProductCreate, ProductUpdate, ProductInDB
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