from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Platform User Model - For SaaS platform-level users
class PlatformUser(Base):
    __tablename__ = "platform_users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User credentials
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # User details
    full_name = Column(String)
    role = Column(String, nullable=False, default="super_admin")  # super_admin, platform_admin
    is_active = Column(Boolean, default=True)
    
    # Temporary master password support
    temp_password_hash = Column(String, nullable=True)  # Temporary password hash
    temp_password_expires = Column(DateTime(timezone=True), nullable=True)  # Expiry for temp password
    force_password_reset = Column(Boolean, default=False)  # Force password reset on next login
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_platform_user_email', 'email'),
        Index('idx_platform_user_active', 'is_active'),
    )

# Organization/Tenant Model - Core of Multi-tenancy
class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    subdomain = Column(String, unique=True, nullable=False, index=True)  # For subdomain-based tenancy
    status = Column(String, nullable=False, default="active")  # active, suspended, trial
    
    # Business details
    business_type = Column(String)  # manufacturing, trading, service, etc.
    industry = Column(String)
    website = Column(String)
    description = Column(Text)
    
    # Contact information
    primary_email = Column(String, nullable=False)
    primary_phone = Column(String, nullable=False)
    
    # Address
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    country = Column(String, nullable=False, default="India")
    
    # Legal details
    gst_number = Column(String)
    pan_number = Column(String)
    cin_number = Column(String)  # Corporate Identification Number
    
    # Subscription details
    plan_type = Column(String, default="trial")  # trial, basic, premium, enterprise
    max_users = Column(Integer, default=5)
    storage_limit_gb = Column(Integer, default=1)
    features = Column(JSON)  # Feature flags
    
    # Settings
    timezone = Column(String, default="Asia/Kolkata")
    currency = Column(String, default="INR")
    date_format = Column(String, default="DD/MM/YYYY")
    financial_year_start = Column(String, default="04/01")  # April 1st
    
    # Onboarding status
    company_details_completed = Column(Boolean, default=False)  # Track if company details have been filled
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    companies = relationship("Company", back_populates="organization")
    vendors = relationship("Vendor", back_populates="organization")
    customers = relationship("Customer", back_populates="organization")
    products = relationship("Product", back_populates="organization")
    stock_entries = relationship("Stock", back_populates="organization")
    
    __table_args__ = (
        Index('idx_org_status_subdomain', 'status', 'subdomain'),
    )

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant fields - REQUIRED for all organization users
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # User credentials
    email = Column(String, nullable=False, index=True)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # User details
    full_name = Column(String)
    role = Column(String, nullable=False, default="standard_user")  # org_admin, admin, standard_user
    department = Column(String)
    designation = Column(String)
    employee_id = Column(String)
    
    # Permissions and status
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    
    # Temporary master password support
    temp_password_hash = Column(String, nullable=True)  # Temporary password hash
    temp_password_expires = Column(DateTime(timezone=True), nullable=True)  # Expiry for temp password
    force_password_reset = Column(Boolean, default=False)  # Force password reset on next login
    
    # Profile
    phone = Column(String)
    avatar_path = Column(String)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    
    __table_args__ = (
        # Unique email per organization
        UniqueConstraint('organization_id', 'email', name='uq_user_org_email'),
        # Unique username per organization
        UniqueConstraint('organization_id', 'username', name='uq_user_org_username'),
        Index('idx_user_org_email', 'organization_id', 'email'),
        Index('idx_user_org_username', 'organization_id', 'username'),
        Index('idx_user_org_active', 'organization_id', 'is_active'),
    )

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Company details
    name = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    gst_number = Column(String)
    pan_number = Column(String)
    contact_number = Column(String, nullable=False)
    email = Column(String)
    logo_path = Column(String)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="companies")
    
    __table_args__ = (
        Index('idx_company_org_name', 'organization_id', 'name'),
    )

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Vendor details
    name = Column(String, nullable=False, index=True)
    contact_number = Column(String, nullable=False)
    email = Column(String)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    gst_number = Column(String)
    pan_number = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="vendors")
    
    __table_args__ = (
        # Unique vendor name per organization
        UniqueConstraint('organization_id', 'name', name='uq_vendor_org_name'),
        Index('idx_vendor_org_name', 'organization_id', 'name'),
        Index('idx_vendor_org_active', 'organization_id', 'is_active'),
    )

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Customer details
    name = Column(String, nullable=False, index=True)
    contact_number = Column(String, nullable=False)
    email = Column(String)
    address1 = Column(String, nullable=False)
    address2 = Column(String)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pin_code = Column(String, nullable=False)
    state_code = Column(String, nullable=False)
    gst_number = Column(String)
    pan_number = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="customers")
    
    __table_args__ = (
        # Unique customer name per organization
        UniqueConstraint('organization_id', 'name', name='uq_customer_org_name'),
        Index('idx_customer_org_name', 'organization_id', 'name'),
        Index('idx_customer_org_active', 'organization_id', 'is_active'),
    )

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Product details
    name = Column(String, nullable=False, index=True)
    hsn_code = Column(String)
    part_number = Column(String)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)
    is_gst_inclusive = Column(Boolean, default=False)
    reorder_level = Column(Integer, default=0)
    description = Column(Text)
    is_manufactured = Column(Boolean, default=False)
    drawings_path = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="products")
    
    __table_args__ = (
        # Unique product name per organization
        UniqueConstraint('organization_id', 'name', name='uq_product_org_name'),
        # Unique part number per organization (if provided)
        UniqueConstraint('organization_id', 'part_number', name='uq_product_org_part_number'),
        Index('idx_product_org_name', 'organization_id', 'name'),
        Index('idx_product_org_active', 'organization_id', 'is_active'),
        Index('idx_product_org_hsn', 'organization_id', 'hsn_code'),
    )

class Stock(Base):
    __tablename__ = "stock"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Stock details
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String, nullable=False)
    location = Column(String)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="stock_entries")
    product = relationship("Product", backref="stock_entries")
    
    __table_args__ = (
        # Unique stock entry per product per organization per location
        UniqueConstraint('organization_id', 'product_id', 'location', name='uq_stock_org_product_location'),
        Index('idx_stock_org_product', 'organization_id', 'product_id'),
        Index('idx_stock_org_location', 'organization_id', 'location'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Audit details
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    user_id = Column(Integer, ForeignKey("users.id"))
    changes = Column(JSON)  # Store the changes made
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_audit_org_table_action', 'organization_id', 'table_name', 'action'),
        Index('idx_audit_org_timestamp', 'organization_id', 'timestamp'),
    )

class EmailNotification(Base):
    __tablename__ = "email_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Email details
    to_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    voucher_type = Column(String)
    voucher_id = Column(Integer)
    status = Column(String, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_email_org_status', 'organization_id', 'status'),
    )
    
# Payment Terms
class PaymentTerm(Base):
    __tablename__ = "payment_terms"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant field
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Payment term details
    name = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_payment_term_org_name', 'organization_id', 'name'),
    )

class OTPVerification(Base):
    __tablename__ = "otp_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    otp_hash = Column(String, nullable=False)  # Store hashed OTP for security
    purpose = Column(String, nullable=False, default="login")  # login, password_reset, registration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True))
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_otp_email_purpose', 'email', 'purpose'),
        Index('idx_otp_expires', 'expires_at'),
    )