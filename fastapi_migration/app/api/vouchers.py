from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import PurchaseVoucher, SalesVoucher, PurchaseOrder, SalesOrder
from app.schemas.vouchers import (
    PurchaseVoucherCreate, PurchaseVoucherInDB, PurchaseVoucherUpdate,
    SalesVoucherCreate, SalesVoucherInDB, SalesVoucherUpdate,
    PurchaseOrderCreate, PurchaseOrderInDB, PurchaseOrderUpdate,
    SalesOrderCreate, SalesOrderInDB, SalesOrderUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Purchase Vouchers
@router.get("/purchase-vouchers/", response_model=List[PurchaseVoucherInDB])
async def get_purchase_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all purchase vouchers"""
    query = db.query(PurchaseVoucher)
    
    if status:
        query = query.filter(PurchaseVoucher.status == status)
    
    vouchers = query.offset(skip).limit(limit).all()
    return vouchers

@router.post("/purchase-vouchers/", response_model=PurchaseVoucherInDB)
async def create_purchase_voucher(
    voucher: PurchaseVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new purchase voucher"""
    try:
        # Create the voucher
        voucher_data = voucher.dict(exclude={'items'})
        voucher_data['created_by'] = current_user.id
        
        db_voucher = PurchaseVoucher(**voucher_data)
        db.add(db_voucher)
        db.flush()  # Get the voucher ID
        
        # Add items
        for item_data in voucher.items:
            from app.models.vouchers import PurchaseVoucherItem
            item = PurchaseVoucherItem(
                purchase_voucher_id=db_voucher.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_voucher)
        
        # Send email if requested
        if send_email and db_voucher.vendor and db_voucher.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="purchase_voucher",
                voucher_id=db_voucher.id,
                recipient_email=db_voucher.vendor.email,
                recipient_name=db_voucher.vendor.name
            )
        
        logger.info(f"Purchase voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase voucher"
        )

@router.get("/purchase-vouchers/{voucher_id}", response_model=PurchaseVoucherInDB)
async def get_purchase_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase voucher by ID"""
    voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase voucher not found"
        )
    return voucher

# Sales Vouchers
@router.get("/sales-vouchers/", response_model=List[SalesVoucherInDB])
async def get_sales_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all sales vouchers"""
    query = db.query(SalesVoucher)
    
    if status:
        query = query.filter(SalesVoucher.status == status)
    
    vouchers = query.offset(skip).limit(limit).all()
    return vouchers

@router.post("/sales-vouchers/", response_model=SalesVoucherInDB)
async def create_sales_voucher(
    voucher: SalesVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new sales voucher"""
    try:
        # Create the voucher
        voucher_data = voucher.dict(exclude={'items'})
        voucher_data['created_by'] = current_user.id
        
        db_voucher = SalesVoucher(**voucher_data)
        db.add(db_voucher)
        db.flush()  # Get the voucher ID
        
        # Add items
        for item_data in voucher.items:
            from app.models.vouchers import SalesVoucherItem
            item = SalesVoucherItem(
                sales_voucher_id=db_voucher.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_voucher)
        
        # Send email if requested
        if send_email and db_voucher.customer and db_voucher.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="sales_voucher",
                voucher_id=db_voucher.id,
                recipient_email=db_voucher.customer.email,
                recipient_name=db_voucher.customer.name
            )
        
        logger.info(f"Sales voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sales voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sales voucher"
        )

@router.get("/sales-vouchers/{voucher_id}", response_model=SalesVoucherInDB)
async def get_sales_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales voucher by ID"""
    voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales voucher not found"
        )
    return voucher

# Email endpoints
@router.post("/send-email/{voucher_type}/{voucher_id}")
async def send_voucher_email_endpoint(
    voucher_type: str,
    voucher_id: int,
    background_tasks: BackgroundTasks,
    custom_email: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send voucher via email"""
    # Validate voucher type
    valid_types = ["purchase_voucher", "sales_voucher", "purchase_order", "sales_order"]
    if voucher_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid voucher type. Must be one of: {valid_types}"
        )
    
    # Get voucher and determine email
    voucher = None
    recipient_email = custom_email
    recipient_name = ""
    
    if voucher_type == "purchase_voucher":
        voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "sales_voucher":
        voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )
    
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email address available for this voucher"
        )
    
    # Send email in background
    background_tasks.add_task(
        send_voucher_email,
        voucher_type=voucher_type,
        voucher_id=voucher_id,
        recipient_email=recipient_email,
        recipient_name=recipient_name
    )
    
    logger.info(f"Email queued for {voucher_type} {voucher_id} to {recipient_email} by {current_user.email}")
    return {"message": f"Email queued successfully to {recipient_email}"}