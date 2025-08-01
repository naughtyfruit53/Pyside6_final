import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.base import Product, Organization, User
from app.schemas.base import ProductCreate, ProductResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_product_name.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_product_name_consistency():
    """Test that product API returns product_name field for frontend consistency"""
    # Clean up test database file
    if os.path.exists("./test_product_name.db"):
        os.remove("./test_product_name.db")
    
    # Create all tables
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create test organization and user
    db = TestingSessionLocal()
    
    # Create organization
    org = Organization(
        name="Test Org",
        subdomain="testorg",
        primary_email="test@example.com",
        primary_phone="1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456"
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Create user
    user = User(
        organization_id=org.id,
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_super_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create product with name field
    product = Product(
        organization_id=org.id,
        name="Test Product",  # Backend uses 'name' field
        unit="PCS",
        unit_price=100.0
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    db.close()
    
    # Test ProductResponse.from_product method
    product_response = ProductResponse.from_product(product)
    
    # Verify that the response uses product_name field
    assert hasattr(product_response, 'product_name')
    assert product_response.product_name == "Test Product"
    assert product_response.id == product.id
    assert product_response.unit == "PCS"
    assert product_response.unit_price == 100.0
    
    # Verify the product_name is mapped from the name field
    assert product_response.product_name == product.name
    
    # Test that API endpoint returns product_name field
    # Note: This would require authentication setup, so we're testing the schema mapping for now
    
    print("✅ Product name standardization test passed")
    print(f"   Backend field: 'name' = '{product.name}'")
    print(f"   Frontend field: 'product_name' = '{product_response.product_name}'")

if __name__ == "__main__":
    test_product_name_consistency()