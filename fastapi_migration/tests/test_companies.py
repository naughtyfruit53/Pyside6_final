"""
Test module for company API endpoints
"""
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User, Company
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_companies.db"
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
    """Create test client"""
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
        pin_code="123456",
        country="India"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_admin_user(test_db, test_organization):
    """Create a test admin user"""
    admin = User(
        organization_id=test_organization.id,
        email="admin@test.com",
        username="admin",
        hashed_password=get_password_hash("password123"),
        full_name="Test Admin",
        role="org_admin",
        is_active=True
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin

def get_auth_token(client: TestClient, email: str = "admin@test.com", password: str = "password123"):
    """Get authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

class TestCompanyAPI:
    """Test Company API endpoints"""

    def test_create_company_success(self, client, test_admin_user, test_organization):
        """Test successful company creation"""
        token = get_auth_token(client)
        assert token is not None, "Failed to get auth token"
        
        headers = {"Authorization": f"Bearer {token}"}
        company_data = {
            "name": "Test Company",
            "address1": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pin_code": "123456",
            "state_code": "27",
            "contact_number": "+91 9876543210",
            "email": "test@company.com"
        }
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Company"
        assert data["organization_id"] == test_organization.id
        assert data["id"] is not None

    def test_create_company_missing_fields(self, client, test_admin_user):
        """Test company creation with missing required fields"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Missing required fields
        company_data = {"name": "Test Company"}
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        
        # Check that all required fields are reported as missing
        error_fields = [error["loc"][1] for error in data["detail"]]
        expected_fields = ["address1", "city", "state", "pin_code", "state_code", "contact_number"]
        for field in expected_fields:
            assert field in error_fields

    def test_create_company_invalid_pin_code(self, client, test_admin_user):
        """Test company creation with invalid pin code"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        company_data = {
            "name": "Test Company",
            "address1": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pin_code": "12345",  # Invalid: should be 6 digits
            "state_code": "27",
            "contact_number": "+91 9876543210"
        }
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert any("pin_code" in error["loc"] for error in data["detail"])
        assert any("Pin code must be 6 digits" in error["msg"] for error in data["detail"])

    def test_create_company_invalid_state_code(self, client, test_admin_user):
        """Test company creation with invalid state code"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        company_data = {
            "name": "Test Company", 
            "address1": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pin_code": "123456",
            "state_code": "2",  # Invalid: should be 2 digits
            "contact_number": "+91 9876543210"
        }
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert any("state_code" in error["loc"] for error in data["detail"])
        assert any("State code must be 2 digits" in error["msg"] for error in data["detail"])

    def test_create_company_invalid_email(self, client, test_admin_user):
        """Test company creation with invalid email"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        company_data = {
            "name": "Test Company",
            "address1": "123 Test Street", 
            "city": "Test City",
            "state": "Test State",
            "pin_code": "123456",
            "state_code": "27",
            "contact_number": "+91 9876543210",
            "email": "invalid-email"  # Invalid email format
        }
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert any("email" in error["loc"] for error in data["detail"])

    def test_create_duplicate_company(self, client, test_admin_user, test_organization, test_db):
        """Test creating duplicate company for same organization"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create first company
        existing_company = Company(
            organization_id=test_organization.id,
            name="Existing Company",
            address1="123 Existing Street",
            city="Existing City",
            state="Existing State", 
            pin_code="123456",
            state_code="27",
            contact_number="+91 9876543210"
        )
        test_db.add(existing_company)
        test_db.commit()
        
        # Try to create another company for same organization
        company_data = {
            "name": "Another Company",
            "address1": "456 Another Street",
            "city": "Another City",
            "state": "Another State",
            "pin_code": "654321",
            "state_code": "28",
            "contact_number": "+91 9876543211"
        }
        
        response = client.post("/api/v1/companies/", json=company_data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "already exist" in data["detail"]

    def test_get_companies(self, client, test_admin_user, test_organization, test_db):
        """Test getting list of companies"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test company
        company = Company(
            organization_id=test_organization.id,
            name="Test Company",
            address1="123 Test Street", 
            city="Test City",
            state="Test State",
            pin_code="123456",
            state_code="27",
            contact_number="+91 9876543210"
        )
        test_db.add(company)
        test_db.commit()
        
        response = client.get("/api/v1/companies/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Test Company"

    def test_get_company_by_id(self, client, test_admin_user, test_organization, test_db):
        """Test getting company by ID"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test company
        company = Company(
            organization_id=test_organization.id,
            name="Test Company",
            address1="123 Test Street",
            city="Test City", 
            state="Test State",
            pin_code="123456",
            state_code="27",
            contact_number="+91 9876543210"
        )
        test_db.add(company)
        test_db.commit()
        test_db.refresh(company)
        
        response = client.get(f"/api/v1/companies/{company.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == company.id
        assert data["name"] == "Test Company"

    def test_get_nonexistent_company(self, client, test_admin_user):
        """Test getting company that doesn't exist"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/companies/99999", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_update_company(self, client, test_admin_user, test_organization, test_db):
        """Test updating company"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test company
        company = Company(
            organization_id=test_organization.id,
            name="Original Company",
            address1="123 Original Street",
            city="Original City",
            state="Original State",
            pin_code="123456",
            state_code="27", 
            contact_number="+91 9876543210"
        )
        test_db.add(company)
        test_db.commit()
        test_db.refresh(company)
        
        # Update company
        update_data = {
            "name": "Updated Company",
            "city": "Updated City"
        }
        
        response = client.put(f"/api/v1/companies/{company.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Company"
        assert data["city"] == "Updated City"
        assert data["address1"] == "123 Original Street"  # Unchanged field

    def test_unauthorized_access(self, client):
        """Test accessing company endpoints without authentication"""
        company_data = {
            "name": "Test Company",
            "address1": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pin_code": "123456",
            "state_code": "27",
            "contact_number": "+91 9876543210"
        }
        
        # Test without auth header
        response = client.post("/api/v1/companies/", json=company_data)
        assert response.status_code == 401
        
        response = client.get("/api/v1/companies/")
        assert response.status_code == 401