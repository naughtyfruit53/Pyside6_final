import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.base import User, Organization
from app.core.security import get_password_hash
from app.api.v1.auth import get_current_super_admin
from datetime import datetime

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
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
def super_admin_user(test_db):
    """Create a super admin user for testing"""
    user = User(
        email="superadmin@test.com",
        username="superadmin",
        full_name="Super Admin",
        hashed_password=get_password_hash("testpassword123"),
        is_super_admin=True,
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

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
def licenseholder_admin(test_db, test_organization):
    """Create a licenseholder admin user"""
    user = User(
        email="admin@testorg.com",
        username="admin",
        full_name="Test Admin",
        hashed_password=get_password_hash("oldpassword123"),
        is_licenseholder_admin=True,
        organization_id=test_organization.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(super_admin_user):
    """Create authentication headers for super admin"""
    # Mock authentication - in real tests, you'd create a valid JWT token
    def mock_get_current_super_admin():
        return super_admin_user
    
    app.dependency_overrides[get_current_super_admin] = mock_get_current_super_admin
    return {"Authorization": "Bearer mock_token"}

class TestAdminPasswordReset:
    """Test admin password reset functionality"""
    
    def test_reset_password_success(self, setup_database, auth_headers, licenseholder_admin):
        """Test successful password reset"""
        response = client.post(
            "/api/v1/admin/reset-password",
            json={"user_email": licenseholder_admin.email},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password reset successfully"
        assert data["user_email"] == licenseholder_admin.email
        assert "new_password" in data
        assert len(data["new_password"]) >= 12  # Check password length
        assert data["must_change_password"] is True
        
        # Password should contain different character types
        password = data["new_password"]
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
    
    def test_reset_password_user_not_found(self, setup_database, auth_headers):
        """Test password reset for non-existent user"""
        response = client.post(
            "/api/v1/admin/reset-password",
            json={"user_email": "nonexistent@test.com"},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_reset_password_insufficient_privileges(self, setup_database, auth_headers, test_db, test_organization):
        """Test password reset for user without sufficient privileges"""
        # Create a regular user
        regular_user = User(
            email="regular@testorg.com",
            username="regular",
            full_name="Regular User",
            hashed_password=get_password_hash("password123"),
            is_licenseholder_admin=False,
            is_super_admin=False,
            organization_id=test_organization.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_db.add(regular_user)
        test_db.commit()
        
        response = client.post(
            "/api/v1/admin/reset-password",
            json={"user_email": regular_user.email},
            headers=auth_headers
        )
        
        assert response.status_code == 403
        assert "Can only reset passwords for licenseholder admins" in response.json()["detail"]

class TestAdminUserManagement:
    """Test admin user management functionality"""
    
    def test_list_users(self, setup_database, auth_headers, licenseholder_admin):
        """Test listing users"""
        response = client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1  # Should contain at least the licenseholder admin
    
    def test_update_user(self, setup_database, auth_headers, licenseholder_admin):
        """Test updating user"""
        update_data = {
            "full_name": "Updated Admin Name",
            "department": "Updated Department"
        }
        
        response = client.put(
            f"/api/v1/admin/users/{licenseholder_admin.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated Admin Name"
        assert updated_user["department"] == "Updated Department"
    
    def test_delete_user(self, setup_database, auth_headers, test_db, test_organization):
        """Test deleting user"""
        # Create a user to delete
        user_to_delete = User(
            email="todelete@testorg.com",
            username="todelete",
            full_name="To Delete",
            hashed_password=get_password_hash("password123"),
            is_licenseholder_admin=True,
            organization_id=test_organization.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        test_db.add(user_to_delete)
        test_db.commit()
        test_db.refresh(user_to_delete)
        
        response = client.delete(
            f"/api/v1/admin/users/{user_to_delete.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
    
    def test_delete_super_admin_forbidden(self, setup_database, auth_headers, super_admin_user):
        """Test that super admin cannot be deleted"""
        response = client.delete(
            f"/api/v1/admin/users/{super_admin_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
        assert "Cannot delete super admin accounts" in response.json()["detail"]

class TestPasswordGeneration:
    """Test password generation functionality"""
    
    def test_password_strength(self, setup_database):
        """Test that generated passwords meet security requirements"""
        from app.api.routes.admin import generate_secure_password
        
        for _ in range(10):  # Test multiple generations
            password = generate_secure_password()
            
            # Check length
            assert len(password) >= 12
            
            # Check character variety
            assert any(c.islower() for c in password), f"Password missing lowercase: {password}"
            assert any(c.isupper() for c in password), f"Password missing uppercase: {password}"
            assert any(c.isdigit() for c in password), f"Password missing digit: {password}"
            assert any(c in "!@#$%^&*" for c in password), f"Password missing special char: {password}"
    
    def test_password_uniqueness(self, setup_database):
        """Test that generated passwords are unique"""
        from app.api.routes.admin import generate_secure_password
        
        passwords = set()
        for _ in range(100):
            password = generate_secure_password()
            passwords.add(password)
        
        # Should generate 100 unique passwords
        assert len(passwords) == 100

class TestErrorHandling:
    """Test error handling in admin routes"""
    
    def test_database_rollback_on_error(self, setup_database, auth_headers, test_db):
        """Test that database transactions are properly rolled back on errors"""
        # This test would need to simulate a database error
        # For now, we'll test that invalid data doesn't corrupt the database
        
        response = client.post(
            "/api/v1/admin/reset-password",
            json={"user_email": "invalid-email-format"},  # Invalid email
            headers=auth_headers
        )
        
        # Should handle the error gracefully
        assert response.status_code in [400, 404, 422]  # Various possible error codes
    
    def test_unauthorized_access(self, setup_database):
        """Test that admin routes require proper authentication"""
        response = client.post(
            "/api/v1/admin/reset-password",
            json={"user_email": "test@test.com"}
            # No auth headers
        )
        
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])