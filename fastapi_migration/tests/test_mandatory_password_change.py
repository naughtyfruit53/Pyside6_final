"""
Test for mandatory password change functionality - additional tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db, Base
from app.models.base import Organization, User
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserRole

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mandatory_password.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_organization(test_db):
    """Create a test organization"""
    org = Organization(
        name="Test Organization",
        subdomain="testorg",
        primary_email="test@testorg.com",
        primary_phone="+91-1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_user_mandatory(test_db, test_organization):
    """Create a test user with mandatory password change"""
    user = User(
        organization_id=test_organization.id,
        email="mandatoryuser@example.com",
        username="mandatoryuser",
        hashed_password=get_password_hash("temppassword123"),
        full_name="Mandatory User",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        must_change_password=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_user_normal(test_db, test_organization):
    """Create a normal test user"""
    user = User(
        organization_id=test_organization.id,
        email="normaluser@example.com",
        username="normaluser",
        hashed_password=get_password_hash("oldpassword123"),
        full_name="Normal User",
        role=UserRole.STANDARD_USER,
        is_active=True,
        must_change_password=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

def test_user_must_change_password_field(test_user_mandatory, test_user_normal):
    """Test that users are created with correct must_change_password values"""
    assert test_user_mandatory.must_change_password == True
    assert test_user_normal.must_change_password == False

def test_password_hashing(test_user_mandatory):
    """Test that passwords are properly hashed"""
    assert verify_password("temppassword123", test_user_mandatory.hashed_password)
    assert not verify_password("wrongpassword", test_user_mandatory.hashed_password)

def test_user_roles():
    """Test that user roles are properly defined"""
    assert UserRole.SUPER_ADMIN == "super_admin"
    assert UserRole.STANDARD_USER == "standard_user"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])