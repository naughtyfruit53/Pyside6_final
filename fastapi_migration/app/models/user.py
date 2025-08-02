"""
User models for authentication and user management
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model with organization-based multi-tenancy"""
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


class PlatformUser(Base):
    """Platform User Model - For SaaS platform-level users"""
    __tablename__ = "platform_users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User credentials
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    
    # Temporary master password support
    temp_password_hash = Column(String, nullable=True)  # Temporary password hash
    temp_password_expires = Column(DateTime(timezone=True), nullable=True)  # Expiry for temp password
    force_password_reset = Column(Boolean, default=False)  # Force password reset on next login
    
    # User details
    full_name = Column(String)
    role = Column(String, nullable=False, default="super_admin")  # super_admin, platform_admin
    is_active = Column(Boolean, default=True)
    
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