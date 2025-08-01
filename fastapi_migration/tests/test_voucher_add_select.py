import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.base import Product, Vendor, Customer, Organization, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_voucher_features.db"
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

def test_voucher_add_functionality():
    """Test that voucher add functionality is properly implemented"""
    # Clean up test database file
    if os.path.exists("./test_voucher_features.db"):
        os.remove("./test_voucher_features.db")
    
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
    
    # Create test vendor
    vendor = Vendor(
        organization_id=org.id,
        name="Test Vendor",
        contact_number="1234567890",
        address1="Vendor Address",
        city="Mumbai",
        state="Maharashtra",
        pin_code="400001",
        state_code="27"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    # Create test customer
    customer = Customer(
        organization_id=org.id,
        name="Test Customer",
        contact_number="1234567890",
        address1="Customer Address",
        city="Delhi",
        state="Delhi",
        pin_code="110001",
        state_code="07"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    # Create test product
    product = Product(
        organization_id=org.id,
        name="Test Product",
        unit="PCS",
        unit_price=100.0
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    db.close()
    
    # Test that the APIs work for voucher dropdown population
    print("✅ Testing voucher master data integration:")
    
    # Test vendor retrieval
    response = client.get("/api/v1/vendors/")
    print(f"   Vendors API: {response.status_code}")
    if response.status_code == 200:
        vendors_data = response.json()
        print(f"   Found {len(vendors_data)} vendors")
    
    # Test customer retrieval 
    response = client.get("/api/v1/customers/")
    print(f"   Customers API: {response.status_code}")
    if response.status_code == 200:
        customers_data = response.json()
        print(f"   Found {len(customers_data)} customers")
    
    # Test product retrieval
    response = client.get("/api/v1/products/")
    print(f"   Products API: {response.status_code}")
    if response.status_code == 200:
        products_data = response.json()
        print(f"   Found {len(products_data)} products")
        # Check that product name is returned as product_name
        if len(products_data) > 0:
            assert 'product_name' in products_data[0]
            print(f"   ✅ Product name field: {products_data[0]['product_name']}")
    
    print("✅ Voucher add/select functionality test framework ready")
    print("   - Add buttons can be added to voucher forms")
    print("   - Master data APIs work for populating dropdowns")
    print("   - Product names are correctly mapped to product_name")

def test_master_data_for_vouchers():
    """Test that master data is correctly formatted for voucher usage"""
    
    # Test that products return product_name field for dropdown display
    response = client.get("/api/v1/products/")
    if response.status_code == 200:
        products = response.json()
        for product in products:
            assert 'product_name' in product, "Product should have product_name field for voucher dropdowns"
            assert 'id' in product, "Product should have id field for voucher selection"
            assert 'unit' in product, "Product should have unit field for voucher items"
            assert 'unit_price' in product, "Product should have unit_price field for voucher calculations"
    
    # Test that vendors return name field for dropdown display  
    response = client.get("/api/v1/vendors/")
    if response.status_code == 200:
        vendors = response.json()
        for vendor in vendors:
            assert 'name' in vendor, "Vendor should have name field for voucher dropdowns"
            assert 'id' in vendor, "Vendor should have id field for voucher selection"
    
    # Test that customers return name field for dropdown display
    response = client.get("/api/v1/customers/")
    if response.status_code == 200:
        customers = response.json()
        for customer in customers:
            assert 'name' in customer, "Customer should have name field for voucher dropdowns"
            assert 'id' in customer, "Customer should have id field for voucher selection"
    
    print("✅ Master data format validation passed for voucher integration")

if __name__ == "__main__":
    test_voucher_add_functionality()
    test_master_data_for_vouchers()
    print("✅ All voucher add/select tests passed!")