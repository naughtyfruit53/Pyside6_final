from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User
from app.models.vouchers import (
    SalesVoucher, SalesOrder, DeliveryChallan, SalesReturn
)
from app.schemas.vouchers import (
    SalesVoucherCreate, SalesVoucherInDB, SalesVoucherUpdate,
    SalesOrderCreate, SalesOrderInDB, SalesOrderUpdate,
    DeliveryChallanCreate, DeliveryChallanInDB, DeliveryChallanUpdate,
    SalesReturnCreate, SalesReturnInDB, SalesReturnUpdate
)
from app.services.email_service import send_voucher_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Sales Vouchers by Type Endpoint (required by problem statement)
@router.get("/sales", response_model=List[SalesVoucherInDB])
async def get_sales_vouchers_by_type(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales vouchers filtered by type (problem statement requirement)"""
    query = db.query(SalesVoucher).filter(SalesVoucher.voucher_type == "sales")
    
    if status:
        query = query.filter(SalesVoucher.status == status)
    
    vouchers = query.offset(skip).limit(limit).all()
    return vouchers

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
        voucher_data = voucher.dict(exclude={'items'})
        voucher_data['created_by'] = current_user.id
        
        db_voucher = SalesVoucher(**voucher_data)
        db.add(db_voucher)
        db.flush()
        
        for item_data in voucher.items:
            from app.models.vouchers import SalesVoucherItem
            item = SalesVoucherItem(
                sales_voucher_id=db_voucher.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_voucher)
        
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

@router.put("/sales-vouchers/{voucher_id}", response_model=SalesVoucherInDB)
async def update_sales_voucher(
    voucher_id: int,
    voucher_update: SalesVoucherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update sales voucher"""
    try:
        voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales voucher not found"
            )
        
        update_data = voucher_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(voucher, field, value)
        
        if voucher_update.items is not None:
            from app.models.vouchers import SalesVoucherItem
            db.query(SalesVoucherItem).filter(
                SalesVoucherItem.sales_voucher_id == voucher_id
            ).delete()
            
            for item_data in voucher_update.items:
                item = SalesVoucherItem(
                    sales_voucher_id=voucher_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(voucher)
        
        logger.info(f"Sales voucher {voucher.voucher_number} updated by {current_user.email}")
        return voucher
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sales voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sales voucher"
        )

@router.delete("/sales-vouchers/{voucher_id}")
async def delete_sales_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete sales voucher"""
    try:
        voucher = db.query(SalesVoucher).filter(SalesVoucher.id == voucher_id).first()
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales voucher not found"
            )
        
        from app.models.vouchers import SalesVoucherItem
        db.query(SalesVoucherItem).filter(
            SalesVoucherItem.sales_voucher_id == voucher_id
        ).delete()
        
        db.delete(voucher)
        db.commit()
        
        logger.info(f"Sales voucher {voucher.voucher_number} deleted by {current_user.email}")
        return {"message": "Sales voucher deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting sales voucher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sales voucher"
        )

# Sales Orders
@router.get("/sales-orders/", response_model=List[SalesOrderInDB])
async def get_sales_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all sales orders"""
    query = db.query(SalesOrder)
    
    if status:
        query = query.filter(SalesOrder.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders

@router.post("/sales-orders/", response_model=SalesOrderInDB)
async def create_sales_order(
    order: SalesOrderCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new sales order"""
    try:
        order_data = order.dict(exclude={'items'})
        order_data['created_by'] = current_user.id
        
        db_order = SalesOrder(**order_data)
        db.add(db_order)
        db.flush()
        
        for item_data in order.items:
            from app.models.vouchers import SalesOrderItem
            item = SalesOrderItem(
                sales_order_id=db_order.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_order)
        
        if send_email and db_order.customer and db_order.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="sales_order",
                voucher_id=db_order.id,
                recipient_email=db_order.customer.email,
                recipient_name=db_order.customer.name
            )
        
        logger.info(f"Sales order {order.voucher_number} created by {current_user.email}")
        return db_order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sales order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sales order"
        )

@router.get("/sales-orders/{order_id}", response_model=SalesOrderInDB)
async def get_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales order by ID"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales order not found"
        )
    return order

@router.put("/sales-orders/{order_id}", response_model=SalesOrderInDB)
async def update_sales_order(
    order_id: int,
    order_update: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update sales order"""
    try:
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        update_data = order_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(order, field, value)
        
        if order_update.items is not None:
            from app.models.vouchers import SalesOrderItem
            db.query(SalesOrderItem).filter(
                SalesOrderItem.sales_order_id == order_id
            ).delete()
            
            for item_data in order_update.items:
                item = SalesOrderItem(
                    sales_order_id=order_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(order)
        
        logger.info(f"Sales order {order.voucher_number} updated by {current_user.email}")
        return order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sales order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sales order"
        )

@router.delete("/sales-orders/{order_id}")
async def delete_sales_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete sales order"""
    try:
        order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales order not found"
            )
        
        from app.models.vouchers import SalesOrderItem
        db.query(SalesOrderItem).filter(
            SalesOrderItem.sales_order_id == order_id
        ).delete()
        
        db.delete(order)
        db.commit()
        
        logger.info(f"Sales order {order.voucher_number} deleted by {current_user.email}")
        return {"message": "Sales order deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting sales order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sales order"
        )

# Delivery Challan
@router.get("/delivery-challan/", response_model=List[DeliveryChallanInDB])
async def get_delivery_challans(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(DeliveryChallan)
    
    if status:
        query = query.filter(DeliveryChallan.status == status)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/delivery-challan/", response_model=DeliveryChallanInDB)
async def create_delivery_challan(
    challan: DeliveryChallanCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        challan_data = challan.dict(exclude={'items'})
        challan_data['created_by'] = current_user.id
        
        db_challan = DeliveryChallan(**challan_data)
        db.add(db_challan)
        db.flush()
        
        for item_data in challan.items:
            from app.models.vouchers import DeliveryChallanItem
            item = DeliveryChallanItem(
                delivery_challan_id=db_challan.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_challan)
        
        if send_email and db_challan.customer and db_challan.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="delivery_challan",
                voucher_id=db_challan.id,
                recipient_email=db_challan.customer.email,
                recipient_name=db_challan.customer.name
            )
        
        logger.info(f"Delivery Challan {challan.voucher_number} created by {current_user.email}")
        return db_challan
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating Delivery Challan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Delivery Challan")

@router.get("/delivery-challan/{challan_id}", response_model=DeliveryChallanInDB)
async def get_delivery_challan(
    challan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    challan = db.query(DeliveryChallan).filter(DeliveryChallan.id == challan_id).first()
    if not challan:
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
    return challan

@router.put("/delivery-challan/{challan_id}", response_model=DeliveryChallanInDB)
async def update_delivery_challan(
    challan_id: int,
    challan_update: DeliveryChallanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        challan = db.query(DeliveryChallan).filter(DeliveryChallan.id == challan_id).first()
        if not challan:
            raise HTTPException(status_code=404, detail="Delivery Challan not found")
        
        update_data = challan_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(challan, field, value)
        
        if challan_update.items is not None:
            from app.models.vouchers import DeliveryChallanItem
            db.query(DeliveryChallanItem).filter(
                DeliveryChallanItem.delivery_challan_id == challan_id
            ).delete()
            
            for item_data in challan_update.items:
                item = DeliveryChallanItem(
                    delivery_challan_id=challan_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(challan)
        
        logger.info(f"Delivery Challan {challan.voucher_number} updated by {current_user.email}")
        return challan
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating Delivery Challan: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Delivery Challan")

@router.delete("/delivery-challan/{challan_id}")
async def delete_delivery_challan(
    challan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        challan = db.query(DeliveryChallan).filter(DeliveryChallan.id == challan_id).first()
        if not challan:
            raise HTTPException(status_code=404, detail="Delivery Challan not found")
        
        from app.models.vouchers import DeliveryChallanItem
        db.query(DeliveryChallanItem).filter(
            DeliveryChallanItem.delivery_challan_id == challan_id
        ).delete()
        
        db.delete(challan)
        db.commit()
        
        logger.info(f"Delivery Challan {challan.voucher_number} deleted by {current_user.email}")
        return {"message": "Delivery Challan deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting Delivery Challan: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete Delivery Challan")

# Sales Returns
@router.get("/sales-returns/", response_model=List[SalesReturnInDB])
async def get_sales_returns(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all sales returns"""
    query = db.query(SalesReturn)
    
    if status:
        query = query.filter(SalesReturn.status == status)
    
    returns = query.offset(skip).limit(limit).all()
    return returns

@router.post("/sales-returns/", response_model=SalesReturnInDB)
async def create_sales_return(
    return_data: SalesReturnCreate,
    background_tasks: BackgroundTasks,
    send_email: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new sales return"""
    try:
        data = return_data.dict(exclude={'items'})
        data['created_by'] = current_user.id
        
        db_return = SalesReturn(**data)
        db.add(db_return)
        db.flush()
        
        for item_data in return_data.items:
            from app.models.vouchers import SalesReturnItem
            item = SalesReturnItem(
                sales_return_id=db_return.id,
                **item_data.dict()
            )
            db.add(item)
        
        db.commit()
        db.refresh(db_return)
        
        if send_email and db_return.customer and db_return.customer.email:
            background_tasks.add_task(
                send_voucher_email,
                voucher_type="sales_return",
                voucher_id=db_return.id,
                recipient_email=db_return.customer.email,
                recipient_name=db_return.customer.name
            )
        
        logger.info(f"Sales return {return_data.voucher_number} created by {current_user.email}")
        return db_return
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sales return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sales return"
        )

@router.get("/sales-returns/{return_id}", response_model=SalesReturnInDB)
async def get_sales_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales return by ID"""
    return_ = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
    if not return_:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found"
        )
    return return_

@router.put("/sales-returns/{return_id}", response_model=SalesReturnInDB)
async def update_sales_return(
    return_id: int,
    return_update: SalesReturnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update sales return"""
    try:
        return_ = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
        if not return_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales return not found"
            )
        
        update_data = return_update.dict(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(return_, field, value)
        
        if return_update.items is not None:
            from app.models.vouchers import SalesReturnItem
            db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).delete()
            for item_data in return_update.items:
                item = SalesReturnItem(
                    sales_return_id=return_id,
                    **item_data.dict()
                )
                db.add(item)
        
        db.commit()
        db.refresh(return_)
        
        logger.info(f"Sales return {return_.voucher_number} updated by {current_user.email}")
        return return_
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sales return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update sales return"
        )

@router.delete("/sales-returns/{return_id}")
async def delete_sales_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete sales return"""
    try:
        return_ = db.query(SalesReturn).filter(SalesReturn.id == return_id).first()
        if not return_:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sales return not found"
            )
        
        from app.models.vouchers import SalesReturnItem
        db.query(SalesReturnItem).filter(SalesReturnItem.sales_return_id == return_id).delete()
        
        db.delete(return_)
        db.commit()
        
        logger.info(f"Sales return {return_.voucher_number} deleted by {current_user.email}")
        return {"message": "Sales return deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting sales return: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete sales return"
        )