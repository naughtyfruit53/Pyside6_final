from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import (
    PurchaseVoucher, PurchaseOrder, GoodsReceiptNote, PurchaseReturn
)
from app.schemas.vouchers import (
    PurchaseVoucherCreate, PurchaseVoucherInDB, PurchaseVoucherUpdate,
    PurchaseOrderCreate, PurchaseOrderInDB, PurchaseOrderUpdate,
    GRNCreate, GRNInDB, GRNUpdate,
    PurchaseReturnCreate, PurchaseReturnInDB, PurchaseReturnUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Purchase Vouchers
@router.get("/purchase-vouchers", response_model=List[PurchaseVoucherInDB])
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

@router.post("/purchase-vouchers", response_model=PurchaseVoucherInDB)
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