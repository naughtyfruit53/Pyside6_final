from fastapi import APIRouter, HTTPException
from typing import Optional, Dict
import json

router = APIRouter()

# Static pincode database for major Indian cities
# In production, this would be a proper database or external API
PINCODE_DATA = {
    "110001": {"city": "New Delhi", "state": "Delhi", "state_code": "07"},
    "110002": {"city": "New Delhi", "state": "Delhi", "state_code": "07"},
    "110003": {"city": "New Delhi", "state": "Delhi", "state_code": "07"},
    "400001": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400002": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400003": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "560001": {"city": "Bangalore", "state": "Karnataka", "state_code": "29"},
    "560002": {"city": "Bangalore", "state": "Karnataka", "state_code": "29"},
    "560003": {"city": "Bangalore", "state": "Karnataka", "state_code": "29"},
    "700001": {"city": "Kolkata", "state": "West Bengal", "state_code": "19"},
    "700002": {"city": "Kolkata", "state": "West Bengal", "state_code": "19"},
    "600001": {"city": "Chennai", "state": "Tamil Nadu", "state_code": "33"},
    "600002": {"city": "Chennai", "state": "Tamil Nadu", "state_code": "33"},
    "500001": {"city": "Hyderabad", "state": "Telangana", "state_code": "36"},
    "500002": {"city": "Hyderabad", "state": "Telangana", "state_code": "36"},
    "411001": {"city": "Pune", "state": "Maharashtra", "state_code": "27"},
    "411002": {"city": "Pune", "state": "Maharashtra", "state_code": "27"},
    "380001": {"city": "Ahmedabad", "state": "Gujarat", "state_code": "24"},
    "380002": {"city": "Ahmedabad", "state": "Gujarat", "state_code": "24"},
    "302001": {"city": "Jaipur", "state": "Rajasthan", "state_code": "08"},
    "302002": {"city": "Jaipur", "state": "Rajasthan", "state_code": "08"},
    "226001": {"city": "Lucknow", "state": "Uttar Pradesh", "state_code": "09"},
    "226002": {"city": "Lucknow", "state": "Uttar Pradesh", "state_code": "09"},
    "800001": {"city": "Patna", "state": "Bihar", "state_code": "10"},
    "800002": {"city": "Patna", "state": "Bihar", "state_code": "10"},
    "682001": {"city": "Kochi", "state": "Kerala", "state_code": "32"},
    "682002": {"city": "Kochi", "state": "Kerala", "state_code": "32"},
    "160001": {"city": "Chandigarh", "state": "Chandigarh", "state_code": "04"},
    "160002": {"city": "Chandigarh", "state": "Chandigarh", "state_code": "04"},
    "751001": {"city": "Bhubaneswar", "state": "Odisha", "state_code": "21"},
    "751002": {"city": "Bhubaneswar", "state": "Odisha", "state_code": "21"},
    "781001": {"city": "Guwahati", "state": "Assam", "state_code": "18"},
    "781002": {"city": "Guwahati", "state": "Assam", "state_code": "18"},
    "110001": {"city": "New Delhi", "state": "Delhi", "state_code": "07"},
    "121001": {"city": "Faridabad", "state": "Haryana", "state_code": "06"},
    "122001": {"city": "Gurgaon", "state": "Haryana", "state_code": "06"},
    "201001": {"city": "Ghaziabad", "state": "Uttar Pradesh", "state_code": "09"},
    "201301": {"city": "Noida", "state": "Uttar Pradesh", "state_code": "09"},
    "110048": {"city": "New Delhi", "state": "Delhi", "state_code": "07"},
    "122002": {"city": "Gurgaon", "state": "Haryana", "state_code": "06"},
    "400004": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400005": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400006": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400007": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400008": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400009": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400010": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400011": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400012": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400013": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400014": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400015": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400016": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400017": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400018": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400019": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
    "400020": {"city": "Mumbai", "state": "Maharashtra", "state_code": "27"},
}

class PincodeResponse:
    def __init__(self, city: str, state: str, state_code: str):
        self.city = city
        self.state = state
        self.state_code = state_code

@router.get("/lookup/{pin_code}")
async def lookup_pincode(pin_code: str) -> Dict[str, str]:
    """
    Lookup city, state, and state_code by PIN code
    """
    # Validate pin code format
    if not pin_code.isdigit() or len(pin_code) != 6:
        raise HTTPException(
            status_code=400,
            detail="Invalid PIN code format. PIN code must be 6 digits."
        )
    
    # Lookup in static data
    if pin_code in PINCODE_DATA:
        return PINCODE_DATA[pin_code]
    
    # If not found in static data, return error
    raise HTTPException(
        status_code=404,
        detail=f"PIN code {pin_code} not found in database. Please enter city, state manually."
    )