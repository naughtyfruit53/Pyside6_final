from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_admin_user
from app.core.tenant import TenantQueryMixin, require_current_organization_id
from app.models.base import User, Customer
from app.schemas.base import CustomerCreate, CustomerUpdate, CustomerInDB
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
        org_id = require_current_organization_id()
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
    
    org_id = require_current_organization_id()
    
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