from fastapi import APIRouter

from .purchase import router as purchase_router
from .sales import router as sales_router
from .quotes import router as quotes_router
from .notes import router as notes_router
from .accounting import router as accounting_router
from .email import router as email_router

router = APIRouter()
router.include_router(purchase_router)
router.include_router(sales_router)
router.include_router(quotes_router)
router.include_router(notes_router)
router.include_router(accounting_router)
router.include_router(email_router)