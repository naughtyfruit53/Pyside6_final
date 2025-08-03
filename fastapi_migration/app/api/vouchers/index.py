"""
Vouchers index module - consolidates all voucher-related endpoints
This module provides a single router that includes all voucher functionality.
"""

from fastapi import APIRouter

from .purchase import router as purchase_router
from .sales import router as sales_router
from .quotes import router as quotes_router
from .notes import router as notes_router
from .accounting import router as accounting_router
from .email import router as email_router

# Create main vouchers router
router = APIRouter()

# Include all voucher sub-routers
router.include_router(purchase_router, tags=["purchase-vouchers"])
router.include_router(sales_router, tags=["sales-vouchers"])
router.include_router(quotes_router, tags=["quotes"])
router.include_router(notes_router, tags=["notes"])
router.include_router(accounting_router, tags=["accounting-vouchers"])
router.include_router(email_router, tags=["voucher-emails"])