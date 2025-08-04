"""
Focused test for mandatory password change functionality
Tests the password change endpoint without requiring the full app dependencies
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db, Base
from app.models.base import Organization, User
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserRole
from app.api.v1.password import router as password_router
from app.api.v1.user import get_current_active_user

# Create minimal test app
test_app = FastAPI()
test_app.include_router(password_router, prefix="/auth/password")

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mandatory_password.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock the user service to avoid dependencies
class MockUserService:
    @staticmethod
    def clear_temporary_password(db, user):
        # Mock implementation
        pass

# Mock audit logger
class MockAuditLogger:
    @staticmethod
    def log_password_reset(**kwargs):
        # Mock implementation
        pass

# Patch the dependencies
import app.api.v1.password
app.api.v1.password.UserService = MockUserService
app.api.v1.password.AuditLogger = MockAuditLogger

# Mock get_client_ip and get_user_agent
def mock_get_client_ip(request):
    return "127.0.0.1"

def mock_get_user_agent(request):
    return "test-agent"

app.api.v1.password.get_client_ip = mock_get_client_ip
app.api.v1.password.get_user_agent = mock_get_user_agent

test_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    yield TestClient(test_app)
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
        subdomain="testorg",
        primary_email="test@testorg.com",
        primary_phone="+91-1234567890",
        address1="Test Address",
        city="Test City",
        state="Test State",
        pin_code="123456"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_user_normal(test_db, test_organization):
    """Create a normal test user (must_change_password=False)"""
    user = User(
        organization_id=test_organization.id,
        email="normaluser@example.com",
        username="normaluser",
        hashed_password=get_password_hash("oldpassword123"),
        full_name="Normal User",
        role=UserRole.STANDARD_USER,
        is_active=True,
        must_change_password=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_user_mandatory(test_db, test_organization):
    """Create a test user with mandatory password change (must_change_password=True)"""
    user = User(
        organization_id=test_organization.id,
        email="mandatoryuser@example.com",
        username="mandatoryuser",
        hashed_password=get_password_hash("temppassword123"),
        full_name="Mandatory User",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        must_change_password=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

def mock_get_current_user(user):
    """Create a mock dependency for getting current user"""
    def _get_current_user():
        return user
    return _get_current_user

def test_mandatory_password_change_without_current_password(client, test_user_mandatory):
    """Test mandatory password change without providing current password"""
    
    # Override the dependency to return our test user
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user(test_user_mandatory)
    
    password_data = {
        "new_password": "NewSecurePassword123!"
        # Note: no current_password provided
    }
    
    response = client.post(
        "/auth/password/change",
        json=password_data
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]

def test_mandatory_password_change_with_current_password(client, test_user_mandatory):
    """Test mandatory password change with current password (should still work)"""
    
    # Override the dependency to return our test user
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user(test_user_mandatory)
    
    password_data = {
        "current_password": "temppassword123",
        "new_password": "NewSecurePassword123!"
    }
    
    response = client.post(
        "/auth/password/change",
        json=password_data
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]

def test_normal_user_password_change_requires_current_password(client, test_user_normal):
    """Test normal user password change requires current password"""
    
    # Override the dependency to return our test user
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user(test_user_normal)
    
    password_data = {
        "new_password": "NewSecurePassword123!"
        # Note: no current_password provided
    }
    
    response = client.post(
        "/auth/password/change",
        json=password_data
    )
    
    assert response.status_code == 400
    assert "Current password is required" in response.json()["detail"]

def test_normal_user_password_change_with_wrong_current_password(client, test_user_normal):
    """Test normal user password change with wrong current password"""
    
    # Override the dependency to return our test user
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user(test_user_normal)
    
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "NewSecurePassword123!"
    }
    
    response = client.post(
        "/auth/password/change",
        json=password_data
    )
    
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]

def test_normal_user_password_change_success(client, test_user_normal):
    """Test normal user password change with correct current password"""
    
    # Override the dependency to return our test user
    test_app.dependency_overrides[get_current_active_user] = mock_get_current_user(test_user_normal)
    
    password_data = {
        "current_password": "oldpassword123",
        "new_password": "NewSecurePassword123!"
    }
    
    response = client.post(
        "/auth/password/change",
        json=password_data
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])