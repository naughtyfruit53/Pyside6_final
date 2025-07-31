#!/usr/bin/env python3
"""
Setup script to initialize a fresh database for TRITIQ ERP with platform super admin support.

This script creates a new database with the correct schema and seeds the default super admin.
Use this for fresh installations or after running database migrations.
"""

import os
import sys
import logging

# Add the app directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Set up environment variables for testing"""
    os.environ.setdefault('SMTP_USERNAME', 'admin@tritiq.com')
    os.environ.setdefault('SMTP_PASSWORD', 'admin123')
    os.environ.setdefault('EMAILS_FROM_EMAIL', 'admin@tritiq.com')

def create_fresh_database():
    """Create a fresh database with correct schema"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base, User
    from app.core.security import get_password_hash
    
    # Remove existing database
    db_file = './tritiq_erp_fresh.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed existing database: {db_file}")
    
    # Create new database with correct schema
    fresh_engine = create_engine(f'sqlite:///{db_file}', echo=False)
    Base.metadata.create_all(bind=fresh_engine)
    print("Created fresh database with updated schema")
    
    # Create session for this engine
    FreshSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=fresh_engine)
    
    # Seed super admin
    db = FreshSessionLocal()
    try:
        # Check if super admin already exists
        existing_super_admin = db.query(User).filter(
            User.is_super_admin == True,
            User.organization_id.is_(None)
        ).first()
        
        if existing_super_admin:
            print("Platform super admin already exists. Skipping seeding.")
            return
        
        # Create the default super admin user
        super_admin_email = "naughtyfruit53@gmail.com"
        super_admin_password = "123456"
        
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
        
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        print("Successfully seeded platform super admin")
        
        # Verify creation
        super_admin = db.query(User).filter(
            User.is_super_admin == True,
            User.organization_id.is_(None)
        ).first()
        
        if super_admin:
            print(f"✓ Super admin created: {super_admin.email}")
            print(f"✓ Role: {super_admin.role}")
            print(f"✓ Organization ID: {super_admin.organization_id}")
            print("✓ Login credentials: naughtyfruit53@gmail.com / 123456")
            print("⚠️  IMPORTANT: Change the default password after first login!")
        else:
            print("✗ Super admin verification failed")
            
    except Exception as e:
        print(f"Error seeding super admin: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("TRITIQ ERP - Fresh Database Setup")
    print("=" * 40)
    
    setup_environment()
    
    try:
        create_fresh_database()
        print("\n✓ Database setup completed successfully!")
        print(f"\nDatabase file: tritiq_erp_fresh.db")
        print("\nTo use this database:")
        print("1. Set DATABASE_URL=sqlite:///./tritiq_erp_fresh.db")
        print("2. Start the application: python -m uvicorn app.main:app --reload")
        print("3. Login with: naughtyfruit53@gmail.com / 123456")
        print("4. Change the default password")
        print("5. Create organizations and users")
        
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)