from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user, require_current_organization_id
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

# Purchase Vouchers by Type Endpoint (required by problem statement)
@router.get("/purchase", response_model=List[PurchaseVoucherInDB])
async def get_purchase_vouchers_by_type(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase vouchers filtered by type (problem statement requirement)"""
    org_id = require_current_organization_id(current_user)
    query = TenantQueryFilter.apply_organization_filter(db.query(PurchaseVoucher), PurchaseVoucher, org_id, current_user)
    query = query.filter(PurchaseVoucher.voucher_type == "purchase")
    
    if status:
        query = query.filter(PurchaseVoucher.status == status)
    if vendor_id:
        query = query.filter(PurchaseVoucher.vendor_id == vendor_id)
    
    return query.order_by(desc(PurchaseVoucher.date)).offset(skip).limit(limit).all()

# --- Purchase Orders ---

@router.get("/purchase-orders", response_model=List[PurchaseOrderInDB])
async def get_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    query = TenantQueryFilter.apply_organization_filter(db.query(PurchaseOrder), PurchaseOrder, org_id, current_user)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if vendor_id:
        query = query.filter(PurchaseOrder.vendor_id == vendor_id)
    return query.order_by(desc(PurchaseOrder.date)).offset(skip).limit(limit).all()

@router.post("/purchase-orders", response_model=PurchaseOrderInDB)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    # Validate vendor
    vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, org_id, current_user
    ).filter(Vendor.id == order.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {order.vendor_id} not found in organization")
    voucher_number = VoucherNumberService.generate_voucher_number(db, "PO", org_id, PurchaseOrder)
    order_data = order.dict()
    order_data.update({'organization_id': org_id, 'voucher_number': voucher_number, 'created_by': current_user.id})
    db_order = PurchaseOrder(**order_data)
    db.add(db_order)
    db.flush()
    # Add items
    for item_data in order.items:
        product = TenantQueryFilter.apply_organization_filter(
            db.query(Product), Product, org_id, current_user
        ).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found in organization")
        item = PurchaseOrderItem(
            purchase_order_id=db_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            total_amount=item_data.total_amount,
            pending_quantity=item_data.quantity
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
    org_id = require_current_organization_id(current_user)
    po = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseOrder), PurchaseOrder, org_id, current_user
    ).filter(PurchaseOrder.id == order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase Order {order_id} not found")
    po_items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_order_id == order_id,
        PurchaseOrderItem.pending_quantity > 0
    ).all()
    if not po_items:
        raise HTTPException(status_code=400, detail="No pending items in Purchase Order")
    grn_voucher_number = VoucherNumberService.generate_voucher_number(db, "GRN", org_id, GoodsReceiptNote)
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
            "received_quantity": po_item.pending_quantity,
            "accepted_quantity": po_item.pending_quantity,
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

# --- Goods Receipt Notes (GRN) ---

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
    org_id = require_current_organization_id(current_user)
    query = TenantQueryFilter.apply_organization_filter(db.query(GoodsReceiptNote), GoodsReceiptNote, org_id, current_user)
    if status:
        query = query.filter(GoodsReceiptNote.status == status)
    if vendor_id:
        query = query.filter(GoodsReceiptNote.vendor_id == vendor_id)
    if purchase_order_id:
        query = query.filter(GoodsReceiptNote.purchase_order_id == purchase_order_id)
    return query.order_by(desc(GoodsReceiptNote.grn_date)).offset(skip).limit(limit).all()

@router.post("/goods-receipt-notes", response_model=GRNInDB)
async def create_goods_receipt_note(
    grn: GRNCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    po = TenantQueryFilter.apply_organization_filter(
        db.query(PurchaseOrder), PurchaseOrder, org_id, current_user
    ).filter(PurchaseOrder.id == grn.purchase_order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase Order {grn.purchase_order_id} not found")
    grn_data = grn.dict()
    grn_data.update({'organization_id': org_id, 'created_by': current_user.id})
    db_grn = GoodsReceiptNote(**grn_data)
    db.add(db_grn)
    db.flush()
    for item_data in grn.items:
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.id == item_data.po_item_id,
            PurchaseOrderItem.purchase_order_id == grn.purchase_order_id
        ).first()
        if not po_item:
            raise HTTPException(status_code=404, detail=f"Purchase Order item {item_data.po_item_id} not found")
        if item_data.received_quantity > po_item.pending_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Received quantity ({item_data.received_quantity}) exceeds pending quantity ({po_item.pending_quantity}) for product {po_item.product_id}"
            )
        grn_item = GoodsReceiptNoteItem(
            grn_id=db_grn.id,
            **item_data.dict()
        )
        db.add(grn_item)
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
    org_id = require_current_organization_id(current_user)
    grn = TenantQueryFilter.apply_organization_filter(
        db.query(GoodsReceiptNote), GoodsReceiptNote, org_id, current_user
    ).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail=f"GRN {grn_id} not found")
    grn_items = db.query(GoodsReceiptNoteItem).filter(
        GoodsReceiptNoteItem.grn_id == grn_id,
        GoodsReceiptNoteItem.accepted_quantity > 0
    ).all()
    if not grn_items:
        raise HTTPException(status_code=400, detail="No accepted items in GRN")
    pv_voucher_number = VoucherNumberService.generate_voucher_number(db, "PV", org_id, PurchaseVoucher)
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
        taxable_amount = grn_item.accepted_quantity * grn_item.unit_price
        gst_rate = 18.0  # Simplified, normally from product
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

# --- Purchase Vouchers ---

@router.get("/purchase-vouchers", response_model=List[PurchaseVoucherInDB])
async def get_purchase_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    query = TenantQueryFilter.apply_organization_filter(db.query(PurchaseVoucher), PurchaseVoucher, org_id, current_user)
    if status:
        query = query.filter(PurchaseVoucher.status == status)
    if vendor_id:
        query = query.filter(PurchaseVoucher.vendor_id == vendor_id)
    return query.order_by(desc(PurchaseVoucher.date)).offset(skip).limit(limit).all()

@router.post("/purchase-vouchers", response_model=PurchaseVoucherInDB)
async def create_purchase_voucher(
    voucher: PurchaseVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    vendor = TenantQueryFilter.apply_organization_filter(
        db.query(Vendor), Vendor, org_id, current_user
    ).filter(Vendor.id == voucher.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor {voucher.vendor_id} not found")
    voucher_data = voucher.dict()
    voucher_data.update({
        'organization_id': org_id,
        'created_by': current_user.id
    })
    db_voucher = PurchaseVoucher(**voucher_data)
    db.add(db_voucher)
    db.flush()
    for item_data in voucher.items:
        product = TenantQueryFilter.apply_organization_filter(
            db.query(Product), Product, org_id, current_user
        ).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
        item = PurchaseVoucherItem(
            purchase_voucher_id=db_voucher.id,
            **item_data.dict()
        )
        db.add(item)
    db.commit()
    db.refresh(db_voucher)
    if send_email and db_voucher.vendor and db_voucher.vendor.email:
        background_tasks.add_task(
            send_voucher_email,
            db_voucher,
            "purchase_voucher",
            db_voucher.vendor.email
        )
    logger.info(f"Created purchase voucher {db_voucher.voucher_number} for organization {org_id}")
    return db_voucher

# --- Purchase Returns (rejection_in) ---

@router.get("/rejection_in", response_model=List[PurchaseReturnInDB])
async def get_purchase_returns(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    query = TenantQueryFilter.apply_organization_filter(db.query(PurchaseReturn), PurchaseReturn, org_id, current_user)
    if status:
        query = query.filter(PurchaseReturn.status == status)
    return query.offset(skip).limit(limit).all()

@router.post("/rejection_in", response_model=PurchaseReturnInDB)
async def create_purchase_return(
    return_data: PurchaseReturnCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    org_id = require_current_organization_id(current_user)
    data = return_data.dict()
    data['organization_id'] = org_id
    data['created_by'] = current_user.id
    db_return = PurchaseReturn(**data)
    db.add(db_return)
    db.flush()
    for item_data in return_data.items:
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
            db_return,
            "purchase_return",
            db_return.vendor.email
        )
    logger.info(f"Purchase return {return_data.voucher_number} created by {current_user.email}")
    return db_return