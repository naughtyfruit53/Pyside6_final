from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import (
    PurchaseVoucher, SalesVoucher, PurchaseOrder, SalesOrder, GoodsReceiptNote, DeliveryChallan,
    ProformaInvoice, Quotation, CreditNote, DebitNote, PaymentVoucher, ReceiptVoucher,
    ContraVoucher, JournalVoucher, InterDepartmentVoucher, PurchaseReturn, SalesReturn
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
    valid_types = ["purchase_voucher", "sales_voucher", "purchase_order", "sales_order", "grn", "delivery_challan", "proforma_invoice", "quotation", "credit_note", "debit_note", "payment_voucher", "receipt_voucher", "contra_voucher", "journal_voucher", "inter_department_voucher", "purchase_return", "sales_return"]
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
    elif voucher_type == "purchase_order":
        voucher = db.query(PurchaseOrder).filter(PurchaseOrder.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "sales_order":
        voucher = db.query(SalesOrder).filter(SalesOrder.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "grn":
        voucher = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "delivery_challan":
        voucher = db.query(DeliveryChallan).filter(DeliveryChallan.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "proforma_invoice":
        voucher = db.query(ProformaInvoice).filter(ProformaInvoice.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "quotation":
        voucher = db.query(Quotation).filter(Quotation.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "credit_note":
        voucher = db.query(CreditNote).filter(CreditNote.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "debit_note":
        voucher = db.query(DebitNote).filter(DebitNote.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "payment_voucher":
        voucher = db.query(PaymentVoucher).filter(PaymentVoucher.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "receipt_voucher":
        voucher = db.query(ReceiptVoucher).filter(ReceiptVoucher.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.customer.email if voucher.customer else None
            recipient_name = voucher.customer.name if voucher.customer else ""
    elif voucher_type == "contra_voucher":
        voucher = db.query(ContraVoucher).filter(ContraVoucher.id == voucher_id).first()
        # No default recipient
    elif voucher_type == "journal_voucher":
        voucher = db.query(JournalVoucher).filter(JournalVoucher.id == voucher_id).first()
        # No default recipient
    elif voucher_type == "inter_department_voucher":
        voucher = db.query(InterDepartmentVoucher).filter(InterDepartmentVoucher.id == voucher_id).first()
        # No default recipient
    elif voucher_type == "purchase_return":
        voucher = db.query(PurchaseReturn).filter(PurchaseReturn.id == voucher_id).first()
        if voucher and not recipient_email:
            recipient_email = voucher.vendor.email if voucher.vendor else None
            recipient_name = voucher.vendor.name if voucher.vendor else ""
    elif voucher_type == "sales_return":
        voucher = db.query(SalesReturn).filter(SalesReturn.id == voucher_id).first()
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