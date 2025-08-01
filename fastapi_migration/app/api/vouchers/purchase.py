from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.auth import get_current_active_user, require_current_organization_id
from app.core.tenant import TenantQueryFilter
from app.models.base import User, Vendor, Product
from app.models.vouchers import (
    PurchaseVoucher, PurchaseOrder, GoodsReceiptNote, PurchaseReturn,
    PurchaseVoucherItem, PurchaseOrderItem, GoodsReceiptNoteItem, PurchaseReturnItem
)
from app.schemas.vouchers import (
    PurchaseVoucherCreate, PurchaseVoucherInDB, PurchaseVoucherUpdate,
    PurchaseOrderCreate, PurchaseOrderInDB, PurchaseOrderUpdate,
    GRNCreate, GRNInDB, GRNUpdate,
    PurchaseReturnCreate, PurchaseReturnInDB, PurchaseReturnUpdate,
    PurchaseOrderAutoPopulateResponse, GRNAutoPopulateResponse
)
from app.services.email_service import send_voucher_email
from app.services.voucher_service import VoucherNumberService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Purchase Orders
@router.get("/purchase-orders", response_model=List[PurchaseOrderInDB])
async def get_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase orders with organization filtering"""
    org_id = require_current_organization_id(current_user)
    
    query = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseOrder), PurchaseOrder, org_id, current_user
    )
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    
    orders = query.order_by(desc(PurchaseOrder.date)).offset(skip).limit(limit).all()
    return orders

@router.post("/purchase-orders", response_model=PurchaseOrderInDB)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new purchase order with organization validation"""
    org_id = require_current_organization_id(current_user)
    
    # Validate vendor belongs to organization
    vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, org_id, current_user
    ).filter(Vendor.id == order.vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {order.vendor_id} not found in organization"
        )
    
    # Generate voucher number
    voucher_number = VoucherNumberService.generate_voucher_number(
        db, "PO", org_id, PurchaseOrder
    )
    
    # Create order
    order_data = order.dict()
    order_data.update({
        'organization_id': org_id,
        'voucher_number': voucher_number,
        'created_by': current_user.id
    })
    
    db_order = PurchaseOrder(**order_data)
    db.add(db_order)
    db.flush()
    
    # Add items
    for item_data in order.items:
        # Validate product belongs to organization
        product = TenantQueryFilter.apply_organization_filter(
            db.query(Product), Product, org_id, current_user
        ).filter(Product.id == item_data.product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found in organization"
            )
        
        item = PurchaseOrderItem(
            purchase_order_id=db_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            total_amount=item_data.total_amount,
            pending_quantity=item_data.quantity  # Initially all quantity is pending
        )
        db.add(item)
    
    db.commit()
    db.refresh(db_order)
    
    logger.info(f"Created purchase order {db_order.voucher_number} for organization {org_id}")
    return db_order

@router.get("/purchase-orders/{order_id}/grn-auto-populate", response_model=GRNAutoPopulateResponse)
async def auto_populate_grn_from_po(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Auto-populate GRN data from Purchase Order"""
    org_id = require_current_organization_id(current_user)
    
    # Find purchase order
    po = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseOrder), PurchaseOrder, org_id, current_user
    ).filter(PurchaseOrder.id == order_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {order_id} not found"
        )
    
    # Get PO items with pending quantities
    po_items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_order_id == order_id,
        PurchaseOrderItem.pending_quantity > 0
    ).all()
    
    if not po_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending items in Purchase Order"
        )
    
    # Generate GRN voucher number
    grn_voucher_number = VoucherNumberService.generate_voucher_number(
        db, "GRN", org_id, GoodsReceiptNote
    )
    
    # Prepare auto-populated GRN data
    grn_data = {
        "voucher_number": grn_voucher_number,
        "purchase_order_id": po.id,
        "vendor_id": po.vendor_id,
        "grn_date": datetime.now(),
        "date": datetime.now(),
        "items": []
    }
    
    for po_item in po_items:
        grn_item = {
            "product_id": po_item.product_id,
            "po_item_id": po_item.id,
            "ordered_quantity": po_item.quantity,
            "received_quantity": po_item.pending_quantity,  # Default to pending quantity
            "accepted_quantity": po_item.pending_quantity,  # Default to received quantity
            "rejected_quantity": 0.0,
            "unit": po_item.unit,
            "unit_price": po_item.unit_price,
            "total_cost": po_item.pending_quantity * po_item.unit_price
        }
        grn_data["items"].append(grn_item)
    
    return {
        "purchase_order": po,
        "grn_data": grn_data,
        "vendor": po.vendor
    }

# Goods Receipt Notes
@router.get("/goods-receipt-notes", response_model=List[GRNInDB])
async def get_goods_receipt_notes(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get goods receipt notes with organization filtering"""
    org_id = require_current_organization_id(current_user)
    
    query = TenantQueryFilter.apply_organization_filter(
        db.query(GoodsReceiptNote), GoodsReceiptNote, org_id, current_user
    )
    
    if status:
        query = query.filter(GoodsReceiptNote.status == status)
    
    if vendor_id:
        query = query.filter(GoodsReceiptNote.vendor_id == vendor_id)
    
    if purchase_order_id:
        query = query.filter(GoodsReceiptNote.purchase_order_id == purchase_order_id)
    
    grns = query.order_by(desc(GoodsReceiptNote.grn_date)).offset(skip).limit(limit).all()
    return grns

@router.post("/goods-receipt-notes", response_model=GRNInDB)
async def create_goods_receipt_note(
    grn: GRNCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new goods receipt note with PO integration"""
    org_id = require_current_organization_id(current_user)
    
    # Validate purchase order
    po = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseOrder), PurchaseOrder, org_id, current_user
    ).filter(PurchaseOrder.id == grn.purchase_order_id).first()
    
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase Order {grn.purchase_order_id} not found"
        )
    
    # Create GRN
    grn_data = grn.dict()
    grn_data.update({
        'organization_id': org_id,
        'created_by': current_user.id
    })
    
    db_grn = GoodsReceiptNote(**grn_data)
    db.add(db_grn)
    db.flush()
    
    # Add items and update PO quantities
    for item_data in grn.items:
        # Validate PO item
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.id == item_data.po_item_id,
            PurchaseOrderItem.purchase_order_id == grn.purchase_order_id
        ).first()
        
        if not po_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order item {item_data.po_item_id} not found"
            )
        
        # Validate quantities
        if item_data.received_quantity > po_item.pending_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Received quantity ({item_data.received_quantity}) exceeds pending quantity ({po_item.pending_quantity}) for product {po_item.product_id}"
            )
        
        # Create GRN item
        grn_item = GoodsReceiptNoteItem(
            grn_id=db_grn.id,
            **item_data.dict()
        )
        db.add(grn_item)
        
        # Update PO item quantities
        po_item.delivered_quantity += item_data.accepted_quantity
        po_item.pending_quantity -= item_data.received_quantity
    
    db.commit()
    db.refresh(db_grn)
    
    logger.info(f"Created GRN {db_grn.voucher_number} for PO {po.voucher_number} in organization {org_id}")
    return db_grn

@router.get("/goods-receipt-notes/{grn_id}/purchase-voucher-auto-populate", response_model=PurchaseOrderAutoPopulateResponse)
async def auto_populate_purchase_voucher_from_grn(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Auto-populate Purchase Voucher data from GRN"""
    org_id = require_current_organization_id(current_user)
    
    # Find GRN
    grn = TenantQueryFilter.apply_organization_filter(
        db.query(GoodsReceiptNote), GoodsReceiptNote, org_id, current_user
    ).filter(GoodsReceiptNote.id == grn_id).first()
    
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GRN {grn_id} not found"
        )
    
    # Get GRN items
    grn_items = db.query(GoodsReceiptNoteItem).filter(
        GoodsReceiptNoteItem.grn_id == grn_id,
        GoodsReceiptNoteItem.accepted_quantity > 0
    ).all()
    
    if not grn_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No accepted items in GRN"
        )
    
    # Generate Purchase Voucher number
    pv_voucher_number = VoucherNumberService.generate_voucher_number(
        db, "PV", org_id, PurchaseVoucher
    )
    
    # Prepare auto-populated PV data
    pv_data = {
        "voucher_number": pv_voucher_number,
        "vendor_id": grn.vendor_id,
        "purchase_order_id": grn.purchase_order_id,
        "grn_id": grn.id,
        "date": datetime.now(),
        "items": []
    }
    
    total_amount = 0.0
    for grn_item in grn_items:
        # Calculate tax amounts (assuming 18% GST for demo)
        taxable_amount = grn_item.accepted_quantity * grn_item.unit_price
        gst_rate = 18.0  # This should come from product or be configurable
        gst_amount = taxable_amount * (gst_rate / 100)
        item_total = taxable_amount + gst_amount
        
        pv_item = {
            "product_id": grn_item.product_id,
            "grn_item_id": grn_item.id,
            "quantity": grn_item.accepted_quantity,
            "unit": grn_item.unit,
            "unit_price": grn_item.unit_price,
            "taxable_amount": taxable_amount,
            "gst_rate": gst_rate,
            "cgst_amount": gst_amount / 2,
            "sgst_amount": gst_amount / 2,
            "igst_amount": 0.0,
            "total_amount": item_total
        }
        pv_data["items"].append(pv_item)
        total_amount += item_total
    
    pv_data["total_amount"] = total_amount
    pv_data["cgst_amount"] = sum(item["cgst_amount"] for item in pv_data["items"])
    pv_data["sgst_amount"] = sum(item["sgst_amount"] for item in pv_data["items"])
    pv_data["igst_amount"] = sum(item["igst_amount"] for item in pv_data["items"])
    
    return {
        "grn": grn,
        "purchase_voucher_data": pv_data,
        "vendor": grn.vendor,
        "purchase_order": grn.purchase_order
    }

# Purchase Vouchers
@router.get("/purchase-vouchers", response_model=List[PurchaseVoucherInDB])
async def get_purchase_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase vouchers with organization filtering"""
    org_id = require_current_organization_id(current_user)
    
    query = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseVoucher), PurchaseVoucher, org_id, current_user
    )
    
    if status:
        query = query.filter(PurchaseVoucher.status == status)
    
    if vendor_id:
        query = query.filter(PurchaseVoucher.vendor_id == vendor_id)
    
    vouchers = query.order_by(desc(PurchaseVoucher.date)).offset(skip).limit(limit).all()
    return vouchers

@router.post("/purchase-vouchers", response_model=PurchaseVoucherInDB)
async def create_purchase_voucher(
    voucher: PurchaseVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new purchase voucher with GRN integration"""
    org_id = require_current_organization_id(current_user)
    
    # Validate vendor
    vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, org_id, current_user
    ).filter(Vendor.id == voucher.vendor_id).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor {voucher.vendor_id} not found"
        )
    
    # Create voucher
    voucher_data = voucher.dict()
    voucher_data.update({
        'organization_id': org_id,
        'created_by': current_user.id
    })
    
    db_voucher = PurchaseVoucher(**voucher_data)
    db.add(db_voucher)
    db.flush()
    
    # Add items
    for item_data in voucher.items:
        # Validate product
        product = TenantQueryFilter.apply_organization_filter(
            db.query(Product), Product, org_id, current_user
        ).filter(Product.id == item_data.product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found"
            )
        
        item = PurchaseVoucherItem(
            purchase_voucher_id=db_voucher.id,
            **item_data.dict()
        )
        db.add(item)
    
    db.commit()
    db.refresh(db_voucher)
    
    # Send email if requested
    if send_email:
        background_tasks.add_task(
            send_voucher_email, 
            db_voucher, 
            "purchase_voucher", 
            vendor.email
        )
    
    logger.info(f"Created purchase voucher {db_voucher.voucher_number} for organization {org_id}")
    return db_voucher
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

@router.put("/purchase-vouchers/{voucher_id}", response_model=PurchaseVoucherInDB)
async def update_purchase_voucher(
    voucher_id: int,
    voucher_update: PurchaseVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update purchase voucher"""
    try:
        voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase voucher not found"
            )
        
        update_data = voucher_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        if voucher_update.items is not None:
            from app.models.vouchers import PurchaseVoucherItem
            db.query(PurchaseVoucherItem).filter(PurchaseVoucherItem.purchase_voucher_id == voucher_id).delete()
            for item_data in voucher_update.items:
                item = PurchaseVoucherItem(
                    purchase_voucher_id=voucher_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Purchase voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating purchase voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase voucher"
        )

@router.delete("/purchase-vouchers/{voucher_id}")
async def delete_purchase_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete purchase voucher"""
    try:
        voucher = db.query(PurchaseVoucher).filter(PurchaseVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase voucher not found"
            )
        
        from app.models.vouchers import PurchaseVoucherItem
        db.query(PurchaseVoucherItem).filter(PurchaseVoucherItem.purchase_voucher_id == voucher_id).delete()
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Purchase voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Purchase voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting purchase voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete purchase voucher"
        )

# Purchase Orders
@router.get("/purchase_order", response_model=List[PurchaseOrderInDB])
async def get_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all purchase orders"""
    query = db.query(PurchaseOrder)
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@router.post("/purchase_order", response_model=PurchaseOrderInDB)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new purchase order"""
    try:
        order_data = order.dict(exclude={'items'})
        order_data['created_by'] = current_user.id
        
        db_order = PurchaseOrder(**order_data)
        db.add(db_order)
        db.flush()
        
        for item_data in order.items:
            from app.models.vouchers import PurchaseOrderItem
            item = PurchaseOrderItem(
                purchase_order_id=db_order.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_order)
        
        if send_email and db_order.vendor and db_order.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="purchase_order",
                voucher_id=db_order.id,
                recipient_email=db_order.vendor.email,
                recipient_name=db_order.vendor.name
            )
        
        logger.info(f"Purchase order {order.voucher_number} created by {current_user.email}")
        return db_order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase order"
        )

@router.get("/purchase_order/{order_id}", response_model=PurchaseOrderInDB)
async def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase order by ID"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found"
        )
    return order

@router.put("/purchase_order/{order_id}", response_model=PurchaseOrderInDB)
async def update_purchase_order(
    order_id: int,
    order_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update purchase order"""
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        update_data = order_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(order, field, value)
        
        if order_update.items is not None:
            from app.models.vouchers import PurchaseOrderItem
            db.query(PurchaseOrderItem).filter(
                PurchaseOrderItem.purchase_order_id == order_id
            ).delete()
            
            for item_data in order_update.items:
                item = PurchaseOrderItem(
                    purchase_order_id=order_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"Purchase order {order.voucher_number} updated by {current_user.email}")
        return order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating purchase order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase order"
        )

@router.delete("/purchase_order/{order_id}")
async def delete_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete purchase order"""
    try:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase order not found"
            )
        
        from app.models.vouchers import PurchaseOrderItem
        db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.purchase_order_id == order_id
        ).delete()
        
        db.delete(order)
        db.commit()
        
        logger.info(f"Purchase order {order.voucher_number} deleted by {current_user.email}")
        return {"message": "Purchase order deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting purchase order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete purchase order"
        )

# Goods Receipt Notes (GRN)
@router.get("/grn", response_model=List[GRNInDB])
async def get_grns(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(GoodsReceiptNote)
    
    if status:
        query = query.filter(GoodsReceiptNote.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/grn", response_model=GRNInDB)
async def create_grn(
    grn: GRNCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        grn_data = grn.dict(exclude={'items'})
        grn_data['created_by'] = current_user.id
        
        db_grn = GoodsReceiptNote(**grn_data)
        db.add(db_grn)
        db.flush()
        
        for item_data in grn.items:
            from app.models.vouchers import GoodsReceiptNoteItem
            item = GoodsReceiptNoteItem(
                grn_id=db_grn.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_grn)
        
        if send_email and db_grn.vendor and db_grn.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="grn",
                voucher_id=db_grn.id,
                recipient_email=db_grn.vendor.email,
                recipient_name=db_grn.vendor.name
            )
        
        logger.info(f"GRN {grn.voucher_number} created by {current_user.email}")
        return db_grn
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating GRN: {e}")
        raise HTTPException(status_code=500, detail="Failed to create GRN")

@router.get("/grn/{grn_id}", response_model=GRNInDB)
async def get_grn(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return grn

@router.put("/grn/{grn_id}", response_model=GRNInDB)
async def update_grn(
    grn_id: int,
    grn_update: GRNUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
        if not grn:
            raise HTTPException(status_code=404, detail="GRN not found")
        
        update_data = grn_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(grn, field, value)
        
        if grn_update.items is not None:
            from app.models.vouchers import GoodsReceiptNoteItem
            db.query(GoodsReceiptNoteItem).filter(GoodsReceiptNoteItem.grn_id == grn_id).delete()
            for item_data in grn_update.items:
                item = GoodsReceiptNoteItem(
                    grn_id=grn_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(grn)
        
        logger.info(f"GRN {grn.voucher_number} updated by {current_user.email}")
        return grn
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating GRN: {e}")
        raise HTTPException(status_code=500, detail="Failed to update GRN")

@router.delete("/grn/{grn_id}")
async def delete_grn(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
        if not grn:
            raise HTTPException(status_code=404, detail="GRN not found")
        
        from app.models.vouchers import GoodsReceiptNoteItem
        db.query(GoodsReceiptNoteItem).filter(GoodsReceiptNoteItem.grn_id == grn_id).delete()
        
        db.delete(grn)
        db.commit()
        
        logger.info(f"GRN {grn.voucher_number} deleted by {current_user.email}")
        return {"message": "GRN deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting GRN: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete GRN")

# Purchase Returns
@router.get("/rejection_in", response_model=List[PurchaseReturnInDB])
async def get_purchase_returns(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all purchase returns"""
    query = db.query(PurchaseReturn)
    
    if status:
        query = query.filter(PurchaseReturn.status == status)
    
    returns = query.offset(skip).limit(limit).all()
    return returns

@router.post("/rejection_in", response_model=PurchaseReturnInDB)
async def create_purchase_return(
    return_data: PurchaseReturnCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new purchase return"""
    try:
        data = return_data.dict(exclude={'items'})
        data['created_by'] = current_user.id
        
        db_return = PurchaseReturn(**data)
        db.add(db_return)
        db.flush()
        
        for item_data in return_data.items:
            from app.models.vouchers import PurchaseReturnItem
            item = PurchaseReturnItem(
                purchase_return_id=db_return.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_return)
        
        if send_email and db_return.vendor and db_return.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="purchase_return",
                voucher_id=db_return.id,
                recipient_email=db_return.vendor.email,
                recipient_name=db_return.vendor.name
            )
        
        logger.info(f"Purchase return {return_data.voucher_number} created by {current_user.email}")
        return db_return
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating purchase return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create purchase return"
        )

@router.get("/rejection_in/{return_id}", response_model=PurchaseReturnInDB)
async def get_purchase_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase return by ID"""
    return_ = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
    if not return_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase return not found"
        )
    return return_

@router.put("/rejection_in/{return_id}", response_model=PurchaseReturnInDB)
async def update_purchase_return(
    return_id: int,
    return_update: PurchaseReturnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update purchase return"""
    try:
        return_ = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
        if not return_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase return not found"
            )
        
        update_data = return_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(return_, field, value)
        
        if return_update.items is not None:
            from app.models.vouchers import PurchaseReturnItem
            db.query(PurchaseReturnItem).filter(PurchaseReturnItem.purchase_return_id == return_id).delete()
            for item_data in return_update.items:
                item = PurchaseReturnItem(
                    purchase_return_id=return_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(return_)
        
        logger.info(f"Purchase return {return_.voucher_number} updated by {current_user.email}")
        return return_
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating purchase return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update purchase return"
        )

@router.delete("/rejection_in/{return_id}")
async def delete_purchase_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete purchase return"""
    try:
        return_ = db.query(PurchaseReturn).filter(PurchaseReturn.id == return_id).first()
        if not return_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase return not found"
            )
        
        from app.models.vouchers import PurchaseReturnItem
        db.query(PurchaseReturnItem).filter(PurchaseReturnItem.purchase_return_id == return_id).delete()
        
        db.delete(return_)
        db.commit()
        
        logger.info(f"Purchase return {return_.voucher_number} deleted by {current_user.email}")
        return {"message": "Purchase return deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting purchase return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete purchase return"
        )