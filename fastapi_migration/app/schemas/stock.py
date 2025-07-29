from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime  # Added import

class StockBase(BaseModel):
    product_id: int
    quantity: float
    unit: str
    location: Optional[str] = None

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None

class StockInDB(StockBase):
    id: int
    organization_id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2+

class StockBulkItem(BaseModel):
    product_name: str
    hsn_code: Optional[str] = None
    unit: str
    quantity: float = 0.0
    location: Optional[str] = None
    unit_price: Optional[float] = None
    gst_rate: Optional[float] = None
    reorder_level: Optional[int] = None

class BulkStockRequest(BaseModel):  # New model for the request body
    items: List[StockBulkItem]

class BulkImportResponse(BaseModel):
    message: str
    total_processed: int
    created: int
    updated: int
    errors: List[str] = []