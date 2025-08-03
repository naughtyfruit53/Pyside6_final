from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import CreditNote, DebitNote
from app.schemas.vouchers import (
    CreditNoteCreate, CreditNoteInDB, CreditNoteUpdate,
    DebitNoteCreate, DebitNoteInDB, DebitNoteUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Credit Notes
@router.get("/credit-notes/", response_model=List[CreditNoteInDB])
async def get_credit_notes(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all credit notes"""
    query = db.query(CreditNote)
    
    if status:
        query = query.filter(CreditNote.status == status)
    
    notes = query.offset(skip).limit(limit).all()
    return notes

@router.post("/credit-notes/", response_model=CreditNoteInDB)
async def create_credit_note(
    note: CreditNoteCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new credit note"""
    try:
        note_data = note.dict(exclude={'items'})
        note_data['created_by'] = current_user.id
        
        db_note = CreditNote(**note_data)
        db.add(db_note)
        db.flush()
        
        for item_data in note.items:
            from app.models.vouchers import CreditNoteItem
            item = CreditNoteItem(
                credit_note_id=db_note.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_note)
        
        if send_email and db_note.customer and db_note.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="credit_note",
                voucher_id=db_note.id,
                recipient_email=db_note.customer.email,
                recipient_name=db_note.customer.name
            )
        
        logger.info(f"Credit note {note.voucher_number} created by {current_user.email}")
        return db_note
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating credit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create credit note"
        )

@router.get("/credit-notes/{note_id}", response_model=CreditNoteInDB)
async def get_credit_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get credit note by ID"""
    note = db.query(CreditNote).filter(CreditNote.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit note not found"
        )
    return note

@router.put("/credit-notes/{note_id}", response_model=CreditNoteInDB)
async def update_credit_note(
    note_id: int,
    note_update: CreditNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update credit note"""
    try:
        note = db.query(CreditNote).filter(CreditNote.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit note not found"
            )
        
        update_data = note_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(note, field, value)
        
        if note_update.items is not None:
            from app.models.vouchers import CreditNoteItem
            db.query(CreditNoteItem).filter(CreditNoteItem.credit_note_id == note_id).delete()
            for item_data in note_update.items:
                item = CreditNoteItem(
                    credit_note_id=note_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(note)
        
        logger.info(f"Credit note {note.voucher_number} updated by {current_user.email}")
        return note
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating credit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credit note"
        )

@router.delete("/credit-notes/{note_id}")
async def delete_credit_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete credit note"""
    try:
        note = db.query(CreditNote).filter(CreditNote.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credit note not found"
            )
        
        from app.models.vouchers import CreditNoteItem
        db.query(CreditNoteItem).filter(CreditNoteItem.credit_note_id == note_id).delete()
        
        db.delete(note)
        db.commit()
        
        logger.info(f"Credit note {note.voucher_number} deleted by {current_user.email}")
        return {"message": "Credit note deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting credit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credit note"
        )

# Debit Notes
@router.get("/debit-notes/", response_model=List[DebitNoteInDB])
async def get_debit_notes(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all debit notes"""
    query = db.query(DebitNote)
    
    if status:
        query = query.filter(DebitNote.status == status)
    
    notes = query.offset(skip).limit(limit).all()
    return notes

@router.post("/debit-notes/", response_model=DebitNoteInDB)
async def create_debit_note(
    note: DebitNoteCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new debit note"""
    try:
        note_data = note.dict(exclude={'items'})
        note_data['created_by'] = current_user.id
        
        db_note = DebitNote(**note_data)
        db.add(db_note)
        db.flush()
        
        for item_data in note.items:
            from app.models.vouchers import DebitNoteItem
            item = DebitNoteItem(
                debit_note_id=db_note.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_note)
        
        if send_email and db_note.vendor and db_note.vendor.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="debit_note",
                voucher_id=db_note.id,
                recipient_email=db_note.vendor.email,
                recipient_name=db_note.vendor.name
            )
        
        logger.info(f"Debit note {note.voucher_number} created by {current_user.email}")
        return db_note
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating debit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create debit note"
        )

@router.get("/debit-notes/{note_id}", response_model=DebitNoteInDB)
async def get_debit_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get debit note by ID"""
    note = db.query(DebitNote).filter(DebitNote.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debit note not found"
        )
    return note

@router.put("/debit-notes/{note_id}", response_model=DebitNoteInDB)
async def update_debit_note(
    note_id: int,
    note_update: DebitNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update debit note"""
    try:
        note = db.query(DebitNote).filter(DebitNote.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debit note not found"
            )
        
        update_data = note_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(note, field, value)
        
        if note_update.items is not None:
            from app.models.vouchers import DebitNoteItem
            db.query(DebitNoteItem).filter(DebitNoteItem.debit_note_id == note_id).delete()
            for item_data in note_update.items:
                item = DebitNoteItem(
                    debit_note_id=note_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(note)
        
        logger.info(f"Debit note {note.voucher_number} updated by {current_user.email}")
        return note
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating debit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update debit note"
        )

@router.delete("/debit-notes/{note_id}")
async def delete_debit_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete debit note"""
    try:
        note = db.query(DebitNote).filter(DebitNote.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Debit note not found"
            )
        
        from app.models.vouchers import DebitNoteItem
        db.query(DebitNoteItem).filter(DebitNoteItem.debit_note_id == note_id).delete()
        
        db.delete(note)
        db.commit()
        
        logger.info(f"Debit note {note.voucher_number} deleted by {current_user.email}")
        return {"message": "Debit note deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting debit note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete debit note"
        )