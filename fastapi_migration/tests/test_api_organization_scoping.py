#!/usr/bin/env python3
"""
Test suite for API endpoints with organization-level scoping
"""

import os
import sys
import pytest
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import get_db, Base
from app.models.base import PlatformUser, Organization, User, Vendor, Customer, Product
from app.models.vouchers import PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings

class TestOrganizationScoping:
    """Test organization-level data scoping in API endpoints"""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            yield db_url
            # Cleanup
            try:
                os.unlink(tmp.name)
            except:
                pass
    
    @pytest.fixture
    def test_db(self, temp_db_url):
        """Create test database session"""
        # Set required env vars
        os.environ['SMTP_USERNAME'] = 'test@example.com'
        os.environ['SMTP_PASSWORD'] = 'testpass'
        os.environ['EMAILS_FROM_EMAIL'] = 'test@example.com'
        
        engine = create_engine(temp_db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
            app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_data(self, test_db):
        """Create test data with multiple organizations"""
        # Create platform admin
        platform_admin = PlatformUser(
            email="admin@platform.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Platform Admin",
            role="super_admin",
            is_active=True
        )
        test_db.add(platform_admin)
        
        # Create two organizations
        org1 = Organization(
            name="Organization One",
            subdomain="org1",
            status="active",
            business_type="Manufacturing",
            primary_email="admin@org1.com",
            primary_phone="+1-555-0001",
            address1="123 Org1 Street",
            city="City1",
            state="State1",
            pin_code="12345",
            country="Country1"
        )
        
        org2 = Organization(
            name="Organization Two",
            subdomain="org2",
            status="active",
            business_type="Trading",
            primary_email="admin@org2.com",
            primary_phone="+1-555-0002",
            address1="456 Org2 Avenue",
            city="City2",
            state="State2",
            pin_code="67890",
            country="Country2"
        )
        
        test_db.add_all([org1, org2])
        test_db.flush()
        
        # Create users for each organization
        user1 = User(
            organization_id=org1.id,
            email="user@org1.com",
            username="user1",
            hashed_password=get_password_hash("user123"),
            full_name="User One",
            role="standard_user",
            is_active=True
        )
        
        admin1 = User(
            organization_id=org1.id,
            email="admin@org1.com",
            username="admin1",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin One",
            role="org_admin",
            is_active=True
        )
        
        user2 = User(
            organization_id=org2.id,
            email="user@org2.com",
            username="user2",
            hashed_password=get_password_hash("user123"),
            full_name="User Two",
            role="standard_user",
            is_active=True
        )
        
        test_db.add_all([user1, admin1, user2])
        test_db.flush()
        
        # Create vendors for each organization
        vendor1 = Vendor(
            organization_id=org1.id,
            name="Vendor One",
            contact_number="+1-555-1001",
            email="vendor1@example.com",
            address1="Vendor1 Street",
            city="VendorCity1",
            state="VendorState1",
            pin_code="11111",
            state_code="VS1"
        )
        
        vendor2 = Vendor(
            organization_id=org2.id,
            name="Vendor Two",
            contact_number="+1-555-2002",
            email="vendor2@example.com",
            address1="Vendor2 Street",
            city="VendorCity2",
            state="VendorState2",
            pin_code="22222",
            state_code="VS2"
        )
        
        test_db.add_all([vendor1, vendor2])
        test_db.flush()
        
        # Create products for each organization
        product1 = Product(
            organization_id=org1.id,
            name="Product One",
            hsn_code="12345678",
            unit="PCS",
            unit_price=100.0,
            gst_rate=18.0
        )
        
        product2 = Product(
            organization_id=org2.id,
            name="Product Two",
            hsn_code="87654321",
            unit="KG",
            unit_price=50.0,
            gst_rate=18.0
        )
        
        test_db.add_all([product1, product2])
        test_db.commit()
        
        return {
            'platform_admin': platform_admin,
            'org1': org1,
            'org2': org2,
            'user1': user1,
            'admin1': admin1,
            'user2': user2,
            'vendor1': vendor1,
            'vendor2': vendor2,
            'product1': product1,
            'product2': product2
        }
    
    def get_auth_headers(self, user_email: str, organization_id: int = None, user_type: str = "organization"):
        """Get authentication headers for API requests"""
        token = create_access_token(
            data={
                "sub": user_email,
                "organization_id": organization_id,
                "user_type": user_type
            }
        )
        return {"Authorization": f"Bearer {token}"}
    
    def test_vendor_organization_isolation(self, test_data):
        """Test that vendors are isolated by organization"""
        client = TestClient(app)
        
        # User from org1 should only see vendors from org1
        headers = self.get_auth_headers("user@org1.com", test_data['org1'].id)
        response = client.get("/api/v1/vendors/", headers=headers)
        
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 1
        assert vendors[0]["name"] == "Vendor One"
        assert vendors[0]["organization_id"] == test_data['org1'].id
        
        # User from org2 should only see vendors from org2
        headers = self.get_auth_headers("user@org2.com", test_data['org2'].id)
        response = client.get("/api/v1/vendors/", headers=headers)
        
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 1
        assert vendors[0]["name"] == "Vendor Two"
        assert vendors[0]["organization_id"] == test_data['org2'].id
    
    def test_cross_organization_access_denied(self, test_data):
        """Test that users cannot access data from other organizations"""
        client = TestClient(app)
        
        # User from org1 tries to access vendor from org2
        headers = self.get_auth_headers("user@org1.com", test_data['org1'].id)
        response = client.get(f"/api/v1/vendors/{test_data['vendor2'].id}", headers=headers)
        
        assert response.status_code == 404  # Vendor not found in user's organization
    
    def test_platform_admin_access(self, test_data):
        """Test that platform admin can access data from any organization"""
        client = TestClient(app)
        
        # Platform admin can access vendors from org1
        headers = self.get_auth_headers("admin@platform.com", user_type="platform")
        response = client.get(f"/api/v1/vendors/?organization_id={test_data['org1'].id}", headers=headers)
        
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 1
        assert vendors[0]["name"] == "Vendor One"
        
        # Platform admin can access vendors from org2
        response = client.get(f"/api/v1/vendors/?organization_id={test_data['org2'].id}", headers=headers)
        
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 1
        assert vendors[0]["name"] == "Vendor Two"
    
    def test_vendor_creation_with_organization_validation(self, test_data):
        """Test vendor creation with organization validation"""
        client = TestClient(app)
        
        # User from org1 creates a vendor
        headers = self.get_auth_headers("admin@org1.com", test_data['org1'].id)
        vendor_data = {
            "name": "New Vendor Org1",
            "contact_number": "+1-555-9999",
            "email": "newvendor@org1.com",
            "address1": "New Address",
            "city": "NewCity",
            "state": "NewState",
            "pin_code": "99999",
            "state_code": "NS"
        }
        
        response = client.post("/api/v1/vendors/", json=vendor_data, headers=headers)
        
        assert response.status_code == 200
        created_vendor = response.json()
        assert created_vendor["name"] == "New Vendor Org1"
        assert created_vendor["organization_id"] == test_data['org1'].id
    
    def test_duplicate_vendor_name_in_organization(self, test_data):
        """Test that duplicate vendor names within an organization are not allowed"""
        client = TestClient(app)
        
        headers = self.get_auth_headers("admin@org1.com", test_data['org1'].id)
        vendor_data = {
            "name": "Vendor One",  # Same name as existing vendor in org1
            "contact_number": "+1-555-8888",
            "email": "duplicate@org1.com",
            "address1": "Duplicate Address",
            "city": "DuplicateCity",
            "state": "DuplicateState",
            "pin_code": "88888",
            "state_code": "DS"
        }
        
        response = client.post("/api/v1/vendors/", json=vendor_data, headers=headers)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_vendor_search_organization_scoped(self, test_data):
        """Test vendor search is scoped to organization"""
        client = TestClient(app)
        
        # User from org1 searches for vendors
        headers = self.get_auth_headers("user@org1.com", test_data['org1'].id)
        response = client.post("/api/v1/vendors/search", 
                              params={"search_term": "Vendor"}, 
                              headers=headers)
        
        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors) == 1
        assert vendors[0]["name"] == "Vendor One"
        assert vendors[0]["organization_id"] == test_data['org1'].id
    
    def test_purchase_order_workflow(self, test_data):
        """Test complete purchase order workflow with organization scoping"""
        client = TestClient(app)
        
        headers = self.get_auth_headers("admin@org1.com", test_data['org1'].id)
        
        # Create purchase order
        po_data = {
            "vendor_id": test_data['vendor1'].id,
            "date": "2025-01-01T10:00:00",
            "delivery_date": "2025-01-15T10:00:00",
            "total_amount": 1180.0,
            "items": [
                {
                    "product_id": test_data['product1'].id,
                    "quantity": 10.0,
                    "unit": "PCS",
                    "unit_price": 100.0,
                    "total_amount": 1000.0
                }
            ]
        }
        
        response = client.post("/api/v1/vouchers/purchase-orders", json=po_data, headers=headers)
        
        assert response.status_code == 200
        po = response.json()
        assert po["vendor_id"] == test_data['vendor1'].id
        assert po["organization_id"] == test_data['org1'].id
        assert len(po["items"]) == 1
        
        # Get auto-populate data for GRN
        response = client.get(f"/api/v1/vouchers/purchase-orders/{po['id']}/grn-auto-populate", 
                             headers=headers)
        
        assert response.status_code == 200
        grn_data = response.json()
        assert grn_data["purchase_order"]["id"] == po["id"]
        assert len(grn_data["grn_data"]["items"]) == 1
    
    def test_voucher_organization_isolation(self, test_data):
        """Test that vouchers are isolated by organization"""
        client = TestClient(app)
        
        # Create PO in org1
        headers1 = self.get_auth_headers("admin@org1.com", test_data['org1'].id)
        po_data = {
            "vendor_id": test_data['vendor1'].id,
            "date": "2025-01-01T10:00:00",
            "total_amount": 1000.0,
            "items": []
        }
        
        response = client.post("/api/v1/vouchers/purchase-orders", json=po_data, headers=headers1)
        assert response.status_code == 200
        po1 = response.json()
        
        # User from org2 should not see PO from org1
        headers2 = self.get_auth_headers("user@org2.com", test_data['org2'].id)
        response = client.get("/api/v1/vouchers/purchase-orders", headers=headers2)
        
        assert response.status_code == 200
        pos = response.json()
        assert len(pos) == 0  # No POs visible to org2 user
        
        # User from org2 should not be able to access PO from org1
        response = client.get(f"/api/v1/vouchers/purchase-orders/{po1['id']}/grn-auto-populate", 
                             headers=headers2)
        
        assert response.status_code == 404  # PO not found in org2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])