"""
Comprehensive tests for platform user functionality and multi-tenancy separation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal
from app.models.base import PlatformUser, User, Organization
from app.core.security import get_password_hash
from app.schemas.base import PlatformUserRole, UserRole

client = TestClient(app)

class TestPlatformUserMultiTenancy:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data for each test"""
        self.db = SessionLocal()
        
        # Clean up any existing test data
        self.db.query(PlatformUser).filter(PlatformUser.email.like("%test%")).delete()
        self.db.query(User).filter(User.email.like("%test%")).delete()
        self.db.query(Organization).filter(Organization.name.like("%Test%")).delete()
        self.db.commit()
        
        # Create test organization
        self.test_org = Organization(
            name="Test Organization",
            subdomain="testorg",
            status="active",
            primary_email="admin@testorg.com",
            primary_phone="+1234567890",
            address1="123 Test St",
            city="Test City",
            state="Test State",
            pin_code="12345",
            country="Test Country",
            max_users=10
        )
        self.db.add(self.test_org)
        self.db.commit()
        self.db.refresh(self.test_org)
        
        # Create test platform user
        self.platform_user = PlatformUser(
            email="platform@test.com",
            full_name="Platform Test User",
            hashed_password=get_password_hash("testpass123"),
            role=PlatformUserRole.SUPER_ADMIN,
            is_active=True
        )
        self.db.add(self.platform_user)
        
        # Create test organization user
        self.org_user = User(
            organization_id=self.test_org.id,
            email="orguser@test.com",
            username="orguser",
            full_name="Org Test User",
            hashed_password=get_password_hash("testpass123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        self.db.add(self.org_user)
        
        self.db.commit()
        self.db.refresh(self.platform_user)
        self.db.refresh(self.org_user)
        
        yield
        
        # Cleanup
        self.db.query(PlatformUser).filter(PlatformUser.email.like("%test%")).delete()
        self.db.query(User).filter(User.email.like("%test%")).delete()
        self.db.query(Organization).filter(Organization.name.like("%Test%")).delete()
        self.db.commit()
        self.db.close()
    
    def test_platform_user_login_success(self):
        """Test platform user can login successfully"""
        login_data = {
            "email": "platform@test.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/platform/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["user_role"] == "super_admin"
        assert token_data["user_type"] == "platform"
    
    def test_platform_user_cannot_login_via_org_endpoint(self):
        """Test platform user cannot login via organization login endpoint"""
        login_data = {
            "email": "platform@test.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/auth/login/email", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_org_user_cannot_login_via_platform_endpoint(self):
        """Test organization user cannot login via platform login endpoint"""
        login_data = {
            "email": "orguser@test.com",
            "password": "testpass123"
        }
        
        response = client.post("/api/v1/platform/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_org_user_login_success(self):
        """Test organization user can login successfully via organization endpoint"""
        login_data = {
            "email": "orguser@test.com",
            "password": "testpass123",
            "subdomain": "testorg"
        }
        
        response = client.post("/api/v1/auth/login/email", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["organization_id"] == self.test_org.id
        assert token_data["user_role"] == "admin"
    
    def test_platform_token_access_platform_endpoints(self):
        """Test platform token can access platform endpoints"""
        # Login as platform user
        login_data = {
            "email": "platform@test.com",
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/platform/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access platform user info
        response = client.get("/api/v1/platform/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == "platform@test.com"
        assert user_data["role"] == "super_admin"
    
    def test_org_token_cannot_access_platform_endpoints(self):
        """Test organization token cannot access platform endpoints"""
        # Login as organization user
        login_data = {
            "email": "orguser@test.com",
            "password": "testpass123",
            "subdomain": "testorg"
        }
        
        login_response = client.post("/api/v1/auth/login/email", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access platform endpoints
        response = client.get("/api/v1/platform/me", headers=headers)
        assert response.status_code == 401
    
    def test_platform_token_access_organization_endpoints(self):
        """Test platform token can access organization endpoints (as super admin)"""
        # Login as platform user
        login_data = {
            "email": "platform@test.com",
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/platform/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access organization endpoints (should work for super admin)
        response = client.get("/api/v1/organizations/", headers=headers)
        assert response.status_code == 200
    
    def test_platform_user_creation_by_super_admin(self):
        """Test platform super admin can create new platform users"""
        # Login as platform super admin
        login_data = {
            "email": "platform@test.com",
            "password": "testpass123"
        }
        
        login_response = client.post("/api/v1/platform/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create new platform user
        new_user_data = {
            "email": "newplatform@test.com",
            "full_name": "New Platform User",
            "password": "newpass123",
            "role": "platform_admin",
            "is_active": True
        }
        
        response = client.post("/api/v1/platform/create", json=new_user_data, headers=headers)
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user["email"] == "newplatform@test.com"
        assert created_user["role"] == "platform_admin"
        assert created_user["is_active"] is True
    
    def test_token_distinction_in_jwt(self):
        """Test that JWT tokens contain proper user_type distinction"""
        from app.core.security import verify_token
        
        # Get platform token
        platform_login = client.post("/api/v1/platform/login", json={
            "email": "platform@test.com",
            "password": "testpass123"
        })
        platform_token = platform_login.json()["access_token"]
        
        # Get organization token
        org_login = client.post("/api/v1/auth/login/email", json={
            "email": "orguser@test.com",
            "password": "testpass123",
            "subdomain": "testorg"
        })
        org_token = org_login.json()["access_token"]
        
        # Verify tokens contain correct user_type
        platform_email, platform_org_id, platform_user_type = verify_token(platform_token)
        assert platform_email == "platform@test.com"
        assert platform_org_id is None
        assert platform_user_type == "platform"
        
        org_email, org_org_id, org_user_type = verify_token(org_token)
        assert org_email == "orguser@test.com"
        assert org_org_id == self.test_org.id
        assert org_user_type == "organization"

if __name__ == "__main__":
    test_platform = TestPlatformUserMultiTenancy()
    # Note: Running these manually won't work without proper pytest setup
    # Run with: python -m pytest test_platform_comprehensive.py -v
    print("Run with: python -m pytest test_platform_comprehensive.py -v")