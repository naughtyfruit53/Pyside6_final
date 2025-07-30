"""
Test module for stock API endpoints
"""
import pytest
import io
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User, Product, Stock
from app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stock.db"
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

@pytest.fixture
def test_product(test_db, test_organization):
    """Create a test product"""
    product = Product(
        organization_id=test_organization.id,
        name="Test Product",
        hsn_code="12345678",
        part_number="TP001",
        unit="PCS",
        unit_price=100.0,
        gst_rate=18.0,
        reorder_level=10,
        is_active=True
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product

def get_auth_token(client: TestClient, email: str = "admin@test.com", password: str = "password123"):
    """Get authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_test_excel_file(data: list) -> io.BytesIO:
    """Create test Excel file from data"""
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer

class TestStockAPI:
    """Test Stock API endpoints"""

    def test_get_stock_list(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test getting stock list"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test stock entry
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=50.0,
            unit="PCS",
            location="Warehouse A"
        )
        test_db.add(stock)
        test_db.commit()
        
        response = client.get("/api/v1/stock/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["quantity"] == 50.0

    def test_get_product_stock(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test getting stock for specific product"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test stock entry
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=75.0,
            unit="PCS",
            location="Warehouse B"
        )
        test_db.add(stock)
        test_db.commit()
        
        response = client.get(f"/api/v1/stock/product/{test_product.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 75.0
        assert data["product_id"] == test_product.id

    def test_get_product_stock_not_exists(self, client, test_admin_user, test_organization, test_product):
        """Test getting stock for product without stock entry"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get(f"/api/v1/stock/product/{test_product.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 0.0  # Should return zero stock
        assert data["product_id"] == test_product.id

    def test_create_stock_entry(self, client, test_admin_user, test_organization, test_product):
        """Test creating new stock entry"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        stock_data = {
            "product_id": test_product.id,
            "quantity": 100.0,
            "unit": "PCS",
            "location": "Warehouse C"
        }
        
        response = client.post("/api/v1/stock/", json=stock_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 100.0
        assert data["product_id"] == test_product.id
        assert data["location"] == "Warehouse C"

    def test_update_stock(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test updating stock"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create initial stock
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=50.0,
            unit="PCS",
            location="Warehouse A"
        )
        test_db.add(stock)
        test_db.commit()
        
        # Update stock
        update_data = {
            "quantity": 80.0,
            "location": "Warehouse B"
        }
        
        response = client.put(f"/api/v1/stock/product/{test_product.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 80.0
        assert data["location"] == "Warehouse B"

    def test_adjust_stock(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test stock adjustment"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create initial stock
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=50.0,
            unit="PCS",
            location="Warehouse A"
        )
        test_db.add(stock)
        test_db.commit()
        
        # Adjust stock (add 25)
        response = client.post(
            f"/api/v1/stock/adjust/{test_product.id}?quantity_change=25.0&reason=Manual adjustment",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["new_quantity"] == 75.0

    def test_bulk_import_success(self, client, test_admin_user, test_organization):
        """Test successful bulk import"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test Excel data
        test_data = [
            {
                "Product Name": "Bulk Product 1",
                "HSN Code": "11111111",
                "Part Number": "BP001",
                "Unit": "PCS",
                "Unit Price": 50.0,
                "GST Rate": 18.0,
                "Reorder Level": 20,
                "Quantity": 100,
                "Location": "Warehouse A"
            },
            {
                "Product Name": "Bulk Product 2",
                "HSN Code": "22222222",
                "Part Number": "BP002",
                "Unit": "KG",
                "Unit Price": 75.0,
                "GST Rate": 12.0,
                "Reorder Level": 10,
                "Quantity": 50,
                "Location": "Warehouse B"
            }
        ]
        
        excel_file = create_test_excel_file(test_data)
        
        files = {
            'file': ('test_stock.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 2
        assert data["created"] == 2  # Should create 2 stock entries
        assert "products created" in data["message"]

    def test_bulk_import_missing_columns(self, client, test_admin_user):
        """Test bulk import with missing required columns"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Missing required columns
        test_data = [{"Product Name": "Test Product"}]  # Missing Unit, Quantity
        excel_file = create_test_excel_file(test_data)
        
        files = {
            'file': ('test_missing.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Missing required columns" in data["detail"]

    def test_bulk_import_invalid_data(self, client, test_admin_user):
        """Test bulk import with invalid data types"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        test_data = [
            {
                "Product Name": "Invalid Product",
                "Unit": "PCS",
                "Quantity": "not_a_number",  # Invalid data type
                "Unit Price": "also_invalid"
            }
        ]
        
        excel_file = create_test_excel_file(test_data)
        
        files = {
            'file': ('test_invalid.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 200  # Should process but with errors
        data = response.json()
        assert data["total_processed"] == 1
        assert len(data["errors"]) > 0
        assert "Invalid data format" in data["errors"][0]

    def test_bulk_import_empty_file(self, client, test_admin_user):
        """Test bulk import with empty Excel file"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Empty DataFrame
        excel_file = create_test_excel_file([])
        
        files = {
            'file': ('test_empty.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Excel file is empty" in data["detail"] or "No data found" in data["detail"]

    def test_bulk_import_invalid_file_type(self, client, test_admin_user):
        """Test bulk import with non-Excel file"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        files = {
            'file': ('test.txt', io.BytesIO(b'not an excel file'), 'text/plain')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "Only Excel files" in data["detail"]

    def test_bulk_import_with_existing_products(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test bulk import that updates existing products"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create existing stock entry
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=25.0,
            unit="PCS",
            location="Old Location"
        )
        test_db.add(stock)
        test_db.commit()
        
        # Import data for existing product (should update)
        test_data = [
            {
                "Product Name": test_product.name,  # Existing product
                "Unit": "PCS",
                "Quantity": 100,
                "Location": "New Location"
            }
        ]
        
        excel_file = create_test_excel_file(test_data)
        
        files = {
            'file': ('test_update.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = client.post("/api/v1/stock/bulk", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_processed"] == 1
        assert data["updated"] == 1  # Should update existing stock
        assert data["created"] == 0

    def test_download_template(self, client, test_admin_user):
        """Test downloading stock template"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/stock/template/excel", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "stock_template.xlsx" in response.headers["content-disposition"]

    def test_export_stock(self, client, test_admin_user, test_organization, test_product, test_db):
        """Test exporting stock to Excel"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test stock entry
        stock = Stock(
            organization_id=test_organization.id,
            product_id=test_product.id,
            quantity=75.0,
            unit="PCS",
            location="Export Test Location"
        )
        test_db.add(stock)
        test_db.commit()
        
        response = client.get("/api/v1/stock/export/excel", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "stock_export.xlsx" in response.headers["content-disposition"]

    def test_get_low_stock(self, client, test_admin_user, test_organization, test_db):
        """Test getting low stock items"""
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create product with high reorder level
        product = Product(
            organization_id=test_organization.id,
            name="Low Stock Product",
            unit="PCS",
            unit_price=100.0,
            reorder_level=100,  # High reorder level
            is_active=True
        )
        test_db.add(product)
        test_db.commit()
        test_db.refresh(product)
        
        # Create stock with quantity below reorder level
        stock = Stock(
            organization_id=test_organization.id,
            product_id=product.id,
            quantity=50.0,  # Below reorder level of 100
            unit="PCS",
            location="Low Stock Warehouse"
        )
        test_db.add(stock)
        test_db.commit()
        
        response = client.get("/api/v1/stock/low-stock", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["quantity"] <= 100  # Should be below reorder level

    def test_unauthorized_access(self, client):
        """Test accessing stock endpoints without authentication"""
        # Test without auth header
        response = client.get("/api/v1/stock/")
        assert response.status_code == 401
        
        response = client.post("/api/v1/stock/", json={})
        assert response.status_code == 401
        
        files = {'file': ('test.xlsx', io.BytesIO(b'test'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = client.post("/api/v1/stock/bulk", files=files)
        assert response.status_code == 401