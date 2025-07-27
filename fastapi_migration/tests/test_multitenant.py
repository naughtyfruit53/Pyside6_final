"""
Basic tests for multi-tenant functionality
"""
import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User, Company, Vendor, Customer, Product
from app.core.security import get_password_hash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

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
        subdomain="test",
        status="active",
        primary_email="test@example.com",
        primary_phone="+1234567890",
        address1="123 Test Street",
        city="Test City",
        state="Test State",
        pin_code="12345",
        country="India"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_user(test_db, test_organization):
    """Create a test user"""
    user = User(
        organization_id=test_organization.id,
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role="standard_user",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_admin_user(test_db, test_organization):
    """Create a test admin user"""
    admin = User(
        organization_id=test_organization.id,
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        role="org_admin",
        is_active=True
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin

@pytest.fixture
def super_admin_user(test_db, test_organization):
    """Create a super admin user"""
    super_admin = User(
        organization_id=test_organization.id,
        email="superadmin@example.com",
        username="superadmin",
        hashed_password=get_password_hash("superpass123"),
        full_name="Super Admin",
        role="org_admin",
        is_super_admin=True,
        is_active=True
    )
    test_db.add(super_admin)
    test_db.commit()
    test_db.refresh(super_admin)
    return super_admin

def get_user_token(client, email: str, password: str):
    """Get authentication token for user"""
    response = client.post(
        "/api/v1/auth/login/email",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

class TestOrganizationIsolation:
    """Test tenant isolation functionality"""
    
    def test_organization_creation_by_super_admin(self, client, super_admin_user):
        """Test that super admin can create organizations"""
        token = get_user_token(client, "superadmin@example.com", "superpass123")
        
        org_data = {
            "name": "New Test Org",
            "subdomain": "newtest",
            "primary_email": "admin@newtest.com",
            "primary_phone": "+1234567891",
            "address1": "456 New Street",
            "city": "New City",
            "state": "New State",
            "pin_code": "54321",
            "country": "India",
            "admin_email": "admin@newtest.com",
            "admin_password": "newadmin123",
            "admin_full_name": "New Admin"
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=org_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["name"] == "New Test Org"
        assert response.json()["subdomain"] == "newtest"
    
    def test_organization_creation_by_regular_user_fails(self, client, test_user):
        """Test that regular users cannot create organizations"""
        token = get_user_token(client, "testuser@example.com", "testpass123")
        
        org_data = {
            "name": "Unauthorized Org",
            "subdomain": "unauthorized",
            "primary_email": "admin@unauthorized.com",
            "primary_phone": "+1234567892",
            "address1": "789 Unauthorized Street",
            "city": "Unauthorized City",
            "state": "Unauthorized State",
            "pin_code": "99999",
            "country": "India",
            "admin_email": "admin@unauthorized.com",
            "admin_password": "unauthorized123",
            "admin_full_name": "Unauthorized Admin"
        }
        
        response = client.post(
            "/api/v1/organizations/",
            json=org_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403

class TestDataIsolation:
    """Test data isolation between tenants"""
    
    def test_user_can_only_see_own_org_data(self, client, test_db, test_user):
        """Test that users can only see data from their organization"""
        # Create another organization
        other_org = Organization(
            name="Other Organization",
            subdomain="other",
            status="active",
            primary_email="other@example.com",
            primary_phone="+1234567893",
            address1="999 Other Street",
            city="Other City",
            state="Other State",
            pin_code="99999",
            country="India"
        )
        test_db.add(other_org)
        test_db.commit()
        
        # Create vendor in user's organization
        user_vendor = Vendor(
            organization_id=test_user.organization_id,
            name="User Vendor",
            contact_number="+1111111111",
            address1="User Vendor Street",
            city="User City",
            state="User State",
            pin_code="11111",
            state_code="US"
        )
        test_db.add(user_vendor)
        
        # Create vendor in other organization
        other_vendor = Vendor(
            organization_id=other_org.id,
            name="Other Vendor",
            contact_number="+2222222222", 
            address1="Other Vendor Street",
            city="Other City",
            state="Other State",
            pin_code="22222",
            state_code="OS"
        )
        test_db.add(other_vendor)
        test_db.commit()
        
        # Get user token and fetch vendors
        token = get_user_token(client, "testuser@example.com", "testpass123")
        
        response = client.get(
            "/api/v1/vendors/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        vendors = response.json()
        
        # User should only see vendor from their organization
        assert len(vendors) == 1
        assert vendors[0]["name"] == "User Vendor"
        assert vendors[0]["organization_id"] == test_user.organization_id
    
    def test_user_cannot_access_other_org_vendor(self, client, test_db, test_user):
        """Test that users cannot access vendors from other organizations"""
        # Create another organization and vendor
        other_org = Organization(
            name="Other Organization",
            subdomain="other",
            status="active",
            primary_email="other@example.com",
            primary_phone="+1234567893",
            address1="999 Other Street",
            city="Other City",
            state="Other State", 
            pin_code="99999",
            country="India"
        )
        test_db.add(other_org)
        test_db.flush()
        
        other_vendor = Vendor(
            organization_id=other_org.id,
            name="Other Vendor",
            contact_number="+2222222222",
            address1="Other Vendor Street",
            city="Other City",
            state="Other State",
            pin_code="22222",
            state_code="OS"
        )
        test_db.add(other_vendor)
        test_db.commit()
        
        # Try to access other org's vendor
        token = get_user_token(client, "testuser@example.com", "testpass123")
        
        response = client.get(
            f"/api/v1/vendors/{other_vendor.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should return 404 (not 403 to avoid information leakage)
        assert response.status_code == 404

class TestUserManagement:
    """Test user management with multi-tenancy"""
    
    def test_admin_can_create_user_in_org(self, client, test_admin_user):
        """Test that admin can create users in their organization"""
        token = get_user_token(client, "admin@example.com", "adminpass123")
        
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpass123",
            "full_name": "New User",
            "role": "standard_user"
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["email"] == "newuser@example.com"
        assert response.json()["organization_id"] == test_admin_user.organization_id
    
    def test_regular_user_cannot_create_user(self, client, test_user):
        """Test that regular users cannot create other users"""
        token = get_user_token(client, "testuser@example.com", "testpass123")
        
        user_data = {
            "email": "unauthorized@example.com",
            "username": "unauthorized",
            "password": "unauthorized123",
            "full_name": "Unauthorized User",
            "role": "standard_user"
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403

class TestAuthentication:
    """Test authentication with multi-tenancy"""
    
    def test_login_with_valid_credentials(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login/email",
            json={"email": "testuser@example.com", "password": "testpass123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["organization_id"] == test_user.organization_id
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login/email",
            json={"email": "invalid@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
    
    def test_token_contains_organization_info(self, client, test_user):
        """Test that JWT token contains organization information"""
        response = client.post(
            "/api/v1/auth/login/email",
            json={"email": "testuser@example.com", "password": "testpass123"}
        )
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Use token to access protected endpoint
        me_response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        assert me_response.json()["organization_id"] == test_user.organization_id

if __name__ == "__main__":
    pytest.main([__file__])