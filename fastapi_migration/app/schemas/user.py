"""
User schemas for authentication and user management
"""
from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from app.core.security import check_password_strength


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    STANDARD_USER = "standard_user"


class PlatformUserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    PLATFORM_ADMIN = "platform_admin"


# User schemas
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
    
    @field_validator('password')
    def validate_password(cls, v):
        is_strong, msg = check_password_strength(v)
        if not is_strong:
            raise ValueError(msg)
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
    organization_id: Optional[int] = None  # Optional to allow None for platform users
    is_super_admin: bool = False
    must_change_password: bool = False
    force_password_reset: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes = True)


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
    must_change_password: bool = False
    force_password_reset: bool = False
    is_first_login: bool = False
    company_details_completed: bool = True


class TokenData(BaseModel):
    email: Optional[str] = None
    organization_id: Optional[int] = None


# Platform User schemas - for SaaS platform-level users
class PlatformUserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: PlatformUserRole = PlatformUserRole.PLATFORM_ADMIN
    is_active: bool = True


class PlatformUserCreate(PlatformUserBase):
    password: str
    
    @field_validator('password')
    def validate_password(cls, v):
        is_strong, msg = check_password_strength(v)
        if not is_strong:
            raise ValueError(msg)
        return v


class PlatformUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[PlatformUserRole] = None
    is_active: Optional[bool] = None


class PlatformUserInDB(PlatformUserBase):
    id: int
    force_password_reset: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes = True)


# Password management schemas
class PasswordChangeRequest(BaseModel):
    current_password: Optional[str] = Field(None, description="Current password for verification")
    new_password: str = Field(..., description="New password to set")
    confirm_password: Optional[str] = Field(None, description="Confirm new password")
    
    @field_validator('new_password')
    def validate_password(cls, v):
        is_strong, msg = check_password_strength(v)
        if not is_strong:
            raise ValueError(msg)
        return v
    
    @field_validator('confirm_password')
    def validate_password_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    model_config = ConfigDict(populate_by_name = True)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    
    @field_validator('new_password')
    def validate_password(cls, v):
        is_strong, msg = check_password_strength(v)
        if not is_strong:
            raise ValueError(msg)
        return v


class PasswordChangeResponse(BaseModel):
    message: str
    
    model_config = ConfigDict(from_attributes = True)


# Admin password reset schemas
class AdminPasswordResetRequest(BaseModel):
    target_email: EmailStr


class AdminPasswordResetResponse(BaseModel):
    message: str
    target_email: str
    new_password: str  # Displayed to admin
    email_sent: bool
    email_error: Optional[str] = None
    must_change_password: bool = True


class BulkPasswordResetRequest(BaseModel):
    organization_id: Optional[int] = None  # None for all organizations


class BulkPasswordResetResponse(BaseModel):
    message: str
    total_users_reset: int
    organizations_affected: list
    failed_resets: list = []


# Temporary password schemas
class TemporaryPasswordRequest(BaseModel):
    target_email: EmailStr
    expires_hours: int = 24
    
    @field_validator('expires_hours')
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
    

# OTP schemas
class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "login"  # login, password_reset


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
    purpose: str = "login"


class OTPResponse(BaseModel):
    message: str
    email: str


# Master password schemas
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