"""
Tests for temporary master password functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User
from app.core.security import get_password_hash, verify_password
from app.schemas.base import UserRole

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp_master_password.db"

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
def super_admin_user(test_db):
    """Create the specific super admin user for testing"""
    user = User(
        organization_id=None,  # Super admin has no organization
        email="naughtyfruit53@gmail.com",
        username="naughtyfruit53",
        hashed_password=get_password_hash("originalpassword123"),  # Different from master password
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_super_admin=True,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def other_super_admin_user(test_db):
    """Create another super admin user to test that master password only works for specific email"""
    user = User(
        organization_id=None,
        email="other-admin@example.com",
        username="otheradmin",
        hashed_password=get_password_hash("originalpassword123"),
        full_name="Other Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_super_admin=True,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

def test_master_password_login_success_oauth_form(client, super_admin_user):
    """Test successful login with master password using OAuth2 form endpoint"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "naughtyfruit53@gmail.com",
            "password": "Qweasdzxc"  # Master password
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_role"] == UserRole.SUPER_ADMIN
    assert data["organization_id"] is None  # Super admin has no organization

def test_master_password_login_success_email_endpoint(client, super_admin_user):
    """Test successful login with master password using email endpoint"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "Qweasdzxc"  # Master password
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_role"] == UserRole.SUPER_ADMIN
    assert data["organization_id"] is None

def test_original_password_still_works(client, super_admin_user):
    """Test that the original password still works (master password doesn't break existing functionality)"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "originalpassword123"  # Original password
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_role"] == UserRole.SUPER_ADMIN

def test_master_password_wrong_email(client, other_super_admin_user):
    """Test that master password doesn't work with different email"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "other-admin@example.com",
            "password": "Qweasdzxc"  # Master password
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_wrong_password_with_correct_email(client, super_admin_user):
    """Test that wrong password (not master or original) fails"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "wrongpassword123"  # Wrong password
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_master_password_case_sensitive(client, super_admin_user):
    """Test that master password is case sensitive"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "qweasdzxc"  # Wrong case
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_master_password_exact_match_required(client, super_admin_user):
    """Test that exact master password is required (no partial matches)"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "Qweasdzxc123"  # Extra characters
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_inactive_user_master_password_fails(client, test_db):
    """Test that master password doesn't work for inactive users"""
    user = User(
        organization_id=None,
        email="naughtyfruit53@gmail.com",
        username="naughtyfruit53",
        hashed_password=get_password_hash("originalpassword123"),
        full_name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        is_super_admin=True,
        is_active=False  # Inactive user
    )
    test_db.add(user)
    test_db.commit()
    
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "Qweasdzxc"  # Master password
        }
    )
    
    assert response.status_code == 401
    assert "User account is inactive" in response.json()["detail"]

def test_nonexistent_user_master_password_fails(client):
    """Test that master password doesn't work for non-existent users"""
    response = client.post(
        "/api/auth/login/email",
        json={
            "email": "naughtyfruit53@gmail.com",
            "password": "Qweasdzxc"  # Master password
        }
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]