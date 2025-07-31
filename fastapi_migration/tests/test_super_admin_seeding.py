"""
Test for Super Admin Seeding Functionality
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.seed_super_admin import seed_super_admin, check_super_admin_exists
from app.models.base import User
import os

# Test database
TEST_DATABASE_URL = "sqlite:///./test_super_admin.db"

@pytest.fixture
def test_db():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    yield db
    
    db.close()
    # Clean up
    if os.path.exists("./test_super_admin.db"):
        os.remove("./test_super_admin.db")

def test_seed_super_admin_creation(test_db):
    """Test that super admin is created when none exists"""
    # Ensure no super admin exists initially
    assert not check_super_admin_exists(test_db)
    
    # Run seeding
    seed_super_admin(test_db)
    
    # Check that super admin was created
    assert check_super_admin_exists(test_db)
    
    # Verify super admin details
    super_admin = test_db.query(User).filter(
        User.is_super_admin == True,
        User.organization_id.is_(None)
    ).first()
    
    assert super_admin is not None
    assert super_admin.email == "naughtyfruit53@gmail.com"
    assert super_admin.username == "super_admin"
    assert super_admin.role == "super_admin"
    assert super_admin.organization_id is None
    assert super_admin.is_super_admin is True
    assert super_admin.is_active is True
    assert super_admin.must_change_password is True

def test_seed_super_admin_no_duplicate(test_db):
    """Test that no duplicate super admin is created"""
    # Create initial super admin
    seed_super_admin(test_db)
    
    # Count super admins
    initial_count = test_db.query(User).filter(
        User.is_super_admin == True,
        User.organization_id.is_(None)
    ).count()
    
    assert initial_count == 1
    
    # Run seeding again
    seed_super_admin(test_db)
    
    # Verify count didn't increase
    final_count = test_db.query(User).filter(
        User.is_super_admin == True,
        User.organization_id.is_(None)
    ).count()
    
    assert final_count == 1

def test_check_super_admin_exists(test_db):
    """Test the check_super_admin_exists function"""
    # Initially no super admin
    assert not check_super_admin_exists(test_db)
    
    # Create super admin
    seed_super_admin(test_db)
    
    # Now should exist
    assert check_super_admin_exists(test_db)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])