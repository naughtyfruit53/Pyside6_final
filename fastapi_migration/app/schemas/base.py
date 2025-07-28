from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    STANDARD_USER = "standard_user"

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"

class PlanType(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# Organization schemas
class OrganizationBase(BaseModel):
    name: str
    subdomain: str
    business_type: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    primary_email: EmailStr
    primary_phone: str
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    country: str = "India"
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    cin_number: Optional[str] = None
    
class OrganizationCreate(OrganizationBase):
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str
    
    @validator('admin_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('subdomain')
    def validate_subdomain(cls, v):
        if not v.isalnum() or len(v) < 3:
            raise ValueError('Subdomain must be alphanumeric and at least 3 characters')
        return v.lower()

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    primary_phone: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    cin_number: Optional[str] = None
    status: Optional[OrganizationStatus] = None
    plan_type: Optional[PlanType] = None
    max_users: Optional[int] = None
    storage_limit_gb: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    financial_year_start: Optional[str] = None

class OrganizationInDB(OrganizationBase):
    id: int
    status: OrganizationStatus = OrganizationStatus.TRIAL
    plan_type: PlanType = PlanType.TRIAL
    max_users: int = 5
    storage_limit_gb: int = 1
    features: Optional[Dict[str, Any]] = None
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    date_format: str = "DD/MM/YYYY"
    financial_year_start: str = "04/01"
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.STANDARD_USER
    department: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    organization_id: Optional[int] = None  # Optional for creation by super admin
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    must_change_password: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    organization_id: int
    is_super_admin: bool = False
    must_change_password: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    subdomain: Optional[str] = None  # For tenant-specific login

class Token(BaseModel):
    access_token: str
    token_type: str
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    user_role: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    organization_id: Optional[int] = None

# OTP Authentication schemas
class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "login"  # login, password_reset, registration

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
    purpose: str = "login"

class OTPResponse(BaseModel):
    message: str
    email: str
    expires_in_minutes: int = 10

# Company schemas
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
    pass

class CompanyUpdate(BaseModel):
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

class CompanyInDB(CompanyBase):
    id: int
    organization_id: int
    logo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Vendor schemas
class VendorBase(BaseModel):
    name: str
    contact_number: str
    email: Optional[EmailStr] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    state_code: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    state_code: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: Optional[bool] = None

class VendorInDB(VendorBase):
    id: int
    organization_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Customer schemas (same structure as Vendor)
class CustomerBase(BaseModel):
    name: str
    contact_number: str
    email: Optional[EmailStr] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    state_code: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    state_code: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerInDB(CustomerBase):
    id: int
    organization_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    hsn_code: Optional[str] = None
    part_number: Optional[str] = None
    unit: str
    unit_price: float
    gst_rate: float = 0.0
    is_gst_inclusive: bool = False
    reorder_level: int = 0
    description: Optional[str] = None
    is_manufactured: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    hsn_code: Optional[str] = None
    part_number: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    gst_rate: Optional[float] = None
    is_gst_inclusive: Optional[bool] = None
    reorder_level: Optional[int] = None
    description: Optional[str] = None
    is_manufactured: Optional[bool] = None
    is_active: Optional[bool] = None

class ProductInDB(ProductBase):
    id: int
    organization_id: int
    drawings_path: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Stock schemas
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
        orm_mode = True

# Email notification schemas
class EmailNotificationBase(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    voucher_type: Optional[str] = None
    voucher_id: Optional[int] = None

class EmailNotificationCreate(EmailNotificationBase):
    pass

class EmailNotificationInDB(EmailNotificationBase):
    id: int
    organization_id: int
    status: str = "pending"
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

# Payment term schemas
class PaymentTermBase(BaseModel):
    name: str
    days: int
    description: Optional[str] = None

class PaymentTermCreate(PaymentTermBase):
    pass

class PaymentTermUpdate(BaseModel):
    name: Optional[str] = None
    days: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PaymentTermInDB(PaymentTermBase):
    id: int
    organization_id: int
    is_active: bool = True
    
    class Config:
        orm_mode = True

# Bulk import/export response schemas
class BulkImportResponse(BaseModel):
    message: str
    total_processed: int
    created: int
    updated: int
    errors: List[str] = []
    
class BulkImportError(BaseModel):
    row: int
    field: str
    value: str
    error: str
    
class DetailedBulkImportResponse(BaseModel):
    message: str
    total_processed: int
    created: int
    updated: int
    skipped: int
    errors: List[BulkImportError] = []