"""
Test platform user authentication
"""

import pytest
import requests
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.base import PlatformUser
from app.core.security import get_password_hash
from app.schemas.base import PlatformUserRole

client = TestClient(app)

class TestPlatformAuth:
    
    def test_platform_login_success(self):
        """Test successful platform user login"""
        # Ensure platform user exists (created by previous script)
        login_data = {
            "email": "naughtyfruit53@gmail.com",
            "password": "123456"
        }
        
        response = client.post("/api/v1/platform/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["user_role"] == "super_admin"
        assert token_data["user_type"] == "platform"
    
    def test_platform_login_invalid_credentials(self):
        """Test platform login with invalid credentials"""
        login_data = {
            "email": "naughtyfruit53@gmail.com",
            "password": "wrong_password"
        }
        
        response = client.post("/api/v1/platform/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_platform_login_nonexistent_user(self):
        """Test platform login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/platform/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_platform_user_info(self):
        """Test getting platform user info with valid token"""
        # First login to get token
        login_data = {
            "email": "naughtyfruit53@gmail.com",
            "password": "123456"
        }
        
        login_response = client.post("/api/v1/platform/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Use token to get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/platform/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "naughtyfruit53@gmail.com"
        assert user_data["role"] == "super_admin"
        assert user_data["is_active"] is True
    
    def test_platform_logout(self):
        """Test platform logout"""
        response = client.post("/api/v1/platform/logout")
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]

if __name__ == "__main__":
    test_platform = TestPlatformAuth()
    test_platform.test_platform_login_success()
    test_platform.test_platform_login_invalid_credentials()
    test_platform.test_platform_login_nonexistent_user()
    test_platform.test_platform_user_info()
    test_platform.test_platform_logout()
    print("All platform authentication tests passed!")