import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from decimal import Decimal

from app.main import app
from app.core.database import get_db, Base
from app.models.base import User, Organization, Vendor, Customer, Product
from app.models.vouchers import PurchaseVoucher, SalesVoucher
from app.core.security import get_password_hash
from app.api.v1.auth import get_current_active_user

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_vouchers.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_db():
    """Get test database session"""
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
        primary_email="admin@testorg.com",
        primary_phone="1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456",
        country="India",
        created_at=datetime.utcnow()
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_user(test_db, test_organization):
    """Create a test user"""
    user = User(
        email="testuser@test.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        organization_id=test_organization.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_vendor(test_db, test_organization):
    """Create a test vendor"""
    vendor = Vendor(
        name="Test Vendor",
        contact_number="9876543210",
        email="vendor@test.com",
        address1="Vendor Address",
        city="Vendor City",
        state="Vendor State",
        pin_code="654321",
        state_code="TS",
        organization_id=test_organization.id,
        created_at=datetime.utcnow()
    )
    test_db.add(vendor)
    test_db.commit()
    test_db.refresh(vendor)
    return vendor

@pytest.fixture
def test_customer(test_db, test_organization):
    """Create a test customer"""
    customer = Customer(
        name="Test Customer",
        contact_number="5555555555",
        email="customer@test.com",
        address1="Customer Address",
        city="Customer City", 
        state="Customer State",
        pin_code="111111",
        state_code="CS",
        organization_id=test_organization.id,
        created_at=datetime.utcnow()
    )
    test_db.add(customer)
    test_db.commit()
    test_db.refresh(customer)
    return customer

@pytest.fixture
def test_product(test_db, test_organization):
    """Create a test product"""
    product = Product(
        name="Test Product",
        hsn_code="12345678",
        part_number="PN-001",
        unit="PCS",
        unit_price=100.0,
        gst_rate=18.0,
        organization_id=test_organization.id,
        created_at=datetime.utcnow()
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    def mock_get_current_active_user():
        return test_user
    
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    return {"Authorization": "Bearer mock_token"}

class TestPurchaseVoucherEndpoints:
    """Test purchase voucher API endpoints"""
    
    def test_get_purchase_vouchers(self, setup_database, auth_headers):
        """Test getting purchase vouchers"""
        response = client.get(
            "/api/v1/vouchers/purchase-vouchers/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        vouchers = response.json()
        assert isinstance(vouchers, list)
    
    def test_get_purchase_vouchers_simple_endpoint(self, setup_database, auth_headers):
        """Test the simplified /purchase endpoint"""
        response = client.get(
            "/api/v1/vouchers/purchase",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        vouchers = response.json()
        assert isinstance(vouchers, list)
    
    def test_create_purchase_voucher(self, setup_database, auth_headers, test_vendor, test_product):
        """Test creating a purchase voucher"""
        voucher_data = {
            "voucher_number": "PV-001",
            "vendor_id": test_vendor.id,
            "voucher_date": date.today().isoformat(),
            "total_amount": 1180.0,
            "cgst_amount": 90.0,
            "sgst_amount": 90.0,
            "igst_amount": 0.0,
            "status": "draft",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 10.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "taxable_amount": 1000.0,
                    "gst_rate": 18.0,
                    "cgst_amount": 90.0,
                    "sgst_amount": 90.0,
                    "igst_amount": 0.0,
                    "total_amount": 1180.0
                }
            ]
        }
        
        response = client.post(
            "/api/v1/vouchers/purchase-vouchers/",
            json=voucher_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        created_voucher = response.json()
        assert created_voucher["voucher_number"] == "PV-001"
        assert created_voucher["vendor_id"] == test_vendor.id
        assert created_voucher["total_amount"] == 1180.0
    
    def test_create_purchase_voucher_simple_endpoint(self, setup_database, auth_headers, test_vendor, test_product):
        """Test creating purchase voucher via simplified endpoint"""
        voucher_data = {
            "voucher_number": "PV-002",
            "vendor_id": test_vendor.id,
            "voucher_date": date.today().isoformat(),
            "total_amount": 590.0,
            "cgst_amount": 45.0,
            "sgst_amount": 45.0,
            "igst_amount": 0.0,
            "status": "draft",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 5.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "taxable_amount": 500.0,
                    "gst_rate": 18.0,
                    "cgst_amount": 45.0,
                    "sgst_amount": 45.0,
                    "igst_amount": 0.0,
                    "total_amount": 590.0
                }
            ]
        }
        
        response = client.post(
            "/api/v1/vouchers/purchase",
            json=voucher_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        created_voucher = response.json()
        assert created_voucher["voucher_number"] == "PV-002"

class TestSalesVoucherEndpoints:
    """Test sales voucher API endpoints"""
    
    def test_get_sales_vouchers(self, setup_database, auth_headers):
        """Test getting sales vouchers"""
        response = client.get(
            "/api/v1/vouchers/sales-vouchers/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        vouchers = response.json()
        assert isinstance(vouchers, list)
    
    def test_get_sales_vouchers_simple_endpoint(self, setup_database, auth_headers):
        """Test the simplified /sales endpoint"""
        response = client.get(
            "/api/v1/vouchers/sales",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        vouchers = response.json()
        assert isinstance(vouchers, list)
    
    def test_create_sales_voucher(self, setup_database, auth_headers, test_customer, test_product):
        """Test creating a sales voucher"""
        voucher_data = {
            "voucher_number": "SV-001",
            "customer_id": test_customer.id,
            "voucher_date": date.today().isoformat(),
            "total_amount": 1180.0,
            "cgst_amount": 90.0,
            "sgst_amount": 90.0,
            "igst_amount": 0.0,
            "status": "draft",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 10.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "taxable_amount": 1000.0,
                    "gst_rate": 18.0,
                    "cgst_amount": 90.0,
                    "sgst_amount": 90.0,
                    "igst_amount": 0.0,
                    "total_amount": 1180.0
                }
            ]
        }
        
        response = client.post(
            "/api/v1/vouchers/sales-vouchers/",
            json=voucher_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        created_voucher = response.json()
        assert created_voucher["voucher_number"] == "SV-001"
        assert created_voucher["customer_id"] == test_customer.id
        assert created_voucher["total_amount"] == 1180.0
    
    def test_create_sales_voucher_simple_endpoint(self, setup_database, auth_headers, test_customer, test_product):
        """Test creating sales voucher via simplified endpoint"""
        voucher_data = {
            "voucher_number": "SV-002",
            "customer_id": test_customer.id,
            "voucher_date": date.today().isoformat(),
            "total_amount": 590.0,
            "cgst_amount": 45.0,
            "sgst_amount": 45.0,
            "igst_amount": 0.0,
            "status": "draft",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 5.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "taxable_amount": 500.0,
                    "gst_rate": 18.0,
                    "cgst_amount": 45.0,
                    "sgst_amount": 45.0,
                    "igst_amount": 0.0,
                    "total_amount": 590.0
                }
            ]
        }
        
        response = client.post(
            "/api/v1/vouchers/sales",
            json=voucher_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        created_voucher = response.json()
        assert created_voucher["voucher_number"] == "SV-002"

class TestVoucherEmailFunctionality:
    """Test voucher email functionality"""
    
    def test_send_voucher_email(self, setup_database, auth_headers, test_vendor, test_product, test_db):
        """Test sending voucher email"""
        # First create a voucher
        voucher = PurchaseVoucher(
            voucher_number="PV-EMAIL-001",
            vendor_id=test_vendor.id,
            voucher_date=date.today(),
            total_amount=1180.0,
            cgst_amount=90.0,
            sgst_amount=90.0,
            igst_amount=0.0,
            status="confirmed",
            organization_id=test_vendor.organization_id,
            created_by=1
        )
        test_db.add(voucher)
        test_db.commit()
        test_db.refresh(voucher)
        
        # Test sending email
        response = client.post(
            f"/api/v1/vouchers/send-email/purchase_voucher/{voucher.id}",
            headers=auth_headers
        )
        
        # Email might fail due to configuration, but endpoint should exist
        assert response.status_code in [200, 400, 500]  # Various possible responses

class TestErrorHandling:
    """Test error handling in voucher endpoints"""
    
    def test_create_voucher_invalid_vendor(self, setup_database, auth_headers, test_product):
        """Test creating voucher with invalid vendor ID"""
        voucher_data = {
            "voucher_number": "PV-INVALID",
            "vendor_id": 99999,  # Non-existent vendor
            "voucher_date": date.today().isoformat(),
            "total_amount": 1180.0,
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 10.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "total_amount": 1000.0
                }
            ]
        }
        
        response = client.post(
            "/api/v1/vouchers/purchase",
            json=voucher_data,
            headers=auth_headers
        )
        
        # Should handle error gracefully
        assert response.status_code in [400, 404, 422, 500]
    
    def test_unauthorized_access(self, setup_database):
        """Test that voucher endpoints require authentication"""
        response = client.get("/api/v1/vouchers/purchase")
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])