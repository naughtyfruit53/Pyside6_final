"""
Comprehensive tests for enhanced authentication system (API v1)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from app.main import app
from app.core.database import get_db, Base
from app.models.base import Organization, User, PlatformUser
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.user import UserRole
from app.core.audit import AuditLog

# Test database URL (use SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_v1.db"

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
def test_organization(test_db):
    """Create a test organization"""
    org = Organization(
        name="Test Organization",
        subdomain="testorg",
        primary_email="admin@testorg.com",
        primary_phone="1234567890",
        address1="123 Test St",
        city="Test City",
        state="Test State",
        pin_code="123456",
        status="active"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org


@pytest.fixture
def super_admin_user(test_db):
    """Create the specific super admin user for testing"""
    user = User(
        organization_id=None,  # Super admin has no organization
        email="naughtyfruit53@gmail.com",
        username="naughtyfruit53",
        hashed_password=get_password_hash("originalpassword123"),
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
def org_admin_user(test_db, test_organization):
    """Create an organization admin user"""
    user = User(
        organization_id=test_organization.id,
        email="admin@testorg.com",
        username="orgadmin",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Org Admin",
        role=UserRole.ORG_ADMIN,
        is_super_admin=False,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def standard_user(test_db, test_organization):
    """Create a standard user"""
    user = User(
        organization_id=test_organization.id,
        email="user@testorg.com",
        username="standarduser",
        hashed_password=get_password_hash("userpassword123"),
        full_name="Standard User",
        role=UserRole.STANDARD_USER,
        is_super_admin=False,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def platform_user(test_db):
    """Create a platform user"""
    user = PlatformUser(
        email="platform@example.com",
        hashed_password=get_password_hash("platformpassword123"),
        full_name="Platform Admin",
        role="super_admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestAuthenticationV1:
    """Test cases for v1 authentication endpoints"""
    
    def test_login_oauth_form_super_admin(self, client, super_admin_user):
        """Test OAuth2 form login for super admin"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "naughtyfruit53@gmail.com",
                "password": "originalpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_role"] == UserRole.SUPER_ADMIN
        assert data["organization_id"] is None
        assert not data["must_change_password"]
        assert not data["force_password_reset"]
    
    def test_login_email_org_admin(self, client, org_admin_user):
        """Test email login for organization admin"""
        response = client.post(
            "/api/v1/auth/login/email",
            json={
                "email": "admin@testorg.com",
                "password": "adminpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_role"] == UserRole.ORG_ADMIN
        assert data["organization_id"] is not None
        assert data["organization_name"] == "Test Organization"
    
    def test_master_password_login(self, client, super_admin_user):
        """Test master password login"""
        response = client.post(
            "/api/v1/auth/master-password/login",
            json={
                "email": "naughtyfruit53@gmail.com",
                "master_password": "Qweasdzxc"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["force_password_reset"] is True
        assert "You must change your password immediately" in data["message"]
    
    def test_master_password_login_wrong_user(self, client, org_admin_user):
        """Test master password login with non-super admin"""
        response = client.post(
            "/api/v1/auth/master-password/login",
            json={
                "email": "admin@testorg.com",
                "master_password": "Qweasdzxc"
            }
        )
        
        assert response.status_code == 403
        assert "Master password access is restricted" in response.json()["detail"]
    
    def test_login_with_username(self, client, standard_user):
        """Test login with username instead of email"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "standarduser",
                "password": "userpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_role"] == UserRole.STANDARD_USER
    
    def test_login_invalid_credentials(self, client, standard_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email/username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, test_db, standard_user):
        """Test login with inactive user"""
        # Deactivate user
        standard_user.is_active = False
        test_db.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        
        assert response.status_code == 401
        assert "User account is inactive" in response.json()["detail"]
    
    def test_password_change(self, client, standard_user):
        """Test password change"""
        # Get access token first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "userpassword123",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
        
        # Test login with new password
        new_login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "newpassword123"
            }
        )
        assert new_login_response.status_code == 200
    
    def test_password_change_wrong_current(self, client, standard_user):
        """Test password change with wrong current password"""
        # Get access token first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to change password with wrong current password
        response = client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
    
    def test_logout(self, client, standard_user):
        """Test logout endpoint"""
        # Get access token first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_token_validation(self, client, standard_user):
        """Test token validation endpoint"""
        # Get access token first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Test token
        response = client.post(
            "/api/v1/auth/test-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@testorg.com"
        assert data["role"] == UserRole.STANDARD_USER


class TestAuditLogging:
    """Test cases for audit logging functionality"""
    
    def test_login_audit_logging(self, client, test_db, standard_user):
        """Test that login attempts are properly audited"""
        # Successful login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        assert response.status_code == 200
        
        # Check audit log
        audit_logs = test_db.query(AuditLog).filter(
            AuditLog.event_type == "LOGIN",
            AuditLog.user_email == "user@testorg.com"
        ).all()
        
        assert len(audit_logs) >= 1
        log = audit_logs[-1]  # Get latest
        assert log.action == "LOGIN_ATTEMPT"
        assert log.success == "SUCCESS"
        assert log.user_id == standard_user.id
    
    def test_failed_login_audit_logging(self, client, test_db, standard_user):
        """Test that failed login attempts are properly audited"""
        # Failed login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        
        # Check audit log
        audit_logs = test_db.query(AuditLog).filter(
            AuditLog.event_type == "LOGIN",
            AuditLog.user_email == "user@testorg.com",
            AuditLog.success == "FAILED"
        ).all()
        
        assert len(audit_logs) >= 1
        log = audit_logs[-1]  # Get latest
        assert log.action == "LOGIN_ATTEMPT"
        assert log.error_message is not None
    
    def test_master_password_audit_logging(self, client, test_db, super_admin_user):
        """Test that master password usage is properly audited"""
        response = client.post(
            "/api/v1/auth/master-password/login",
            json={
                "email": "naughtyfruit53@gmail.com",
                "master_password": "Qweasdzxc"
            }
        )
        assert response.status_code == 200
        
        # Check audit log for master password usage
        audit_logs = test_db.query(AuditLog).filter(
            AuditLog.event_type == "SECURITY",
            AuditLog.action == "MASTER_PASSWORD_USED",
            AuditLog.user_email == "naughtyfruit53@gmail.com"
        ).all()
        
        assert len(audit_logs) >= 1
        log = audit_logs[-1]
        assert log.success == "SUCCESS"
        assert log.user_role == "super_admin"
    
    def test_password_change_audit_logging(self, client, test_db, standard_user):
        """Test that password changes are properly audited"""
        # Get access token first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "userpassword123",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Check audit log
        audit_logs = test_db.query(AuditLog).filter(
            AuditLog.event_type == "PASSWORD_RESET",
            AuditLog.user_email == "user@testorg.com"
        ).all()
        
        assert len(audit_logs) >= 1
        log = audit_logs[-1]
        assert log.action == "ADMIN_PASSWORD_RESET"
        assert log.success == "SUCCESS"
        assert "SELF_PASSWORD_CHANGE" in str(log.details)


class TestTemporaryPassword:
    """Test cases for temporary password functionality"""
    
    def test_temporary_password_authentication(self, client, test_db, standard_user):
        """Test authentication with temporary password"""
        from app.services.user_service import UserService
        
        # Set temporary password
        temp_password = "temppass123"
        UserService.set_temporary_password(
            db=test_db,
            user=standard_user,
            temp_password=temp_password,
            expires_hours=24
        )
        
        # Try to login with temporary password
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": temp_password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["force_password_reset"] is True
    
    def test_expired_temporary_password(self, client, test_db, standard_user):
        """Test authentication with expired temporary password"""
        from app.services.user_service import UserService
        
        # Set expired temporary password
        temp_password = "temppass123"
        standard_user.temp_password_hash = get_password_hash(temp_password)
        standard_user.temp_password_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        test_db.commit()
        
        # Try to login with expired temporary password
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": temp_password
            }
        )
        
        assert response.status_code == 401


class TestRobustUserLookup:
    """Test cases for robust user lookup functionality"""
    
    def test_email_lookup_with_organization_context(self, client, org_admin_user):
        """Test user lookup prioritizes organization context"""
        response = client.post(
            "/api/v1/auth/login/email",
            json={
                "email": "admin@testorg.com",
                "password": "adminpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "Test Organization"
    
    def test_username_fallback_lookup(self, client, standard_user):
        """Test that system falls back to username if email not found"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "standarduser",  # Using username instead of email
                "password": "userpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_role"] == UserRole.STANDARD_USER
    
    def test_super_admin_organization_handling(self, client, super_admin_user):
        """Test that super admin login works without organization context"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "naughtyfruit53@gmail.com",
                "password": "originalpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] is None
        assert data["user_role"] == UserRole.SUPER_ADMIN


class TestFailedLoginAttempts:
    """Test cases for failed login attempt handling"""
    
    def test_failed_login_counter_increment(self, client, test_db, standard_user):
        """Test that failed login attempts are tracked"""
        initial_attempts = standard_user.failed_login_attempts or 0
        
        # Make a failed login attempt
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        
        # Refresh user from database
        test_db.refresh(standard_user)
        assert standard_user.failed_login_attempts == initial_attempts + 1
    
    def test_successful_login_resets_counter(self, client, test_db, standard_user):
        """Test that successful login resets failed attempt counter"""
        # Set some failed attempts
        standard_user.failed_login_attempts = 3
        test_db.commit()
        
        # Make successful login
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@testorg.com",
                "password": "userpassword123"
            }
        )
        assert response.status_code == 200
        
        # Check that counter is reset
        test_db.refresh(standard_user)
        assert standard_user.failed_login_attempts == 0