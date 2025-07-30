"""
Company Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    state_code: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    contact_number: str
    email: Optional[EmailStr] = None

class CompanyCreate(CompanyBase):
    """Schema for creating a new company with enhanced validation"""
    
    @validator('pin_code')
    def validate_pin_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Pin code must be exactly 6 digits')
        return v

    @validator('state_code')
    def validate_state_code(cls, v):
        if not v.isdigit() or len(v) != 2:
            raise ValueError('State code must be exactly 2 digits')
        return v
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        # Remove any spaces or special characters for validation
        clean_number = ''.join(filter(str.isdigit, v))
        if len(clean_number) < 10:
            raise ValueError('Contact number must contain at least 10 digits')
        return v
    
    @validator('gst_number')
    def validate_gst_number(cls, v):
        if v and len(v) != 15:
            raise ValueError('GST number must be exactly 15 characters')
        return v
    
    @validator('pan_number')
    def validate_pan_number(cls, v):
        if v and len(v) != 10:
            raise ValueError('PAN number must be exactly 10 characters')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()

class CompanyUpdate(BaseModel):
    """Schema for updating company details"""
    name: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    state_code: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    
    @validator('pin_code')
    def validate_pin_code(cls, v):
        if v is not None and (not v.isdigit() or len(v) != 6):
            raise ValueError('Pin code must be exactly 6 digits')
        return v

    @validator('state_code')
    def validate_state_code(cls, v):
        if v is not None and (not v.isdigit() or len(v) != 2):
            raise ValueError('State code must be exactly 2 digits')
        return v
    
    @validator('contact_number')
    def validate_contact_number(cls, v):
        if v is not None:
            clean_number = ''.join(filter(str.isdigit, v))
            if len(clean_number) < 10:
                raise ValueError('Contact number must contain at least 10 digits')
        return v
    
    @validator('gst_number')
    def validate_gst_number(cls, v):
        if v is not None and v != "" and len(v) != 15:
            raise ValueError('GST number must be exactly 15 characters')
        return v
    
    @validator('pan_number')
    def validate_pan_number(cls, v):
        if v is not None and v != "" and len(v) != 10:
            raise ValueError('PAN number must be exactly 10 characters')
        return v

class CompanyInDB(CompanyBase):
    """Schema for company data from database"""
    id: int
    organization_id: int
    logo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CompanyResponse(CompanyInDB):
    """Enhanced response schema with additional metadata"""
    pass

class CompanyListResponse(BaseModel):
    """Response schema for company list with metadata"""
    companies: list[CompanyInDB]
    total: int
    page: int = 1
    per_page: int = 100

# Error response schemas
class CompanyValidationError(BaseModel):
    """Detailed validation error response"""
    field: str
    message: str
    value: Optional[str] = None

class CompanyErrorResponse(BaseModel):
    """Enhanced error response with detailed information"""
    error: str
    message: str
    details: Optional[list[CompanyValidationError]] = None
    error_code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

# Bulk operations schemas  
class CompanyBulkImportResponse(BaseModel):
    """Response for bulk company import operations"""
    message: str
    total_processed: int
    created: int
    updated: int
    skipped: int
    errors: list[str] = []
    warnings: list[str] = []