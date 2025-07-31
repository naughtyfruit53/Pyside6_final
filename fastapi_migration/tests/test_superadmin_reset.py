"""
Test superadmin reset functionality for both platform and organization level
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base, engine
from app.models.base import User, Organization, Product, Stock, Vendor, Customer, Company
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_db():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_org_and_users(test_db: Session):
    # Create test organization
    org = Organization(
        name="Test Organization",
        subdomain="testorg",
        primary_email="test@example.com", 
        primary_phone="+1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456"
    )
    test_db.add(org)
    test_db.flush()
    
    # Create organization admin user
    org_admin = User(
        organization_id=org.id,
        email="orgadmin@example.com",
        username="orgadmin",
        hashed_password=get_password_hash("testpass123"),
        full_name="Org Admin User",
        role="org_admin"
    )
    test_db.add(org_admin)
    
    # Create super admin user
    super_admin = User(
        organization_id=None,  # Super admin has no organization
        email="superadmin@example.com",
        username="superadmin",
        hashed_password=get_password_hash("testpass123"),
        full_name="Super Admin User",
        role="super_admin",
        is_super_admin=True
    )
    test_db.add(super_admin)
    
    # Create some test data to reset
    product = Product(
        organization_id=org.id,
        name="Test Product",
        unit="PCS",
        unit_price=100.0,
        gst_rate=18.0
    )
    test_db.add(product)
    test_db.flush()
    
    stock = Stock(
        organization_id=org.id,
        product_id=product.id,
        quantity=50.0,
        unit="PCS"
    )
    test_db.add(stock)
    
    vendor = Vendor(
        organization_id=org.id,
        name="Test Vendor",
        contact_number="+1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456",
        state_code="01"
    )
    test_db.add(vendor)
    
    test_db.commit()
    
    return org, org_admin, super_admin

@pytest.fixture
def org_admin_headers(client: TestClient, test_org_and_users):
    org, org_admin, super_admin = test_org_and_users
    
    # Login as organization admin
    login_data = {
        "email": org_admin.email,
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def super_admin_headers(client: TestClient, test_org_and_users):
    org, org_admin, super_admin = test_org_and_users
    
    # Login as super admin
    login_data = {
        "email": super_admin.email,
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

def test_org_admin_can_reset_organization_data(client: TestClient, org_admin_headers, test_org_and_users, test_db: Session):
    """Test that organization admin can reset their organization's data"""
    org, org_admin, super_admin = test_org_and_users
    
    # Verify test data exists before reset
    products_before = test_db.query(Product).filter(Product.organization_id == org.id).count()
    stocks_before = test_db.query(Stock).filter(Stock.organization_id == org.id).count()
    vendors_before = test_db.query(Vendor).filter(Vendor.organization_id == org.id).count()
    
    assert products_before > 0
    assert stocks_before > 0
    assert vendors_before > 0
    
    # Reset organization data
    response = client.post("/api/v1/organizations/reset-data", headers=org_admin_headers)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "message" in response_data
    assert "Organization data has been reset successfully" in response_data["message"]
    assert "details" in response_data
    
    # Verify data was deleted
    test_db.refresh(org)  # Refresh session
    products_after = test_db.query(Product).filter(Product.organization_id == org.id).count()
    stocks_after = test_db.query(Stock).filter(Stock.organization_id == org.id).count()
    vendors_after = test_db.query(Vendor).filter(Vendor.organization_id == org.id).count()
    
    assert products_after == 0
    assert stocks_after == 0  
    assert vendors_after == 0
    
    # Verify organization still exists
    org_exists = test_db.query(Organization).filter(Organization.id == org.id).first()
    assert org_exists is not None

def test_super_admin_can_reset_specific_organization(client: TestClient, super_admin_headers, test_org_and_users, test_db: Session):
    """Test that super admin can reset a specific organization's data"""
    org, org_admin, super_admin = test_org_and_users
    
    # Verify test data exists before reset
    products_before = test_db.query(Product).filter(Product.organization_id == org.id).count()
    assert products_before > 0
    
    # Reset specific organization data as super admin
    response = client.post(f"/api/v1/organizations/reset-data?organization_id={org.id}", headers=super_admin_headers)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "message" in response_data
    assert f"Data reset successfully for organization: {org.name}" in response_data["message"]
    
    # Verify data was deleted for that organization
    test_db.refresh(org)
    products_after = test_db.query(Product).filter(Product.organization_id == org.id).count()
    assert products_after == 0

def test_super_admin_can_reset_all_data(client: TestClient, super_admin_headers, test_org_and_users, test_db: Session):
    """Test that super admin can reset all system data"""
    org, org_admin, super_admin = test_org_and_users
    
    # Verify test data exists before reset
    total_products_before = test_db.query(Product).count()
    total_organizations_before = test_db.query(Organization).count()
    assert total_products_before > 0
    assert total_organizations_before > 0
    
    # Reset all data as super admin
    response = client.post("/api/v1/organizations/reset-data", headers=super_admin_headers)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "message" in response_data
    assert "All system data has been reset successfully" in response_data["message"]
    
    # Verify all business data was deleted
    test_db.refresh(org)
    total_products_after = test_db.query(Product).count()
    assert total_products_after == 0

def test_regular_user_cannot_reset_data(client: TestClient, test_org_and_users, test_db: Session):
    """Test that regular users cannot access reset functionality"""
    org, org_admin, super_admin = test_org_and_users
    
    # Create regular user
    regular_user = User(
        organization_id=org.id,
        email="regularuser@example.com",
        username="regularuser",
        hashed_password=get_password_hash("testpass123"),
        full_name="Regular User",
        role="standard_user"
    )
    test_db.add(regular_user)
    test_db.commit()
    
    # Login as regular user
    login_data = {
        "email": regular_user.email,
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to reset data
    response = client.post("/api/v1/organizations/reset-data", headers=headers)
    assert response.status_code == 403
    assert "don't have permission to reset data" in response.json()["detail"]

def test_unauthenticated_user_cannot_reset_data(client: TestClient):
    """Test that unauthenticated users cannot access reset functionality"""
    
    # Try to reset data without authentication
    response = client.post("/api/v1/organizations/reset-data")
    assert response.status_code == 401

def test_reset_preserves_user_accounts(client: TestClient, org_admin_headers, test_org_and_users, test_db: Session):
    """Test that organization reset preserves user accounts but resets business data"""
    org, org_admin, super_admin = test_org_and_users
    
    # Verify users exist before reset
    org_users_before = test_db.query(User).filter(User.organization_id == org.id).count()
    assert org_users_before > 0
    
    # Reset organization data
    response = client.post("/api/v1/organizations/reset-data", headers=org_admin_headers)
    assert response.status_code == 200
    
    # Verify organization admin user still exists
    test_db.refresh(org_admin)
    org_admin_after = test_db.query(User).filter(User.id == org_admin.id).first()
    assert org_admin_after is not None
    assert org_admin_after.email == org_admin.email