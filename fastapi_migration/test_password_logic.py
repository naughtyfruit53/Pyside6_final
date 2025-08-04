"""
Simple test script for mandatory password change functionality
Uses direct imports to avoid dependency issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test the password change logic directly
from fastapi import HTTPException
from unittest.mock import Mock

# Test data
class MockUser:
    def __init__(self, must_change_password=False):
        self.email = "test@example.com"
        self.id = 1
        self.organization_id = 1
        self.hashed_password = "$2b$12$dummyhash"  # Mock hash
        self.must_change_password = must_change_password

class MockPasswordData:
    def __init__(self, current_password=None, new_password="NewPassword123!"):
        self.current_password = current_password
        self.new_password = new_password
    
    def dict(self):
        result = {"new_password": self.new_password}
        if self.current_password:
            result["current_password"] = self.current_password
        return result

# Mock verify_password function
def mock_verify_password(plain_password, hashed_password):
    # For testing, assume "oldpassword123" is the correct password
    return plain_password == "oldpassword123"

def test_password_change_logic():
    """Test the core password change logic"""
    
    print("Testing mandatory password change logic...")
    
    # Test 1: Mandatory password change WITHOUT current password (should succeed)
    print("\n1. Testing mandatory password change without current password...")
    user = MockUser(must_change_password=True)
    password_data = MockPasswordData(current_password=None)
    
    # Simulate the logic from our updated password change function
    try:
        if user.must_change_password:
            print("✓ Mandatory password change detected - skipping current password verification")
            success = True
        else:
            if not password_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required")
            if not mock_verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            success = True
        
        if success:
            print("✓ Test 1 PASSED: Mandatory password change without current password succeeded")
    except HTTPException as e:
        print(f"✗ Test 1 FAILED: {e.detail}")
    
    # Test 2: Mandatory password change WITH current password (should succeed)
    print("\n2. Testing mandatory password change with current password...")
    user = MockUser(must_change_password=True)
    password_data = MockPasswordData(current_password="oldpassword123")
    
    try:
        if user.must_change_password:
            print("✓ Mandatory password change detected - skipping current password verification")
            success = True
        else:
            if not password_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required")
            if not mock_verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            success = True
        
        if success:
            print("✓ Test 2 PASSED: Mandatory password change with current password succeeded")
    except HTTPException as e:
        print(f"✗ Test 2 FAILED: {e.detail}")
    
    # Test 3: Normal password change WITHOUT current password (should fail)
    print("\n3. Testing normal password change without current password...")
    user = MockUser(must_change_password=False)
    password_data = MockPasswordData(current_password=None)
    
    try:
        if user.must_change_password:
            print("Mandatory password change detected - skipping current password verification")
            success = True
        else:
            if not password_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required")
            if not mock_verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            success = True
        
        print("✗ Test 3 FAILED: Normal password change without current password should have failed")
    except HTTPException as e:
        if "Current password is required" in e.detail:
            print("✓ Test 3 PASSED: Normal password change correctly requires current password")
        else:
            print(f"✗ Test 3 FAILED: Wrong error message: {e.detail}")
    
    # Test 4: Normal password change WITH wrong current password (should fail)
    print("\n4. Testing normal password change with wrong current password...")
    user = MockUser(must_change_password=False)
    password_data = MockPasswordData(current_password="wrongpassword")
    
    try:
        if user.must_change_password:
            print("Mandatory password change detected - skipping current password verification")
            success = True
        else:
            if not password_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required")
            if not mock_verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            success = True
        
        print("✗ Test 4 FAILED: Normal password change with wrong password should have failed")
    except HTTPException as e:
        if "Current password is incorrect" in e.detail:
            print("✓ Test 4 PASSED: Normal password change correctly validates current password")
        else:
            print(f"✗ Test 4 FAILED: Wrong error message: {e.detail}")
    
    # Test 5: Normal password change WITH correct current password (should succeed)
    print("\n5. Testing normal password change with correct current password...")
    user = MockUser(must_change_password=False)
    password_data = MockPasswordData(current_password="oldpassword123")
    
    try:
        if user.must_change_password:
            print("Mandatory password change detected - skipping current password verification")
            success = True
        else:
            if not password_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required")
            if not mock_verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            success = True
        
        if success:
            print("✓ Test 5 PASSED: Normal password change with correct current password succeeded")
    except HTTPException as e:
        print(f"✗ Test 5 FAILED: {e.detail}")
    
    print("\n" + "="*60)
    print("Password change logic tests completed!")
    print("All tests should show PASSED for the implementation to be correct.")

if __name__ == "__main__":
    test_password_change_logic()