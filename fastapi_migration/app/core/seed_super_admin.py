"""
Super Admin Seeding Logic

This module contains logic to seed the default platform super admin user.
The super admin is not tied to any organization and can create organizations
and organization-level super admins.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.base import User

logger = logging.getLogger(__name__)

def seed_super_admin(db: Session = None) -> None:
    """
    Creates a default platform super admin if none exists.
    
    The super admin user has:
    - Email: naughtyfruit53@gmail.com
    - Password: 123456 (hashed with bcrypt)
    - organization_id: NULL (not tied to any organization)
    - role: super_admin
    - is_super_admin: True
    
    This seeding logic only runs if no super admin exists in the database.
    It handles both new installations and existing databases after migration.
    """
    db_session = db
    if db_session is None:
        db_session = SessionLocal()
    
    try:
        # First check if the users table has the necessary columns
        # This handles the case where migrations haven't been run yet
        try:
            # Try to query with the new columns
            existing_super_admin = db_session.query(User).filter(
                User.is_super_admin == True,
                User.organization_id.is_(None)
            ).first()
            
            if existing_super_admin:
                logger.info("Platform super admin already exists. Skipping seeding.")
                return
                
        except OperationalError as e:
            if "no such column" in str(e):
                logger.warning("Database schema appears to be outdated. The users table is missing organization_id or is_super_admin columns.")
                logger.warning("Please run 'alembic upgrade head' to update the database schema before seeding super admin.")
                logger.warning("Skipping super admin seeding for now.")
                return
            else:
                raise
        
        # Create the default super admin user
        super_admin_email = "naughtyfruit53@gmail.com"
        super_admin_password = "123456"  # This should be changed after first login
        
        # Hash the password
        hashed_password = get_password_hash(super_admin_password)
        
        # Create the super admin user
        super_admin = User(
            email=super_admin_email,
            username="super_admin",
            hashed_password=hashed_password,
            full_name="Platform Super Administrator",
            role="super_admin",
            organization_id=None,  # Not tied to any organization
            is_super_admin=True,
            is_active=True,
            must_change_password=True  # Force password change on first login
        )
        
        db_session.add(super_admin)
        db_session.commit()
        db_session.refresh(super_admin)
        
        logger.info(f"Successfully created platform super admin with email: {super_admin_email}")
        logger.warning("SECURITY: Default super admin created with password '123456'. Please change this password immediately after first login!")
        
    except Exception as e:
        logger.error(f"Failed to seed super admin: {e}")
        db_session.rollback()
        raise
    finally:
        if db is None:  # Only close if we created the session
            db_session.close()

def check_super_admin_exists(db: Session = None) -> bool:
    """
    Check if a platform super admin exists.
    
    Returns:
        bool: True if a super admin exists, False otherwise
    """
    db_session = db
    if db_session is None:
        db_session = SessionLocal()
    
    try:
        # Check if the necessary columns exist first
        try:
            super_admin = db_session.query(User).filter(
                User.is_super_admin == True,
                User.organization_id.is_(None)
            ).first()
            
            return super_admin is not None
            
        except OperationalError as e:
            if "no such column" in str(e):
                logger.warning("Database schema is outdated. Cannot check for super admin existence.")
                return False
            else:
                raise
    
    except Exception as e:
        logger.error(f"Failed to check super admin existence: {e}")
        return False
    finally:
        if db is None:  # Only close if we created the session
            db_session.close()

def check_database_schema_updated(db: Session = None) -> bool:
    """
    Check if the database schema has been updated with organization support.
    
    Returns:
        bool: True if schema is updated, False otherwise
    """
    db_session = db
    if db_session is None:
        db_session = SessionLocal()
    
    try:
        # Try to query the new columns
        db_session.execute(text("SELECT organization_id, is_super_admin FROM users LIMIT 1"))
        return True
    except OperationalError:
        return False
    except Exception:
        return False
    finally:
        if db is None:
            db_session.close()