"""
Tests for mandatory password change functionality with confirm_password
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserRole

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mandatory_password_api.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

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
def mandatory_user(test_db, test_organization):
    """Create a user with mandatory password change"""
    user = User(
        organization_id=test_organization.id,
        email="superadmin@example.com",
        username="superadmin",
        hashed_password=get_password_hash("temppassword123"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        must_change_password=True  # This is the key flag for mandatory change
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def normal_user(test_db, test_organization):
    """Create a normal user without mandatory password change"""
    user = User(
        organization_id=test_organization.id,
        email="normaluser@example.com",
        username="normaluser",
        hashed_password=get_password_hash("normalpassword123"),
        full_name="Normal User",
        role=UserRole.STANDARD_USER,
        is_active=True,
        must_change_password=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def mandatory_auth_headers(client, mandatory_user):
    """Get authentication headers for mandatory password change user"""
    response = client.post(
        "/api/auth/login/email",
        json={"email": "superadmin@example.com", "password": "temppassword123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def normal_auth_headers(client, normal_user):
    """Get authentication headers for normal user"""
    response = client.post(
        "/api/auth/login/email",
        json={"email": "normaluser@example.com", "password": "normalpassword123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_mandatory_password_change_success_with_confirm(client, mandatory_auth_headers, test_db, mandatory_user):
    """Test successful mandatory password change with confirm_password"""
    password_data = {
        "new_password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
        # Note: NO current_password for mandatory changes
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=mandatory_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]
    
    # Verify password was actually changed
    test_db.refresh(mandatory_user)
    assert verify_password("NewSecurePassword123!", mandatory_user.hashed_password)
    assert not verify_password("temppassword123", mandatory_user.hashed_password)
    
    # Verify must_change_password flag was cleared
    assert mandatory_user.must_change_password == False

def test_mandatory_password_change_mismatch_passwords(client, mandatory_auth_headers):
    """Test mandatory password change with mismatched passwords"""
    password_data = {
        "new_password": "NewSecurePassword123!",
        "confirm_password": "DifferentPassword123!"
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=mandatory_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 422  # Pydantic validation error is better than 400
    assert "do not match" in str(response.json())

def test_mandatory_password_change_without_confirm(client, mandatory_auth_headers, test_db, mandatory_user):
    """Test mandatory password change without confirm_password (should still work)"""
    password_data = {
        "new_password": "NewSecurePassword123!"
        # No confirm_password field
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=mandatory_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]
    
    # Verify password was actually changed
    test_db.refresh(mandatory_user)
    assert verify_password("NewSecurePassword123!", mandatory_user.hashed_password)

def test_normal_password_change_with_confirm(client, normal_auth_headers, test_db, normal_user):
    """Test normal password change with all fields including confirm_password"""
    password_data = {
        "current_password": "normalpassword123",
        "new_password": "NewNormalPassword123!",
        "confirm_password": "NewNormalPassword123!"
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=normal_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]
    
    # Verify password was actually changed
    test_db.refresh(normal_user)
    assert verify_password("NewNormalPassword123!", normal_user.hashed_password)
    assert not verify_password("normalpassword123", normal_user.hashed_password)

def test_normal_password_change_mismatch_confirm(client, normal_auth_headers):
    """Test normal password change with mismatched confirm_password"""
    password_data = {
        "current_password": "normalpassword123",
        "new_password": "NewNormalPassword123!",
        "confirm_password": "DifferentPassword123!"
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=normal_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 422  # Pydantic validation error is better than 400
    assert "do not match" in str(response.json())

def test_normal_password_change_missing_current(client, normal_auth_headers):
    """Test normal password change without current_password should fail"""
    password_data = {
        "new_password": "NewNormalPassword123!",
        "confirm_password": "NewNormalPassword123!"
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=normal_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 400
    assert "Current password is required" in response.json()["detail"]

def test_weak_password_validation(client, mandatory_auth_headers):
    """Test that weak passwords are rejected even for mandatory changes"""
    password_data = {
        "new_password": "weak",
        "confirm_password": "weak"
    }
    
    response = client.post(
        "/api/auth/password/change",
        json=password_data,
        headers=mandatory_auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 422  # Validation error from Pydantic

if __name__ == "__main__":
    pytest.main([__file__, "-v"])