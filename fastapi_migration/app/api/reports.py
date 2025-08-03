from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.core.database import get_db
from app.api.v1.auth import get_current_active_user
from app.models.base import User, Product, Stock, Vendor, Customer
from app.models.vouchers import (
    PurchaseVoucher, SalesVoucher, PurchaseOrder, SalesOrder,
    GoodsReceiptNote, DeliveryChallan
)
from app.core.tenant import require_current_organization_id, TenantQueryMixin
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics"""
    try:
        org_id = require_current_organization_id()
        
        # Count masters
        vendors_count = TenantQueryMixin.filter_by_tenant(
            db.query(Vendor), Vendor, org_id
        ).filter(Vendor.is_active == True).count()
        
        customers_count = TenantQueryMixin.filter_by_tenant(
            db.query(Customer), Customer, org_id
        ).filter(Customer.is_active == True).count()
        
        products_count = TenantQueryMixin.filter_by_tenant(
            db.query(Product), Product, org_id
        ).filter(Product.is_active == True).count()
        
        # Count vouchers
        purchase_vouchers_count = TenantQueryMixin.filter_by_tenant(
            db.query(PurchaseVoucher), PurchaseVoucher, org_id
        ).count()
        
        sales_vouchers_count = TenantQueryMixin.filter_by_tenant(
            db.query(SalesVoucher), SalesVoucher, org_id
        ).count()
        
        # Low stock items
        low_stock_query = TenantQueryMixin.filter_by_tenant(
            db.query(Stock), Stock, org_id
        ).join(Product).filter(
            Stock.quantity <= Product.reorder_level,
            Product.is_active == True
        )
        low_stock_count = low_stock_query.count()
        
        return {
            "masters": {
                "vendors": vendors_count,
                "customers": customers_count,
                "products": products_count
            },
            "vouchers": {
                "purchase_vouchers": purchase_vouchers_count,
                "sales_vouchers": sales_vouchers_count
            },
            "inventory": {
                "low_stock_items": low_stock_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )

@router.get("/sales-report")
async def get_sales_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sales report"""
    try:
        org_id = require_current_organization_id()
        
        query = TenantQueryMixin.filter_by_tenant(
            db.query(SalesVoucher), SalesVoucher, org_id
        ).join(Customer)
        
        if start_date:
            query = query.filter(SalesVoucher.date >= start_date)
        if end_date:
            query = query.filter(SalesVoucher.date <= end_date)
        if customer_id:
            query = query.filter(SalesVoucher.customer_id == customer_id)
        
        sales_vouchers = query.all()
        
        total_sales = sum(voucher.total_amount for voucher in sales_vouchers)
        total_gst = sum(
            voucher.cgst_amount + voucher.sgst_amount + voucher.igst_amount 
            for voucher in sales_vouchers
        )
        
        return {
            "vouchers": [
                {
                    "id": voucher.id,
                    "voucher_number": voucher.voucher_number,
                    "date": voucher.date,
                    "customer_name": voucher.customer.name,
                    "total_amount": voucher.total_amount,
                    "gst_amount": voucher.cgst_amount + voucher.sgst_amount + voucher.igst_amount,
                    "status": voucher.status
                }
                for voucher in sales_vouchers
            ],
            "summary": {
                "total_vouchers": len(sales_vouchers),
                "total_sales": total_sales,
                "total_gst": total_gst
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sales report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sales report"
        )

@router.get("/purchase-report")
async def get_purchase_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get purchase report"""
    try:
        org_id = require_current_organization_id()
        
        query = TenantQueryMixin.filter_by_tenant(
            db.query(PurchaseVoucher), PurchaseVoucher, org_id
        ).join(Vendor)
        
        if start_date:
            query = query.filter(PurchaseVoucher.date >= start_date)
        if end_date:
            query = query.filter(PurchaseVoucher.date <= end_date)
        if vendor_id:
            query = query.filter(PurchaseVoucher.vendor_id == vendor_id)
        
        purchase_vouchers = query.all()
        
        total_purchases = sum(voucher.total_amount for voucher in purchase_vouchers)
        total_gst = sum(
            voucher.cgst_amount + voucher.sgst_amount + voucher.igst_amount 
            for voucher in purchase_vouchers
        )
        
        return {
            "vouchers": [
                {
                    "id": voucher.id,
                    "voucher_number": voucher.voucher_number,
                    "date": voucher.date,
                    "vendor_name": voucher.vendor.name,
                    "total_amount": voucher.total_amount,
                    "gst_amount": voucher.cgst_amount + voucher.sgst_amount + voucher.igst_amount,
                    "status": voucher.status
                }
                for voucher in purchase_vouchers
            ],
            "summary": {
                "total_vouchers": len(purchase_vouchers),
                "total_purchases": total_purchases,
                "total_gst": total_gst
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting purchase report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get purchase report"
        )

@router.get("/inventory-report")
async def get_inventory_report(
    low_stock_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get inventory report"""
    try:
        org_id = require_current_organization_id()
        
        query = TenantQueryMixin.filter_by_tenant(
            db.query(Stock), Stock, org_id
        ).join(Product).filter(Product.is_active == True)
        
        if low_stock_only:
            query = query.filter(Stock.quantity <= Product.reorder_level)
        
        stock_items = query.all()
        
        total_value = sum(
            item.quantity * item.product.unit_price 
            for item in stock_items if item.product
        )
        
        return {
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else "Unknown",
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.product.unit_price if item.product else 0,
                    "total_value": item.quantity * (item.product.unit_price if item.product else 0),
                    "reorder_level": item.product.reorder_level if item.product else 0,
                    "is_low_stock": item.quantity <= (item.product.reorder_level if item.product else 0)
                }
                for item in stock_items
            ],
            "summary": {
                "total_items": len(stock_items),
                "total_value": total_value,
                "low_stock_items": sum(
                    1 for item in stock_items 
                    if item.product and item.quantity <= item.product.reorder_level
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting inventory report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get inventory report"
        )

@router.get("/pending-orders")
async def get_pending_orders(
    order_type: str = "all",  # all, purchase, sales
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get pending orders report"""
    try:
        org_id = require_current_organization_id()
        
        pending_orders = []
        
        if order_type in ["all", "purchase"]:
            purchase_orders = TenantQueryMixin.filter_by_tenant(
                db.query(PurchaseOrder), PurchaseOrder, org_id
            ).filter(PurchaseOrder.status.in_(["draft", "pending"])).all()
            
            for order in purchase_orders:
                pending_orders.append({
                    "id": order.id,
                    "type": "Purchase Order",
                    "number": order.voucher_number,
                    "date": order.date,
                    "party": order.vendor.name if order.vendor else "Unknown",
                    "amount": order.total_amount,
                    "status": order.status
                })
        
        if order_type in ["all", "sales"]:
            sales_orders = TenantQueryMixin.filter_by_tenant(
                db.query(SalesOrder), SalesOrder, org_id
            ).filter(SalesOrder.status.in_(["draft", "pending"])).all()
            
            for order in sales_orders:
                pending_orders.append({
                    "id": order.id,
                    "type": "Sales Order",
                    "number": order.voucher_number,
                    "date": order.date,
                    "party": order.customer.name if order.customer else "Unknown",
                    "amount": order.total_amount,
                    "status": order.status
                })
        
        # Sort by date
        pending_orders.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "orders": pending_orders,
            "summary": {
                "total_orders": len(pending_orders),
                "total_value": sum(order["amount"] for order in pending_orders)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting pending orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending orders"
        )