# Manual Testing with curl/Postman

This document provides examples for testing the password change functionality manually using curl or Postman.

## Prerequisites

1. Start the FastAPI server:
```bash
cd /path/to/fastapi_migration
uvicorn app.main:app --reload
```

2. The server should be running on `http://localhost:8000`

## Test Scenarios

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 2. Super Admin Mandatory Password Change

**Step 1: Login as super admin with must_change_password=True**
```bash
curl -X POST http://localhost:8000/api/auth/login/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@example.com",
    "password": "initial_temp_password"
  }'
```

**Step 2: Change password without current password (mandatory scenario)**
```bash
curl -X POST http://localhost:8000/api/auth/password/change \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "new_password": "NewStrongPassword123!"
  }'
```

Expected response:
```json
{"message": "Password changed successfully"}
```

### 3. Normal User Password Change

**Step 1: Login as normal user**
```bash
curl -X POST http://localhost:8000/api/auth/login/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "normaluser@example.com",
    "password": "current_password"
  }'
```

**Step 2: Try to change password without current password (should fail)**
```bash
curl -X POST http://localhost:8000/api/auth/password/change \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "new_password": "NewStrongPassword123!"
  }'
```

Expected response (error):
```json
{"detail": "Current password is required"}
```

**Step 3: Change password with current password (should succeed)**
```bash
curl -X POST http://localhost:8000/api/auth/password/change \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "current_password": "current_password",
    "new_password": "NewStrongPassword123!"
  }'
```

Expected response:
```json
{"message": "Password changed successfully"}
```

### 4. CORS Testing

```bash
curl -X OPTIONS http://localhost:8000/api/auth/password/change \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization, Content-Type" \
  -v
```

Look for CORS headers in the response:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`

### 5. Error Scenarios

**Weak password validation:**
```bash
curl -X POST http://localhost:8000/api/auth/password/change \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "current_password": "current_password",
    "new_password": "weak"
  }'
```

Expected response (422 Validation Error):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "new_password"],
      "msg": "Value error, Password must be at least 8 characters long",
      "input": "weak",
      "ctx": {"error": {}}
    }
  ]
}
```

## Postman Collection

If using Postman, create requests with these configurations:

1. **Health Check**
   - Method: GET
   - URL: `http://localhost:8000/health`

2. **Login**
   - Method: POST
   - URL: `http://localhost:8000/api/auth/login/email`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON): `{"email": "user@example.com", "password": "password"}`

3. **Password Change**
   - Method: POST
   - URL: `http://localhost:8000/api/auth/password/change`
   - Headers: 
     - `Content-Type: application/json`
     - `Authorization: Bearer {{token}}`
   - Body (raw JSON): `{"current_password": "old", "new_password": "NewStrongPassword123!"}`

## Log Monitoring

While testing, monitor the server logs for the enhanced logging output:

- 🔐 Password change requests
- ✅ Successful operations
- ❌ Failed operations
- 🔍 User and request details
- 🎉 Completion confirmations

## Security Notes

- Always use strong passwords in testing (8+ chars, uppercase, lowercase, number, special char)
- The `current_password` field is optional only when `must_change_password=True`
- All password change attempts are logged for audit purposes
- Invalid tokens will result in 401 Unauthorized responses