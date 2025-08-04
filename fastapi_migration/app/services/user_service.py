"""
User service for user management operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from app.models.base import User, PlatformUser
from app.models.base import Organization
from app.schemas.user import (
    UserCreate, UserUpdate, UserInDB, 
    PlatformUserCreate, PlatformUserUpdate, PlatformUserInDB,
    AdminPasswordResetResponse, BulkPasswordResetResponse
)
from app.core.security import get_password_hash, verify_password, is_super_admin_email
from app.core.audit import AuditLogger
from app.services.email_service import email_service
import secrets
import string
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    @staticmethod
    def get_user_by_email(
        db: Session, 
        email: str, 
        organization_id: Optional[int] = None
    ) -> Optional[User]:
        """Get user by email, with optional organization filtering"""
        query = db.query(User).filter(User.email == email)
        
        if organization_id is not None:
            query = query.filter(User.organization_id == organization_id)
        else:
            # If no organization specified, prefer super admin users
            query = query.order_by(User.is_super_admin.desc())
        
        return query.first()
    
    @staticmethod
    def get_user_by_username(
        db: Session, 
        username: str, 
        organization_id: Optional[int] = None
    ) -> Optional[User]:
        """Get user by username, with optional organization filtering"""
        query = db.query(User).filter(User.username == username)
        
        if organization_id is not None:
            query = query.filter(User.organization_id == organization_id)
        
        return query.first()
    
    @staticmethod
    def get_platform_user_by_email(db: Session, email: str) -> Optional[PlatformUser]:
        """Get platform user by email"""
        return db.query(PlatformUser).filter(PlatformUser.email == email).first()
    
    @staticmethod
    def authenticate_user(
        db: Session, 
        email: str, 
        password: str, 
        organization_id: Optional[int] = None,
        allow_master_password: bool = True
    ) -> Optional[User]:
        """Authenticate user with email/password"""
        # Try to find user
        user = UserService.get_user_by_email(db, email, organization_id)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Check account lock
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return None
        
        # Check master password for super admin (temporary)
        if (allow_master_password and 
            user.is_super_admin and 
            is_super_admin_email(user.email) and
            password == "Qweasdzxc"):  # Temporary master password
            user.force_password_reset = True
            return user
        
        # Check temporary password
        if (user.temp_password_hash and 
            user.temp_password_expires and
            user.temp_password_expires > datetime.now(timezone.utc) and
            verify_password(password, user.temp_password_hash)):
            user.force_password_reset = True
            return user
        
        # Check regular password
        if verify_password(password, user.hashed_password):
            return user
        
        return None
    
    @staticmethod
    def authenticate_platform_user(
        db: Session, 
        email: str, 
        password: str,
        allow_master_password: bool = True
    ) -> Optional[PlatformUser]:
        """Authenticate platform user with email/password"""
        user = UserService.get_platform_user_by_email(db, email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Check account lock
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return None
        
        # Check master password (temporary)
        if (allow_master_password and 
            user.role == "super_admin" and 
            is_super_admin_email(user.email) and
            password == "Qweasdzxc"):  # Temporary master password
            user.force_password_reset = True
            return user
        
        # Check temporary password
        if (user.temp_password_hash and 
            user.temp_password_expires and
            user.temp_password_expires > datetime.now(timezone.utc) and
            verify_password(password, user.temp_password_hash)):
            user.force_password_reset = True
            return user
        
        # Check regular password
        if verify_password(password, user.hashed_password):
            return user
        
        return None
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_create.password)
        
        db_user = User(
            organization_id=user_create.organization_id,
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
            department=user_create.department,
            designation=user_create.designation,
            employee_id=user_create.employee_id,
            phone=user_create.phone,
            is_active=user_create.is_active,
            must_change_password=True  # Force password change on first login
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Generate a secure random password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure at least one character from each category
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        
        return password
    
    @staticmethod
    def reset_user_password(
        db: Session, 
        admin_user: User,
        target_email: str,
        request=None
    ) -> AdminPasswordResetResponse:
        """Reset password for a specific user (admin operation)"""
        # Find target user
        target_user = UserService.get_user_by_email(db, target_email)
        if not target_user:
            raise ValueError(f"User with email {target_email} not found")
        
        # Generate new password
        new_password = UserService.generate_secure_password()
        hashed_password = get_password_hash(new_password)
        
        # Update user password
        target_user.hashed_password = hashed_password
        target_user.must_change_password = True
        target_user.force_password_reset = True
        target_user.failed_login_attempts = 0
        target_user.locked_until = None
        
        db.commit()
        
        # Try to send email notification
        email_sent = False
        email_error = None
        try:
            success, error = email_service.send_password_reset_email(
                target_email, 
                target_user.full_name or target_user.username,
                new_password, 
                admin_user.full_name or admin_user.email,
                organization_name=None  # Add if needed
            )
            email_sent = success
            email_error = error
        except Exception as e:
            email_error = str(e)
            logger.warning(f"Failed to send password reset email: {e}")
        
        # Log the password reset
        AuditLogger.log_password_reset(
            db=db,
            admin_email=admin_user.email,
            target_email=target_email,
            admin_user_id=admin_user.id,
            target_user_id=target_user.id,
            organization_id=target_user.organization_id,
            success=True,
            ip_address=None if not request else AuditLogger.get_client_ip(request),
            user_agent=None if not request else AuditLogger.get_user_agent(request),
            reset_type="SINGLE_USER"
        )
        
        return AdminPasswordResetResponse(
            message="Password reset successfully",
            target_email=target_email,
            new_password=new_password,
            email_sent=email_sent,
            email_error=email_error
        )
    
    @staticmethod
    def reset_organization_passwords(
        db: Session,
        admin_user: User,
        organization_id: int,
        request=None
    ) -> BulkPasswordResetResponse:
        """Reset passwords for all users in an organization"""
        # Get all active users in the organization
        users = db.query(User).filter(
            and_(
                User.organization_id == organization_id,
                User.is_active == True
            )
        ).all()
        
        if not users:
            raise ValueError(f"No active users found in organization {organization_id}")
        
        reset_results = []
        failed_resets = []
        
        for user in users:
            try:
                new_password = UserService.generate_secure_password()
                hashed_password = get_password_hash(new_password)
                
                user.hashed_password = hashed_password
                user.must_change_password = True
                user.force_password_reset = True
                user.failed_login_attempts = 0
                user.locked_until = None
                
                # Try to send email
                email_sent = False
                email_error = None
                try:
                    success, error = email_service.send_password_reset_email(
                        user.email, 
                        user.full_name or user.username,
                        new_password, 
                        admin_user.full_name or admin_user.email,
                        organization_name=None  # Add if needed
                    )
                    email_sent = success
                    email_error = error
                except Exception as e:
                    email_error = str(e)
                    logger.warning(f"Failed to send password reset email to {user.email}: {e}")
                
                reset_results.append({
                    "email": user.email,
                    "new_password": new_password,
                    "email_sent": email_sent,
                    "email_error": email_error
                })
                
            except Exception as e:
                failed_resets.append({
                    "email": user.email,
                    "error": str(e)
                })
        
        db.commit()
        
        # Log the bulk password reset
        AuditLogger.log_password_reset(
            db=db,
            admin_email=admin_user.email,
            target_email=f"organization_{organization_id}",
            admin_user_id=admin_user.id,
            organization_id=organization_id,
            success=len(failed_resets) == 0,
            ip_address=None if not request else AuditLogger.get_client_ip(request),
            user_agent=None if not request else AuditLogger.get_user_agent(request),
            reset_type="ORGANIZATION_BULK"
        )
        
        return BulkPasswordResetResponse(
            message=f"Password reset completed for organization {organization_id}",
            total_users_reset=len(reset_results),
            organizations_affected=[organization_id],
            failed_resets=failed_resets
        )
    
    @staticmethod
    def reset_all_passwords(
        db: Session,
        admin_user: User,
        request=None
    ) -> BulkPasswordResetResponse:
        """Reset passwords for all users across all organizations (super admin only)"""
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            raise ValueError("No active users found")
        
        reset_results = []
        failed_resets = []
        affected_orgs = set()
        
        for user in users:
            try:
                new_password = UserService.generate_secure_password()
                hashed_password = get_password_hash(new_password)
                
                user.hashed_password = hashed_password
                user.must_change_password = True
                user.force_password_reset = True
                user.failed_login_attempts = 0
                user.locked_until = None
                
                if user.organization_id:
                    affected_orgs.add(user.organization_id)
                
                # Try to send email
                email_sent = False
                email_error = None
                try:
                    success, error = email_service.send_password_reset_email(
                        user.email, 
                        user.full_name or user.username,
                        new_password, 
                        admin_user.full_name or admin_user.email,
                        organization_name=None  # Add if needed
                    )
                    email_sent = success
                    email_error = error
                except Exception as e:
                    email_error = str(e)
                    logger.warning(f"Failed to send password reset email to {user.email}: {e}")
                
                reset_results.append({
                    "email": user.email,
                    "organization_id": user.organization_id,
                    "new_password": new_password,
                    "email_sent": email_sent,
                    "email_error": email_error
                })
                
            except Exception as e:
                failed_resets.append({
                    "email": user.email,
                    "organization_id": user.organization_id,
                    "error": str(e)
                })
        
        db.commit()
        
        # Log the global password reset
        AuditLogger.log_password_reset(
            db=db,
            admin_email=admin_user.email,
            target_email="ALL_USERS",
            admin_user_id=admin_user.id,
            success=len(failed_resets) == 0,
            ip_address=None if not request else AuditLogger.get_client_ip(request),
            user_agent=None if not request else AuditLogger.get_user_agent(request),
            reset_type="GLOBAL_BULK"
        )
        
        return BulkPasswordResetResponse(
            message="Global password reset completed",
            total_users_reset=len(reset_results),
            organizations_affected=list(affected_orgs),
            failed_resets=failed_resets
        )
    
    @staticmethod
    def set_temporary_password(
        db: Session,
        user: User,
        temp_password: str,
        expires_hours: int = 24
    ) -> None:
        """Set temporary password for user"""
        user.temp_password_hash = get_password_hash(temp_password)
        user.temp_password_expires = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        user.force_password_reset = True
        db.commit()
    
    @staticmethod
    def clear_temporary_password(db: Session, user: User) -> None:
        """Clear temporary password for user"""
        user.temp_password_hash = None
        user.temp_password_expires = None
        db.commit()
    
    @staticmethod
    def update_login_attempt(
        db: Session, 
        user: User, 
        success: bool
    ) -> None:
        """Update login attempt statistics"""
        if success:
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now(timezone.utc)
        else:
            # Increment failed attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        db.commit()
    
    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Check if user account is locked"""
        return user.locked_until is not None and user.locked_until > datetime.now(timezone.utc)
    
    @staticmethod
    def increment_failed_login_attempts(db: Session, user: User) -> None:
        """Increment failed login attempts and lock if necessary"""
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
    
    @staticmethod
    def reset_failed_login_attempts(db: Session, user: User) -> None:
        """Reset failed login attempts"""
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()