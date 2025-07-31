"""
Test product name consistency across API responses and Excel import/export
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base, engine
from app.models.base import User, Organization, Product, Stock
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
import io
import pandas as pd

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
def test_org_and_user(test_db: Session):
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
    
    # Create test user
    user = User(
        organization_id=org.id,
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    
    return org, user

@pytest.fixture
def auth_headers(client: TestClient, test_org_and_user):
    org, user = test_org_and_user
    
    # Login to get token
    login_data = {
        "email": user.email,
        "password": "testpass123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}

def test_product_api_returns_product_name_field(client: TestClient, auth_headers, test_org_and_user):
    """Test that product API returns product_name field consistently"""
    org, user = test_org_and_user
    
    # Create a test product
    product_data = {
        "name": "Test Product",
        "hsn_code": "1234",
        "unit": "PCS", 
        "unit_price": 100.0,
        "gst_rate": 18.0
    }
    
    # Create product
    response = client.post("/api/v1/products/", json=product_data, headers=auth_headers)
    assert response.status_code == 200
    
    created_product = response.json()
    assert "product_name" in created_product
    assert created_product["product_name"] == "Test Product"
    
    # Get products list
    response = client.get("/api/v1/products/", headers=auth_headers)
    assert response.status_code == 200
    
    products = response.json()
    assert len(products) > 0
    assert "product_name" in products[0]
    assert products[0]["product_name"] == "Test Product"
    
    # Get single product
    product_id = created_product["id"]
    response = client.get(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    
    product = response.json()
    assert "product_name" in product
    assert product["product_name"] == "Test Product"

def test_stock_api_returns_product_name_field(client: TestClient, auth_headers, test_org_and_user, test_db: Session):
    """Test that stock API returns product_name field consistently"""
    org, user = test_org_and_user
    
    # Create a test product
    product = Product(
        organization_id=org.id,
        name="Test Stock Product",
        unit="PCS",
        unit_price=50.0,
        gst_rate=18.0
    )
    test_db.add(product)
    test_db.flush()
    
    # Create stock entry
    stock = Stock(
        organization_id=org.id,
        product_id=product.id,
        quantity=100.0,
        unit="PCS"
    )
    test_db.add(stock)
    test_db.commit()
    
    # Get stock list
    response = client.get("/api/v1/stock/", headers=auth_headers)
    assert response.status_code == 200
    
    stock_items = response.json()
    assert len(stock_items) > 0
    assert "product_name" in stock_items[0]
    assert stock_items[0]["product_name"] == "Test Stock Product"

def test_product_excel_export_uses_product_name_column(client: TestClient, auth_headers, test_org_and_user, test_db: Session):
    """Test that product Excel export uses 'Product Name' column header"""
    org, user = test_org_and_user
    
    # Create a test product
    product = Product(
        organization_id=org.id,
        name="Excel Test Product",
        unit="PCS",
        unit_price=75.0,
        gst_rate=18.0
    )
    test_db.add(product)
    test_db.commit()
    
    # Export products to Excel
    response = client.get("/api/v1/products/export/excel", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify the response is an Excel file
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Read the Excel content
    excel_content = io.BytesIO(response.content)
    df = pd.read_excel(excel_content)
    
    # Check that 'Product Name' column exists and has correct data
    assert "Product Name" in df.columns
    assert df["Product Name"].iloc[0] == "Excel Test Product"

def test_product_excel_template_has_product_name_column(client: TestClient, auth_headers):
    """Test that product Excel template uses 'Product Name' column header"""
    
    # Download template
    response = client.get("/api/v1/products/template/excel", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify the response is an Excel file
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Read the Excel content
    excel_content = io.BytesIO(response.content)
    df = pd.read_excel(excel_content)
    
    # Check that 'Product Name' column exists in template
    assert "Product Name" in df.columns

def test_stock_excel_export_uses_product_name_column(client: TestClient, auth_headers, test_org_and_user, test_db: Session):
    """Test that stock Excel export uses 'Product Name' column header"""
    org, user = test_org_and_user
    
    # Create a test product and stock
    product = Product(
        organization_id=org.id,
        name="Stock Excel Test Product",
        unit="PCS",
        unit_price=25.0,
        gst_rate=18.0
    )
    test_db.add(product)
    test_db.flush()
    
    stock = Stock(
        organization_id=org.id,
        product_id=product.id,
        quantity=200.0,
        unit="PCS"
    )
    test_db.add(stock)
    test_db.commit()
    
    # Export stock to Excel
    response = client.get("/api/v1/stock/export/excel", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify the response is an Excel file
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Read the Excel content
    excel_content = io.BytesIO(response.content)
    df = pd.read_excel(excel_content)
    
    # Check that 'Product Name' column exists and has correct data
    assert "Product Name" in df.columns
    assert df["Product Name"].iloc[0] == "Stock Excel Test Product"

def test_stock_excel_template_has_product_name_column(client: TestClient, auth_headers):
    """Test that stock Excel template uses 'Product Name' column header"""
    
    # Download template
    response = client.get("/api/v1/stock/template/excel", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify the response is an Excel file
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Read the Excel content
    excel_content = io.BytesIO(response.content)
    df = pd.read_excel(excel_content)
    
    # Check that 'Product Name' column exists in template
    assert "Product Name" in df.columns