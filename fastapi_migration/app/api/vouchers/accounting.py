# revised fastapi_migration/app/api/vouchers/accounting.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import (
    PaymentVoucher, ReceiptVoucher, ContraVoucher, JournalVoucher, InterDepartmentVoucher
)
from app.schemas.vouchers import (
    PaymentVoucherCreate, PaymentVoucherInDB, PaymentVoucherUpdate,
    ReceiptVoucherCreate, ReceiptVoucherInDB, ReceiptVoucherUpdate,
    ContraVoucherCreate, ContraVoucherInDB, ContraVoucherUpdate,
    JournalVoucherCreate, JournalVoucherInDB, JournalVoucherUpdate,
    InterDepartmentVoucherCreate, InterDepartmentVoucherInDB, InterDepartmentVoucherUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Payment Vouchers
@router.get("/payment-vouchers/", response_model=List[PaymentVoucherInDB])
async def get_payment_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(PaymentVoucher)
    
    if status:
        query = query.filter(PaymentVoucher.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/payment-vouchers/", response_model=PaymentVoucherInDB)
async def create_payment_voucher(
    voucher: PaymentVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher_data = voucher.dict()
        voucher_data['created_by'] = current_user.id
        
        db_voucher = PaymentVoucher(**voucher_data)
        db.add(db_voucher)
        db.commit()
        db.refresh(db_voucher)
        
        if send_email and db_voucher.vendor and db_voucher.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="payment_voucher",
                voucher_id=db_voucher.id,
                recipient_email=db_voucher.vendor.email,
                recipient_name=db_voucher.vendor.name
            )
        
        logger.info(f"Payment voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment voucher")

@router.get("/payment-vouchers/{voucher_id}", response_model=PaymentVoucherInDB)
async def get_payment_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    voucher = db.query(PaymentVoucher).filter(PaymentVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Payment voucher not found")
    return voucher

@router.put("/payment-vouchers/{voucher_id}", response_model=PaymentVoucherInDB)
async def update_payment_voucher(
    voucher_id: int,
    voucher_update: PaymentVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(PaymentVoucher).filter(PaymentVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Payment voucher not found")
        
        update_data = voucher_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Payment voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating payment voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to update payment voucher")

@router.delete("/payment-vouchers/{voucher_id}")
async def delete_payment_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(PaymentVoucher).filter(PaymentVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Payment voucher not found")
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Payment voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Payment voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting payment voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete payment voucher")

# Receipt Vouchers
@router.get("/receipt-vouchers/", response_model=List[ReceiptVoucherInDB])
async def get_receipt_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(ReceiptVoucher)
    
    if status:
        query = query.filter(ReceiptVoucher.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/receipt-vouchers/", response_model=ReceiptVoucherInDB)
async def create_receipt_voucher(
    voucher: ReceiptVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher_data = voucher.dict()
        voucher_data['created_by'] = current_user.id
        
        db_voucher = ReceiptVoucher(**voucher_data)
        db.add(db_voucher)
        db.commit()
        db.refresh(db_voucher)
        
        if send_email and db_voucher.customer and db_voucher.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="receipt_voucher",
                voucher_id=db_voucher.id,
                recipient_email=db_voucher.customer.email,
                recipient_name=db_voucher.customer.name
            )
        
        logger.info(f"Receipt voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating receipt voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to create receipt voucher")

@router.get("/receipt-vouchers/{voucher_id}", response_model=ReceiptVoucherInDB)
async def get_receipt_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    voucher = db.query(ReceiptVoucher).filter(ReceiptVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Receipt voucher not found")
    return voucher

@router.put("/receipt-vouchers/{voucher_id}", response_model=ReceiptVoucherInDB)
async def update_receipt_voucher(
    voucher_id: int,
    voucher_update: ReceiptVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(ReceiptVoucher).filter(ReceiptVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Receipt voucher not found")
        
        update_data = voucher_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Receipt voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating receipt voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to update receipt voucher")

@router.delete("/receipt-vouchers/{voucher_id}")
async def delete_receipt_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(ReceiptVoucher).filter(ReceiptVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Receipt voucher not found")
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Receipt voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Receipt voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting receipt voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete receipt voucher")

# Contra Vouchers
@router.get("/contra-vouchers/", response_model=List[ContraVoucherInDB])
async def get_contra_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(ContraVoucher)
    
    if status:
        query = query.filter(ContraVoucher.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/contra-vouchers/", response_model=ContraVoucherInDB)
async def create_contra_voucher(
    voucher: ContraVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher_data = voucher.dict()
        voucher_data['created_by'] = current_user.id
        
        db_voucher = ContraVoucher(**voucher_data)
        db.add(db_voucher)
        db.commit()
        db.refresh(db_voucher)
        
        # No default recipient for contra, rely on custom email if needed
        
        logger.info(f"Contra voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating contra voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to create contra voucher")

@router.get("/contra-vouchers/{voucher_id}", response_model=ContraVoucherInDB)
async def get_contra_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    voucher = db.query(ContraVoucher).filter(ContraVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Contra voucher not found")
    return voucher

@router.put("/contra-vouchers/{voucher_id}", response_model=ContraVoucherInDB)
async def update_contra_voucher(
    voucher_id: int,
    voucher_update: ContraVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(ContraVoucher).filter(ContraVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Contra voucher not found")
        
        update_data = voucher_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Contra voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating contra voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to update contra voucher")

@router.delete("/contra-vouchers/{voucher_id}")
async def delete_contra_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(ContraVoucher).filter(ContraVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Contra voucher not found")
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Contra voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Contra voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting contra voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete contra voucher")

# Journal Vouchers
@router.get("/journal-vouchers/", response_model=List[JournalVoucherInDB])
async def get_journal_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(JournalVoucher)
    
    if status:
        query = query.filter(JournalVoucher.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/journal-vouchers/", response_model=JournalVoucherInDB)
async def create_journal_voucher(
    voucher: JournalVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher_data = voucher.dict()
        voucher_data['created_by'] = current_user.id
        
        db_voucher = JournalVoucher(**voucher_data)
        db.add(db_voucher)
        db.commit()
        db.refresh(db_voucher)
        
        # No default recipient for journal, rely on custom email if needed
        
        logger.info(f"Journal voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating journal voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to create journal voucher")

@router.get("/journal-vouchers/{voucher_id}", response_model=JournalVoucherInDB)
async def get_journal_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    voucher = db.query(JournalVoucher).filter(JournalVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Journal voucher not found")
    return voucher

@router.put("/journal-vouchers/{voucher_id}", response_model=JournalVoucherInDB)
async def update_journal_voucher(
    voucher_id: int,
    voucher_update: JournalVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(JournalVoucher).filter(JournalVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Journal voucher not found")
        
        update_data = voucher_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Journal voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating journal voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to update journal voucher")

@router.delete("/journal-vouchers/{voucher_id}")
async def delete_journal_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(JournalVoucher).filter(JournalVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Journal voucher not found")
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Journal voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Journal voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting journal voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete journal voucher")

# Inter Department Vouchers
@router.get("/inter-department-vouchers/", response_model=List[InterDepartmentVoucherInDB])
async def get_inter_department_vouchers(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(InterDepartmentVoucher)
    
    if status:
        query = query.filter(InterDepartmentVoucher.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/inter-department-vouchers/", response_model=InterDepartmentVoucherInDB)
async def create_inter_department_voucher(
    voucher: InterDepartmentVoucherCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher_data = voucher.dict(exclude={'items'})
        voucher_data['created_by'] = current_user.id
        
        db_voucher = InterDepartmentVoucher(**voucher_data)
        db.add(db_voucher)
        db.flush()
        
        for item_data in voucher.items:
            from app.models.vouchers import InterDepartmentVoucherItem
            item = InterDepartmentVoucherItem(
                inter_department_voucher_id=db_voucher.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_voucher)
        
        # No default recipient for inter department, rely on custom email if needed
        
        logger.info(f"Inter department voucher {voucher.voucher_number} created by {current_user.email}")
        return db_voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating inter department voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to create inter department voucher")

@router.get("/inter-department-vouchers/{voucher_id}", response_model=InterDepartmentVoucherInDB)
async def get_inter_department_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    voucher = db.query(InterDepartmentVoucher).filter(InterDepartmentVoucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(status_code=404, detail="Inter department voucher not found")
    return voucher

@router.put("/inter-department-vouchers/{voucher_id}", response_model=InterDepartmentVoucherInDB)
async def update_inter_department_voucher(
    voucher_id: int,
    voucher_update: InterDepartmentVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(InterDepartmentVoucher).filter(InterDepartmentVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Inter department voucher not found")
        
        update_data = voucher_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        if voucher_update.items is not None:
            from app.models.vouchers import InterDepartmentVoucherItem
            db.query(InterDepartmentVoucherItem).filter(
                InterDepartmentVoucherItem.inter_department_voucher_id == voucher_id
            ).delete()
            
            for item_data in voucher_update.items:
                item = InterDepartmentVoucherItem(
                    inter_department_voucher_id=voucher_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Inter department voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating inter department voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to update inter department voucher")

@router.delete("/inter-department-vouchers/{voucher_id}")
async def delete_inter_department_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        voucher = db.query(InterDepartmentVoucher).filter(InterDepartmentVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(status_code=404, detail="Inter department voucher not found")
        
        from app.models.vouchers import InterDepartmentVoucherItem
        db.query(InterDepartmentVoucherItem).filter(
            InterDepartmentVoucherItem.inter_department_voucher_id == voucher_id
        ).delete()
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Inter department voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Inter department voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting inter department voucher: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete inter department voucher")