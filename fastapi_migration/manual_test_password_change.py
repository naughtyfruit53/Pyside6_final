"""
Manual testing script for password change functionality
This script tests the password change endpoints using direct HTTP requests
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "superadmin_test@example.com"
TEST_PASSWORD = "TempPassword123!"
NEW_PASSWORD = "NewStrongPassword123!"

def test_password_change_flow():
    """Test the complete password change flow"""
    print("🧪 Starting manual password change flow test")
    
    # Test 1: Create user login (this would normally be done through registration)
    print("\n1️⃣ Testing login with email...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login/email", json=login_data)
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"✅ Login successful, token obtained")
            
            # Test 2: Password change (mandatory scenario)
            print("\n2️⃣ Testing mandatory password change...")
            headers = {"Authorization": f"Bearer {token}"}
            password_change_data = {
                "new_password": NEW_PASSWORD
                # Note: No current_password for mandatory change
            }
            
            password_response = requests.post(
                f"{BASE_URL}/auth/password/change", 
                json=password_change_data,
                headers=headers
            )
            
            print(f"Password change response status: {password_response.status_code}")
            print(f"Password change response: {password_response.json()}")
            
            if password_response.status_code == 200:
                print("✅ Mandatory password change successful!")
                
                # Test 3: Login with new password
                print("\n3️⃣ Testing login with new password...")
                new_login_data = {
                    "email": TEST_EMAIL,
                    "password": NEW_PASSWORD
                }
                
                new_login_response = requests.post(f"{BASE_URL}/auth/login/email", json=new_login_data)
                print(f"New login response status: {new_login_response.status_code}")
                
                if new_login_response.status_code == 200:
                    print("✅ Login with new password successful!")
                    
                    # Test 4: Normal password change (with current password)
                    print("\n4️⃣ Testing normal password change...")
                    new_token = new_login_response.json().get("access_token")
                    new_headers = {"Authorization": f"Bearer {new_token}"}
                    
                    normal_password_change = {
                        "current_password": NEW_PASSWORD,
                        "new_password": "AnotherStrongPassword123!"
                    }
                    
                    normal_response = requests.post(
                        f"{BASE_URL}/auth/password/change",
                        json=normal_password_change,
                        headers=new_headers
                    )
                    
                    print(f"Normal password change status: {normal_response.status_code}")
                    print(f"Normal password change response: {normal_response.json()}")
                    
                    if normal_response.status_code == 200:
                        print("✅ Normal password change successful!")
                    else:
                        print("❌ Normal password change failed")
                else:
                    print("❌ Login with new password failed")
            else:
                print("❌ Mandatory password change failed")
                print(f"Error: {password_response.json()}")
        else:
            print(f"❌ Login failed: {login_response.json()}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the FastAPI server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_cors_headers():
    """Test CORS headers"""
    print("\n🌐 Testing CORS configuration...")
    
    try:
        response = requests.options(f"{BASE_URL}/auth/password/change", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type"
        })
        
        print(f"CORS preflight status: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
        
        if "access-control-allow-origin" in response.headers:
            print("✅ CORS headers present")
        else:
            print("⚠️ CORS headers may not be visible in this test")
    
    except Exception as e:
        print(f"CORS test error: {e}")

if __name__ == "__main__":
    print("🚀 Manual Password Change Testing")
    print("=" * 50)
    
    # Test server connectivity first
    try:
        health_response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
        if health_response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print("⚠️ Server responded but may not be healthy")
    except:
        print("❌ Server is not running. Please start it first with:")
        print("cd /path/to/fastapi_migration && uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Run tests
    test_cors_headers()
    # test_password_change_flow()  # Commented out as it requires actual user setup
    
    print("\n✅ Manual testing script completed")
    print("Note: Full flow test requires proper user setup in database")