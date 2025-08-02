"""
Reset schemas for password and data reset operations
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class ResetScope(str, Enum):
    ORGANIZATION = "organization"
    ALL_ORGANIZATIONS = "all_organizations"
    SINGLE_USER = "single_user"


class DataResetType(str, Enum):
    FULL_RESET = "full_reset"  # All data except users
    TRANSACTIONAL_ONLY = "transactional_only"  # Only vouchers, invoices etc
    MASTER_DATA_ONLY = "master_data_only"  # Only products, customers, vendors
    CUSTOM = "custom"  # Custom selection of data types


# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    target_email: EmailStr
    notify_user: bool = True


class BulkPasswordResetRequest(BaseModel):
    scope: ResetScope
    organization_id: Optional[int] = None  # Required if scope is ORGANIZATION
    notify_users: bool = True


class PasswordResetResponse(BaseModel):
    message: str
    target_email: str
    new_password: str
    email_sent: bool
    email_error: Optional[str] = None


class BulkPasswordResetResponse(BaseModel):
    message: str
    scope: ResetScope
    total_users_affected: int
    organizations_affected: List[int]
    successful_resets: int
    failed_resets: List[Dict[str, Any]] = []
    email_notification_status: Dict[str, Any] = {}


# Data Reset Schemas
class DataResetRequest(BaseModel):
    scope: ResetScope
    organization_id: Optional[int] = None  # Required if scope is ORGANIZATION
    reset_type: DataResetType = DataResetType.FULL_RESET
    confirm_reset: bool = False  # Safety confirmation
    
    # Custom data types to reset (used when reset_type is CUSTOM)
    include_vouchers: bool = True
    include_products: bool = True
    include_customers: bool = True
    include_vendors: bool = True
    include_stock: bool = True
    include_companies: bool = False  # Usually keep company data
    include_users: bool = False  # Usually don't reset users
    
    @validator('organization_id')
    def validate_organization_id(cls, v, values):
        if values.get('scope') == ResetScope.ORGANIZATION and v is None:
            raise ValueError('organization_id is required when scope is ORGANIZATION')
        return v
    
    @validator('confirm_reset')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('confirm_reset must be True to proceed with data reset')
        return v


class DataResetResponse(BaseModel):
    message: str
    scope: ResetScope
    reset_type: DataResetType
    organizations_affected: List[int]
    data_types_reset: List[str]
    total_records_deleted: int
    deletion_summary: Dict[str, int]  # Count of deleted records by type
    success: bool
    errors: List[str] = []


class OrganizationDataResetResponse(BaseModel):
    message: str
    organization_id: int
    organization_name: str
    reset_type: DataResetType
    data_types_reset: List[str]
    total_records_deleted: int
    deletion_summary: Dict[str, int]
    success: bool
    errors: List[str] = []


# Audit and Status Schemas
class ResetAuditLog(BaseModel):
    id: int
    event_type: str
    action: str
    user_email: str
    organization_id: Optional[int]
    success: bool
    details: Optional[Dict[str, Any]]
    timestamp: str
    
    class Config:
        from_attributes = True


class ResetStatusRequest(BaseModel):
    operation_id: str


class ResetStatusResponse(BaseModel):
    operation_id: str
    status: str  # pending, in_progress, completed, failed
    progress_percentage: Optional[int] = None
    message: str
    started_at: str
    completed_at: Optional[str] = None
    errors: List[str] = []


# Master Password Schemas
class MasterPasswordLoginRequest(BaseModel):
    email: EmailStr
    master_password: str


class MasterPasswordLoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    force_password_reset: bool = True
    organization_id: Optional[int] = None
    user_role: str


class TemporaryPasswordRequest(BaseModel):
    target_email: EmailStr
    expires_hours: int = 24
    
    @validator('expires_hours')
    def validate_expires_hours(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('expires_hours must be between 1 and 168 (1 week)')
        return v


class TemporaryPasswordResponse(BaseModel):
    message: str
    target_email: str
    temporary_password: str
    expires_at: str
    force_password_reset: bool = True


# Emergency Access Schemas
class EmergencyAccessRequest(BaseModel):
    reason: str
    organization_id: Optional[int] = None
    
    @validator('reason')
    def validate_reason(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Emergency access reason must be at least 10 characters')
        return v.strip()


class EmergencyAccessResponse(BaseModel):
    message: str
    emergency_token: str
    valid_for_minutes: int = 30
    restrictions: List[str]
    audit_logged: bool = True