import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.base import User, Organization, Company
from app.core.database import get_db
from app.core.security import get_password_hash
import tempfile
import os


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    db_fd, db_path = tempfile.mkstemp()
    
    # Set environment variable for test database
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    yield db_path
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client():
    """Create test client"""
    from app.core.database import create_tables
    create_tables()
    return TestClient(app)


@pytest.fixture
def test_super_admin(client):
    """Create a test super admin user"""
    db = next(get_db())
    admin = User(
        email="naughtyfruit53@gmail.com",
        username="super_admin",
        hashed_password=get_password_hash("testpass123"),
        full_name="Super Admin",
        role="super_admin",
        is_super_admin=True,
        is_active=True,
        organization_id=None
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_org_admin(client):
    """Create a test organization and admin"""
    db = next(get_db())
    
    # Create organization
    org = Organization(
        name="Test Organization",
        subdomain="testorg",
        primary_email="admin@testorg.com",
        primary_phone="+91-1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456",
        company_details_completed=True
    )
    db.add(org)
    db.flush()
    
    # Create org admin
    admin = User(
        organization_id=org.id,
        email="admin@testorg.com",
        username="org_admin",
        hashed_password=get_password_hash("testpass123"),
        full_name="Org Admin",
        role="org_admin",
        is_active=True
    )
    db.add(admin)
    
    # Create a company for the org
    company = Company(
        organization_id=org.id,
        name="Test Company",
        address1="Company Address",
        city="Company City",
        state="Company State",
        pin_code="654321",
        state_code="27",
        contact_number="+91-9876543210"
    )
    db.add(company)
    
    db.commit()
    db.refresh(admin)
    return admin


def get_auth_token(client, email="naughtyfruit53@gmail.com", password="testpass123"):
    """Get authentication token"""
    response = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    return response.json()["access_token"]


class TestDatabaseReset:
    
    def test_super_admin_reset_all_data(self, client, test_super_admin, test_org_admin):
        """Test super admin can reset all data"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Verify data exists
        db = next(get_db())
        assert db.query(Organization).count() > 0
        assert db.query(Company).count() > 0
        
        # Reset all data
        response = client.post("/api/v1/organizations/reset-data", headers=headers)
        
        assert response.status_code == 200
        assert "All data reset successfully" in response.json()["message"]
        
        # Verify data is deleted
        assert db.query(Organization).count() == 0
        assert db.query(Company).count() == 0
        # Super admin should still exist
        assert db.query(User).filter(User.is_super_admin == True).count() == 1
    
    def test_org_admin_reset_own_data(self, client, test_org_admin):
        """Test org admin can reset only their organization's data"""
        # Login as org admin
        token = get_auth_token(client, "admin@testorg.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Verify data exists
        db = next(get_db())
        org_id = test_org_admin.organization_id
        assert db.query(Company).filter(Company.organization_id == org_id).count() > 0
        
        # Reset organization data
        response = client.post("/api/v1/organizations/reset-data", headers=headers)
        
        assert response.status_code == 200
        assert "Data reset successfully for your organization" in response.json()["message"]
        
        # Verify organization data is deleted
        assert db.query(Company).filter(Company.organization_id == org_id).count() == 0
        # Organization should still exist but marked as incomplete
        org = db.query(Organization).filter(Organization.id == org_id).first()
        assert org is not None
        assert org.company_details_completed == False
    
    def test_unauthorized_reset_access(self, client):
        """Test unauthorized users cannot reset data"""
        # Try without token
        response = client.post("/api/v1/organizations/reset-data")
        assert response.status_code == 401
        
        # Try with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/v1/organizations/reset-data", headers=headers)
        assert response.status_code == 401