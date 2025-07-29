"""
Test Excel import/export functionality including product/stock interlinking
"""
import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User, Product, Stock
from app.core.security import get_password_hash
from app.schemas.base import UserRole

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_excel.db"

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
        pin_code="12345",
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

def get_auth_token(client: TestClient, email: str, password: str):
    """Get authentication token"""
    response = client.post(
        "/api/v1/auth/login/email",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_test_excel_file(data: list, filename: str = "test.xlsx") -> io.BytesIO:
    """Create test Excel file"""
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer

class TestExcelImportExport:
    """Test Excel import/export functionality"""
    
    def test_product_template_download(self, client, test_admin_user, test_organization):
        """Test product template download"""
        token = get_auth_token(client, "admin@example.com", "adminpass123")
        
        if not token:
            pytest.skip("Could not get authentication token")
        
        response = client.get(
            "/api/v1/products/template/excel",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "products_template.xlsx" in response.headers["content-disposition"]
    
    def test_product_import_with_stock_creation(self, client, test_admin_user, test_organization, test_db):
        """Test product import with automatic stock creation"""
        token = get_auth_token(client, "admin@example.com", "adminpass123")
        
        if not token:
            pytest.skip("Could not get authentication token")
        
        # Create test product data with initial stock
        test_data = [
            {
                "Name": "Test Product 1",
                "HSN Code": "12345678",
                "Part Number": "TP001",
                "Unit": "PCS",
                "Unit Price": 100.0,
                "GST Rate": 18.0,
                "Is GST Inclusive": "FALSE",
                "Reorder Level": 10,
                "Description": "Test product with stock",
                "Is Manufactured": "FALSE",
                "Initial Quantity": 50,
                "Initial Location": "Warehouse A"
            },
            {
                "Name": "Test Product 2",
                "HSN Code": "87654321",
                "Part Number": "TP002",
                "Unit": "KG",
                "Unit Price": 75.0,
                "GST Rate": 12.0,
                "Is GST Inclusive": "FALSE",
                "Reorder Level": 5,
                "Description": "Test product without initial stock",
                "Is Manufactured": "TRUE"
                # No Initial Quantity - should create stock with 0
            }
        ]
        
        excel_file = create_test_excel_file(test_data)
        
        response = client.post(
            "/api/v1/products/import/excel",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test_products.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 2
        assert data["created"] == 2
        assert "stock entries created" in data["message"]
        
        # Verify products were created
        products = test_db.query(Product).filter(Product.organization_id == test_organization.id).all()
        assert len(products) == 2
        
        # Verify stock entries were created
        stocks = test_db.query(Stock).filter(Stock.organization_id == test_organization.id).all()
        assert len(stocks) == 2
        
        # Check specific stock quantities
        product1 = test_db.query(Product).filter(
            Product.name == "Test Product 1",
            Product.organization_id == test_organization.id
        ).first()
        stock1 = test_db.query(Stock).filter(Stock.product_id == product1.id).first()
        assert stock1.quantity == 50
        assert stock1.location == "Warehouse A"
        
        product2 = test_db.query(Product).filter(
            Product.name == "Test Product 2",
            Product.organization_id == test_organization.id
        ).first()
        stock2 = test_db.query(Stock).filter(Stock.product_id == product2.id).first()
        assert stock2.quantity == 0
        assert stock2.location == "Default"
    
    def test_stock_import_with_product_creation(self, client, test_admin_user, test_organization, test_db):
        """Test stock import with automatic product creation"""
        token = get_auth_token(client, "admin@example.com", "adminpass123")
        
        if not token:
            pytest.skip("Could not get authentication token")
        
        # Create test stock data that should create products
        test_data = [
            {
                "Product Name": "Auto Created Product 1",
                "HSN Code": "11111111",
                "Part Number": "ACP001",
                "Unit": "PCS",
                "Unit Price": 50.0,
                "GST Rate": 18.0,
                "Reorder Level": 20,
                "Quantity": 100,
                "Location": "Warehouse B"
            }
        ]
        
        excel_file = create_test_excel_file(test_data)
        
        response = client.post(
            "/api/v1/stock/import/excel",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("test_stock.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 1
        assert "products created" in data["message"]
        assert "stock entries created" in data["message"]
        
        # Verify product was created
        product = test_db.query(Product).filter(
            Product.name == "Auto Created Product 1",
            Product.organization_id == test_organization.id
        ).first()
        assert product is not None
        assert product.hsn_code == "11111111"
        assert product.unit_price == 50.0
        
        # Verify stock was created
        stock = test_db.query(Stock).filter(Stock.product_id == product.id).first()
        assert stock is not None
        assert stock.quantity == 100
        assert stock.location == "Warehouse B"
    
    def test_product_export(self, client, test_admin_user, test_organization, test_db):
        """Test product export functionality"""
        token = get_auth_token(client, "admin@example.com", "adminpass123")
        
        if not token:
            pytest.skip("Could not get authentication token")
        
        # Create test product
        product = Product(
            organization_id=test_organization.id,
            name="Export Test Product",
            hsn_code="99999999",
            unit="PCS",
            unit_price=200.0,
            gst_rate=18.0,
            reorder_level=15
        )
        test_db.add(product)
        test_db.commit()
        
        response = client.get(
            "/api/v1/products/export/excel",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "products_export.xlsx" in response.headers["content-disposition"]
        
        # Verify Excel content
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data)
        assert len(df) >= 1
        assert "Export Test Product" in df["Name"].values

class TestOrganizationUserManagement:
    """Test organization and user management features"""
    
    def test_organization_license_creation(self, client, test_db):
        """Test organization license creation by super admin"""
        # Create super admin user first
        super_admin = User(
            organization_id=1,  # Placeholder
            email="superadmin@system.com",
            username="superadmin",
            hashed_password=get_password_hash("superpass123"),
            full_name="Super Admin",
            role="super_admin",
            is_super_admin=True,
            is_active=True
        )
        test_db.add(super_admin)
        test_db.commit()
        
        token = get_auth_token(client, "superadmin@system.com", "superpass123")
        
        if not token:
            pytest.skip("Could not get authentication token")
        
        license_data = {
            "organization_name": "New Test Organization",
            "superadmin_email": "newadmin@neworg.com"
        }
        
        response = client.post(
            "/api/v1/organizations/license/create",
            headers={"Authorization": f"Bearer {token}"},
            json=license_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["organization_name"] == "New Test Organization"
        assert data["superadmin_email"] == "newadmin@neworg.com"
        assert "subdomain" in data
        assert "temp_password" in data
        
        # Verify organization was created
        org = test_db.query(Organization).filter(
            Organization.name == "New Test Organization"
        ).first()
        assert org is not None
        
        # Verify admin user was created
        admin = test_db.query(User).filter(
            User.email == "newadmin@neworg.com"
        ).first()
        assert admin is not None
        assert admin.organization_id == org.id
        assert admin.role == "org_admin"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])