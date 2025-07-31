#!/usr/bin/env python3
"""
Script to create platform super admin user for testing
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.base import PlatformUser
from app.core.security import get_password_hash
from app.schemas.base import PlatformUserRole

def create_platform_super_admin():
    """Create platform super admin user"""
    db = SessionLocal()
    try:
        # Check if super admin already exists
        existing_admin = db.query(PlatformUser).filter(
            PlatformUser.email == "naughtyfruit53@gmail.com"
        ).first()
        
        if existing_admin:
            print("Platform super admin already exists")
            print(f"Email: {existing_admin.email}")
            print(f"Role: {existing_admin.role}")
            print(f"Active: {existing_admin.is_active}")
            return existing_admin
        
        # Create new platform super admin
        admin_user = PlatformUser(
            email="naughtyfruit53@gmail.com",
            full_name="Platform Super Admin",
            hashed_password=get_password_hash("123456"),  # Default password
            role=PlatformUserRole.SUPER_ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Platform super admin created successfully!")
        print(f"Email: {admin_user.email}")
        print(f"Password: 123456 (please change after first login)")
        print(f"Role: {admin_user.role}")
        
        return admin_user
        
    except Exception as e:
        print(f"Error creating platform super admin: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_platform_super_admin()