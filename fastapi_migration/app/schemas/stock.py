"""
Enhanced Stock Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class StockBase(BaseModel):
    product_id: int
    quantity: float
    unit: str
    location: Optional[str] = None

class StockCreate(StockBase):
    """Schema for creating stock entry with enhanced validation"""
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Unit cannot be empty')
        return v.strip().upper()
    
    @validator('product_id')
    def validate_product_id(cls, v):
        if v <= 0:
            raise ValueError('Product ID must be a positive integer')
        return v

class StockUpdate(BaseModel):
    """Schema for updating stock with enhanced validation"""
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v < 0:
            raise ValueError('Quantity cannot be negative')
        return v
    
    @validator('unit')
    def validate_unit(cls, v):
        if v is not None and len(v.strip()) < 1:
            raise ValueError('Unit cannot be empty')
        return v.strip().upper() if v else v

class StockInDB(StockBase):
    """Schema for stock data from database"""
    id: int
    organization_id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True

class StockWithProduct(StockInDB):
    """Stock data with product information"""
    product_name: str
    product_hsn_code: Optional[str] = None
    product_part_number: Optional[str] = None
    unit_price: float
    reorder_level: int

# Bulk import schemas
class StockBulkItem(BaseModel):
    """Individual item for bulk stock operations with enhanced validation"""
    product_name: str
    hsn_code: Optional[str] = None
    part_number: Optional[str] = None
    unit: str
    quantity: float = 0.0
    location: Optional[str] = None
    unit_price: Optional[float] = None
    gst_rate: Optional[float] = None
    reorder_level: Optional[int] = None
    
    @validator('product_name')
    def validate_product_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Unit cannot be empty')
        return v.strip().upper()
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Unit price cannot be negative')
        return v
    
    @validator('gst_rate')
    def validate_gst_rate(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('GST rate must be between 0 and 100')
        return v
    
    @validator('reorder_level')
    def validate_reorder_level(cls, v):
        if v is not None and v < 0:
            raise ValueError('Reorder level cannot be negative')
        return v

class BulkStockRequest(BaseModel):
    """Schema for bulk stock request body"""
    items: List[StockBulkItem]
    
    @validator('items')
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError('At least one item is required')
        return v

class BulkImportError(BaseModel):
    """Detailed error information for bulk imports"""
    row: int
    field: Optional[str] = None
    value: Optional[str] = None
    error: str
    error_code: Optional[str] = None

class BulkImportResponse(BaseModel):
    """Enhanced response for bulk import operations"""
    message: str
    total_processed: int
    created: int
    updated: int
    skipped: int = 0
    errors: List[str] = []
    detailed_errors: List[BulkImportError] = []
    warnings: List[str] = []
    processing_time_seconds: Optional[float] = None

# Stock adjustment schemas
class StockAdjustment(BaseModel):
    """Schema for stock adjustments"""
    quantity_change: float
    reason: str = "Manual adjustment"
    reference_number: Optional[str] = None
    
    @validator('reason')
    def validate_reason(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Reason must be at least 3 characters long')
        return v.strip()

class StockAdjustmentResponse(BaseModel):
    """Response for stock adjustment operations"""
    message: str
    previous_quantity: float
    quantity_change: float
    new_quantity: float
    timestamp: datetime = datetime.utcnow()

# Low stock reporting
class LowStockItem(StockWithProduct):
    """Stock item that is below reorder level"""
    shortage: float  # How much below reorder level
    
class LowStockReport(BaseModel):
    """Report of items with low stock"""
    items: List[LowStockItem]
    total_items: int
    critical_items: int  # Items with zero stock
    generated_at: datetime = datetime.utcnow()

# Export schemas
class StockExportOptions(BaseModel):
    """Options for stock export"""
    include_zero_stock: bool = False
    include_inactive_products: bool = False
    location_filter: Optional[str] = None
    product_category_filter: Optional[str] = None

class StockListResponse(BaseModel):
    """Response schema for stock list with pagination"""
    items: List[StockWithProduct]
    total: int
    page: int = 1
    per_page: int = 100
    has_next: bool = False
    has_prev: bool = False