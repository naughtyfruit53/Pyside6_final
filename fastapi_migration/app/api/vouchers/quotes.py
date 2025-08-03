from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import ProformaInvoice, Quotation
from app.schemas.vouchers import (
    ProformaInvoiceCreate, ProformaInvoiceInDB, ProformaInvoiceUpdate,
    QuotationCreate, QuotationInDB, QuotationUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Proforma Invoices
@router.get("/proforma-invoices/", response_model=List[ProformaInvoiceInDB])
async def get_proforma_invoices(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all proforma invoices"""
    query = db.query(ProformaInvoice)
    
    if status:
        query = query.filter(ProformaInvoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices

@router.post("/proforma-invoices/", response_model=ProformaInvoiceInDB)
async def create_proforma_invoice(
    invoice: ProformaInvoiceCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new proforma invoice"""
    try:
        invoice_data = invoice.dict(exclude={'items'})
        invoice_data['created_by'] = current_user.id
        
        db_invoice = ProformaInvoice(**invoice_data)
        db.add(db_invoice)
        db.flush()
        
        for item_data in invoice.items:
            from app.models.vouchers import ProformaInvoiceItem
            item = ProformaInvoiceItem(
                proforma_invoice_id=db_invoice.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_invoice)
        
        if send_email and db_invoice.customer and db_invoice.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="proforma_invoice",
                voucher_id=db_invoice.id,
                recipient_email=db_invoice.customer.email,
                recipient_name=db_invoice.customer.name
            )
        
        logger.info(f"Proforma invoice {invoice.voucher_number} created by {current_user.email}")
        return db_invoice
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating proforma invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proforma invoice"
        )

@router.get("/proforma-invoices/{invoice_id}", response_model=ProformaInvoiceInDB)
async def get_proforma_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get proforma invoice by ID"""
    invoice = db.query(ProformaInvoice).filter(ProformaInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proforma invoice not found"
        )
    return invoice

@router.put("/proforma-invoices/{invoice_id}", response_model=ProformaInvoiceInDB)
async def update_proforma_invoice(
    invoice_id: int,
    invoice_update: ProformaInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update proforma invoice"""
    try:
        invoice = db.query(ProformaInvoice).filter(ProformaInvoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proforma invoice not found"
            )
        
        update_data = invoice_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        if invoice_update.items is not None:
            from app.models.vouchers import ProformaInvoiceItem
            db.query(ProformaInvoiceItem).filter(ProformaInvoiceItem.proforma_invoice_id == invoice_id).delete()
            for item_data in invoice_update.items:
                item = ProformaInvoiceItem(
                    proforma_invoice_id=invoice_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(invoice)
        
        logger.info(f"Proforma invoice {invoice.voucher_number} updated by {current_user.email}")
        return invoice
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating proforma invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update proforma invoice"
        )

@router.delete("/proforma-invoices/{invoice_id}")
async def delete_proforma_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete proforma invoice"""
    try:
        invoice = db.query(ProformaInvoice).filter(ProformaInvoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proforma invoice not found"
            )
        
        from app.models.vouchers import ProformaInvoiceItem
        db.query(ProformaInvoiceItem).filter(ProformaInvoiceItem.proforma_invoice_id == invoice_id).delete()
        
        db.delete(invoice)
        db.commit()
        
        logger.info(f"Proforma invoice {invoice.voucher_number} deleted by {current_user.email}")
        return {"message": "Proforma invoice deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting proforma invoice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete proforma invoice"
        )

# Quotation
@router.get("/quotations/", response_model=List[QuotationInDB])
async def get_quotations(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all quotations"""
    query = db.query(Quotation)
    
    if status:
        query = query.filter(Quotation.status == status)
    
    quotations = query.offset(skip).limit(limit).all()
    return quotations

@router.post("/quotations/", response_model=QuotationInDB)
async def create_quotation(
    quotation: QuotationCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new quotation"""
    try:
        quotation_data = quotation.dict(exclude={'items'})
        quotation_data['created_by'] = current_user.id
        
        db_quotation = Quotation(**quotation_data)
        db.add(db_quotation)
        db.flush()
        
        for item_data in quotation.items:
            from app.models.vouchers import QuotationItem
            item = QuotationItem(
                quotation_id=db_quotation.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_quotation)
        
        if send_email and db_quotation.customer and db_quotation.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="quotation",
                voucher_id=db_quotation.id,
                recipient_email=db_quotation.customer.email,
                recipient_name=db_quotation.customer.name
            )
        
        logger.info(f"Quotation {quotation.voucher_number} created by {current_user.email}")
        return db_quotation
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating quotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quotation"
        )

@router.get("/quotations/{quotation_id}", response_model=QuotationInDB)
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get quotation by ID"""
    quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found"
        )
    return quotation

@router.put("/quotations/{quotation_id}", response_model=QuotationInDB)
async def update_quotation(
    quotation_id: int,
    quotation_update: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update quotation"""
    try:
        quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found"
            )
        
        update_data = quotation_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(quotation, field, value)
        
        if quotation_update.items is not None:
            from app.models.vouchers import QuotationItem
            db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).delete()
            for item_data in quotation_update.items:
                item = QuotationItem(
                    quotation_id=quotation_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(quotation)
        
        logger.info(f"Quotation {quotation.voucher_number} updated by {current_user.email}")
        return quotation
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating quotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quotation"
        )

@router.delete("/quotations/{quotation_id}")
async def delete_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete quotation"""
    try:
        quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found"
            )
        
        from app.models.vouchers import QuotationItem
        db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).delete()
        
        db.delete(quotation)
        db.commit()
        
        logger.info(f"Quotation {quotation.voucher_number} deleted by {current_user.email}")
        return {"message": "Quotation deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting quotation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quotation"
        )