import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pincode_lookup_valid():
    """Test pincode lookup with valid PIN code"""
    # Test with Mumbai PIN code
    response = client.get("/api/v1/pincode/lookup/400001")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Mumbai"
    assert data["state"] == "Maharashtra"
    assert data["state_code"] == "27"

def test_pincode_lookup_delhi():
    """Test pincode lookup with Delhi PIN code"""
    # Test with Delhi PIN code
    response = client.get("/api/v1/pincode/lookup/110001")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "New Delhi"
    assert data["state"] == "Delhi"
    assert data["state_code"] == "07"

def test_pincode_lookup_bangalore():
    """Test pincode lookup with Bangalore PIN code"""
    # Test with Bangalore PIN code
    response = client.get("/api/v1/pincode/lookup/560001")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Bangalore"
    assert data["state"] == "Karnataka"
    assert data["state_code"] == "29"

def test_pincode_lookup_invalid_format():
    """Test pincode lookup with invalid format"""
    # Test with invalid PIN code (less than 6 digits)
    response = client.get("/api/v1/pincode/lookup/12345")
    assert response.status_code == 400
    assert "Invalid PIN code format" in response.json()["detail"]
    
    # Test with non-numeric PIN code
    response = client.get("/api/v1/pincode/lookup/abcdef")
    assert response.status_code == 400
    assert "Invalid PIN code format" in response.json()["detail"]

def test_pincode_lookup_not_found():
    """Test pincode lookup with PIN code not in database"""
    # Test with PIN code not in our static database
    response = client.get("/api/v1/pincode/lookup/999999")
    assert response.status_code == 404
    assert "not found in database" in response.json()["detail"]

def test_pincode_auto_fill_workflow():
    """Test the complete pincode auto-fill workflow"""
    # This tests the expected workflow:
    # 1. User enters PIN code
    # 2. System looks up city/state/state_code
    # 3. Form fields are auto-populated
    
    test_cases = [
        {"pin_code": "400001", "expected": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"}},
        {"pin_code": "110001", "expected": {"city": "New Delhi", "state": "Delhi", "state_code": "07"}},
        {"pin_code": "560001", "expected": {"city": "Bangalore", "state": "Karnataka", "state_code": "29"}},
        {"pin_code": "600001", "expected": {"city": "Chennai", "state": "Tamil Nadu", "state_code": "33"}},
        {"pin_code": "500001", "expected": {"city": "Hyderabad", "state": "Telangana", "state_code": "36"}},
    ]
    
    for case in test_cases:
        response = client.get(f"/api/v1/pincode/lookup/{case['pin_code']}")
        assert response.status_code == 200
        data = response.json()
        expected = case["expected"]
        assert data["city"] == expected["city"]
        assert data["state"] == expected["state"]
        assert data["state_code"] == expected["state_code"]
        print(f"✅ PIN {case['pin_code']} -> {data['city']}, {data['state']} ({data['state_code']})")

if __name__ == "__main__":
    test_pincode_lookup_valid()
    test_pincode_lookup_delhi()
    test_pincode_lookup_bangalore()
    test_pincode_lookup_invalid_format()
    test_pincode_lookup_not_found()
    test_pincode_auto_fill_workflow()
    print("✅ All pincode lookup tests passed!")