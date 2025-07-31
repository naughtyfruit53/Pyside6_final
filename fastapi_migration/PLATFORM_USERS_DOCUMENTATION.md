# Platform Users and Multi-Tenancy Architecture

## Overview

This document describes the implementation of platform users and the multi-tenant architecture that separates platform-level (SaaS) users from organization-specific users.

## Architecture Components

### 1. Platform Users Table (`platform_users`)

A dedicated table for SaaS platform-level users who manage the system at a global level.

**Fields:**
- `id` - Primary key
- `email` - Unique email address
- `hashed_password` - Bcrypt hashed password
- `full_name` - Full name of the platform user
- `role` - Platform role (`super_admin`, `platform_admin`)
- `is_active` - Account status
- `created_at`, `updated_at`, `last_login` - Metadata

**Roles:**
- `super_admin` - Full platform access, can manage organizations and platform users
- `platform_admin` - Limited platform access

### 2. Organization Users Table (`users`)

Organization-specific users who work within a specific tenant/organization.

**Key Changes:**
- `organization_id` - Foreign key to organizations table (will be non-nullable after migration)
- Removed platform-level users from this table
- All users in this table belong to an organization

### 3. Authentication Separation

#### Platform Authentication
- **Endpoint:** `/api/v1/platform/login`
- **Token Type:** Contains `user_type: "platform"` and `organization_id: null`
- **Access:** Platform-level endpoints and cross-organization operations

#### Organization Authentication  
- **Endpoint:** `/api/v1/auth/login/email`
- **Token Type:** Contains `user_type: "organization"` and specific `organization_id`
- **Access:** Organization-scoped endpoints and data

## API Endpoints

### Platform Endpoints (`/api/v1/platform/`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/login` | Platform user login | None |
| GET | `/me` | Get current platform user info | Platform Token |
| POST | `/create` | Create new platform user | Super Admin |
| POST | `/logout` | Platform logout | None |

### Organization Endpoints (existing)

All existing endpoints under `/api/v1/` are organization-scoped and require organization authentication.

## JWT Token Structure

### Platform Token
```json
{
  "exp": 1234567890,
  "sub": "platform@example.com",
  "user_type": "platform",
  "organization_id": null
}
```

### Organization Token
```json
{
  "exp": 1234567890,
  "sub": "user@organization.com", 
  "user_type": "organization",
  "organization_id": 123
}
```

## Migration Process

### Automatic Migration

The migration `005_platform_users` automatically:

1. Creates the `platform_users` table
2. Identifies existing super admin users (where `organization_id IS NULL` and `is_super_admin = 1`)
3. Migrates them to the `platform_users` table
4. Removes them from the `users` table

### Manual Steps Required

After migration, administrators should:

1. Update any hardcoded super admin credentials to use platform login
2. Test platform authentication with existing super admin accounts  
3. Create additional platform users as needed

## Usage Examples

### Platform User Login

```python
import requests

# Platform user login
response = requests.post("http://localhost:8000/api/v1/platform/login", json={
    "email": "platform@example.com",
    "password": "secure_password"
})

token_data = response.json()
platform_token = token_data["access_token"]

# Access platform endpoints
headers = {"Authorization": f"Bearer {platform_token}"}
user_info = requests.get("http://localhost:8000/api/v1/platform/me", headers=headers)
```

### Organization User Login

```python
# Organization user login
response = requests.post("http://localhost:8000/api/v1/auth/login/email", json={
    "email": "user@organization.com",
    "password": "secure_password",
    "subdomain": "organization_subdomain"
})

token_data = response.json()
org_token = token_data["access_token"]
org_id = token_data["organization_id"]

# Access organization endpoints
headers = {"Authorization": f"Bearer {org_token}"}
products = requests.get("http://localhost:8000/api/v1/products/", headers=headers)
```

## Security Considerations

### Token Validation

- Platform tokens are validated to ensure `user_type == "platform"`
- Organization tokens are validated to ensure `user_type == "organization"`
- Cross-contamination is prevented by token type checking

### Permission Isolation

- Platform users cannot accidentally access organization-specific data without explicit cross-tenant permissions
- Organization users cannot access platform-level functionality
- Super admins retain cross-organization access for management purposes

### Password Security

- All passwords use bcrypt hashing
- Platform and organization users have separate credential stores
- Password policies apply to both user types

## Development Guidelines

### Creating Platform Endpoints

```python
from app.api.platform import get_current_platform_super_admin

@router.post("/admin-function")
async def platform_admin_function(
    current_platform_user: PlatformUser = Depends(get_current_platform_super_admin)
):
    # Platform admin logic here
    pass
```

### Creating Organization Endpoints

```python
from app.api.auth import get_current_active_user, require_current_organization_id

@router.get("/organization-data")
async def get_organization_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    org_id = require_current_organization_id()
    # Organization-scoped logic here
    pass
```

## Testing

### Platform User Tests

```python
def test_platform_login():
    response = client.post("/api/v1/platform/login", json={
        "email": "platform@test.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert response.json()["user_type"] == "platform"
```

### Multi-Tenant Isolation Tests

```python
def test_token_isolation():
    # Platform token cannot access org endpoints
    platform_token = get_platform_token()
    response = client.get("/api/v1/products/", headers={
        "Authorization": f"Bearer {platform_token}"
    })
    # Should either require org context or fail
```

## Future Enhancements

### Planned Features

1. **Organization ID Constraint:** Make `users.organization_id` non-nullable
2. **Platform User Management UI:** Admin interface for platform users
3. **Cross-Tenant Analytics:** Platform-level reporting across organizations
4. **Platform User Permissions:** More granular platform role permissions

### Scalability Benefits

- **Horizontal Scaling:** Organization data can be partitioned
- **Feature Isolation:** Platform features independent of organization features  
- **Security Boundaries:** Clear separation of concerns
- **SaaS Ready:** Foundation for multi-tenant SaaS deployment

## Troubleshooting

### Common Issues

1. **Token Type Mismatch:** Ensure correct login endpoint for user type
2. **Organization Context Missing:** Organization users need valid organization_id
3. **Permission Denied:** Check user role and authentication type
4. **Migration Issues:** Verify database schema is up to date

### Debug Steps

1. Verify token contents using `verify_token()` function
2. Check user exists in correct table (platform_users vs users)
3. Validate organization exists and is active
4. Confirm endpoint requires correct authentication type

For additional support, check the test files:
- `test_platform_auth.py` - Basic platform authentication tests
- `test_platform_comprehensive.py` - Full multi-tenant scenario tests