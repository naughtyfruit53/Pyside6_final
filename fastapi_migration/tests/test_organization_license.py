"""
Tests for organization license creation functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User
from app.core.security import get_password_hash
from app.schemas.base import UserRole

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_license.db"

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
def super_admin_user(test_db):
    """Create a super admin user for testing"""
    user = User(
        email="superadmin@test.com",
        username="superadmin",
        hashed_password=get_password_hash("password123"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_super_admin=True,
        is_active=True,
        organization_id=None
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, super_admin_user):
    """Get authentication headers for super admin"""
    response = client.post(
        "/api/v1/auth/login/email",
        json={"email": "superadmin@test.com", "password": "password123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_organization_license_success(client, auth_headers):
    """Test successful organization license creation"""
    license_data = {
        "organization_name": "Test Company Ltd",
        "superadmin_email": "admin@testcompany.com"
    }
    
    response = client.post(
        "/api/v1/organizations/license/create",
        json=license_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["organization_name"] == "Test Company Ltd"
    assert data["superadmin_email"] == "admin@testcompany.com"
    assert "subdomain" in data
    assert "temp_password" in data
    assert len(data["temp_password"]) == 12

def test_create_organization_license_duplicate_name(client, auth_headers, test_db):
    """Test organization license creation with duplicate name"""
    # Create existing organization
    existing_org = Organization(
        name="Test Company Ltd",
        subdomain="testcompany",
        primary_email="existing@test.com",
        primary_phone="+91-1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456"
    )
    test_db.add(existing_org)
    test_db.commit()
    
    license_data = {
        "organization_name": "Test Company Ltd",
        "superadmin_email": "admin@testcompany.com"
    }
    
    response = client.post(
        "/api/v1/organizations/license/create",
        json=license_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Organization name already exists" in response.json()["detail"]

def test_create_organization_license_duplicate_email(client, auth_headers, test_db):
    """Test organization license creation with duplicate email"""
    # Create existing user
    existing_user = User(
        email="admin@testcompany.com",
        username="existing",
        hashed_password=get_password_hash("password"),
        full_name="Existing User",
        role=UserRole.STANDARD_USER,
        is_active=True,
        organization_id=1
    )
    test_db.add(existing_user)
    test_db.commit()
    
    license_data = {
        "organization_name": "Test Company Ltd",
        "superadmin_email": "admin@testcompany.com"
    }
    
    response = client.post(
        "/api/v1/organizations/license/create",
        json=license_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Email already exists" in response.json()["detail"]

def test_create_organization_license_unauthorized(client):
    """Test organization license creation without proper authorization"""
    license_data = {
        "organization_name": "Test Company Ltd",
        "superadmin_email": "admin@testcompany.com"
    }
    
    response = client.post(
        "/api/v1/organizations/license/create",
        json=license_data
    )
    
    assert response.status_code == 401

def test_create_organization_license_invalid_data(client, auth_headers):
    """Test organization license creation with invalid data"""
    license_data = {
        "organization_name": "Te",  # Too short
        "superadmin_email": "invalid-email"  # Invalid email
    }
    
    response = client.post(
        "/api/v1/organizations/license/create",
        json=license_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error

def test_organization_subdomain_generation(client, auth_headers):
    """Test that unique subdomains are generated"""
    # Create first organization
    license_data1 = {
        "organization_name": "Test Company Ltd",
        "superadmin_email": "admin1@testcompany.com"
    }
    
    response1 = client.post(
        "/api/v1/organizations/license/create",
        json=license_data1,
        headers=auth_headers
    )
    
    assert response1.status_code == 201
    subdomain1 = response1.json()["subdomain"]
    
    # Create second organization with similar name
    license_data2 = {
        "organization_name": "Test Company Corporation",
        "superadmin_email": "admin2@testcompany.com"
    }
    
    response2 = client.post(
        "/api/v1/organizations/license/create",
        json=license_data2,
        headers=auth_headers
    )
    
    assert response2.status_code == 201
    subdomain2 = response2.json()["subdomain"]
    
    # Subdomains should be different
    assert subdomain1 != subdomain2