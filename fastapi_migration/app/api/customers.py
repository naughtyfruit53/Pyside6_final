from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User, Customer
from app.schemas.base import CustomerCreate, CustomerUpdate, CustomerInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[CustomerInDB])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all customers"""
    query = db.query(Customer)
    
    if active_only:
        query = query.filter(Customer.is_active == True)
    
    if search:
        query = query.filter(
            Customer.name.contains(search) |
            Customer.contact_number.contains(search) |
            Customer.email.contains(search)
        )
    
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
    return customer

@router.post("/", response_model=CustomerInDB)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new customer"""
    # Check if customer name already exists
    existing_customer = db.query(Customer).filter(Customer.name == customer.name).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer name already exists"
        )
    
    # Create new customer
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    logger.info(f"Customer {customer.name} created by {current_user.email}")
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
    
    # Check name uniqueness if being updated
    if customer_update.name and customer_update.name != customer.name:
        existing_customer = db.query(Customer).filter(Customer.name == customer_update.name).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer name already exists"
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
    current_user: User = Depends(get_current_active_user)
):
    """Delete customer (soft delete by setting inactive)"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Soft delete - set as inactive
    customer.is_active = False
    db.commit()
    
    logger.info(f"Customer {customer.name} deactivated by {current_user.email}")
    return {"message": "Customer deactivated successfully"}