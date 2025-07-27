# Multi-Tenant Architecture Documentation

## Overview

This FastAPI application implements a comprehensive multi-tenant architecture that provides complete data isolation between organizations while maintaining a single application instance. Each tenant (organization) has their own isolated data space with proper security controls and feature management.

## Core Components

### 1. Database Schema

#### Organization Model
The `Organization` model is the core of the multi-tenant architecture:

```python
class Organization(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    subdomain = Column(String, unique=True, nullable=False)
    status = Column(String, default="active")  # active, suspended, trial
    plan_type = Column(String, default="trial")  # trial, basic, premium, enterprise
    max_users = Column(Integer, default=5)
    storage_limit_gb = Column(Integer, default=1)
    # ... other fields
```

#### Multi-Tenant Models
All tenant-specific models include an `organization_id` foreign key:

```python
class User(Base):
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    # ... other fields

class Vendor(Base):
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    # ... other fields
```

### 2. Tenant Context Management

#### TenantContext
The `TenantContext` class manages tenant isolation throughout the application:

```python
from app.core.tenant import TenantContext

# Get current organization ID
org_id = TenantContext.get_organization_id()

# Set organization context
TenantContext.set_organization_id(org_id)
```

#### TenantMiddleware
Automatically extracts and sets tenant context from requests:
- Subdomain-based identification (`acme.yourdomain.com`)
- Header-based identification (`X-Organization-ID`)
- Path-based identification (`/api/v1/org/{org_id}/...`)

### 3. Authentication & Authorization

#### JWT Token Structure
```json
{
  "sub": "user@example.com",
  "organization_id": 123,
  "exp": 1234567890
}
```

#### Role-Based Access Control (RBAC)
- **Super Admin**: System-wide access, can manage organizations
- **Organization Admin**: Full access within their organization
- **Admin**: Limited admin access within their organization
- **Standard User**: Basic access within their organization

#### Authentication Dependencies
```python
from app.api.auth import get_current_user, get_current_admin_user, get_current_super_admin

@router.get("/admin-only")
async def admin_endpoint(current_user: User = Depends(get_current_admin_user)):
    # Only admin users can access this endpoint
    pass
```

### 4. Data Isolation

#### Query Filtering
The `TenantQueryMixin` ensures all queries are filtered by organization:

```python
from app.core.tenant import TenantQueryMixin

# Automatically filter by current tenant
query = db.query(Vendor)
filtered_query = TenantQueryMixin.filter_by_tenant(query, Vendor)

# Ensure access to specific object
TenantQueryMixin.ensure_tenant_access(vendor_object, org_id)
```

#### Automatic Tenant Assignment
When creating new records, the organization_id is automatically set:

```python
new_vendor = Vendor(
    organization_id=require_current_organization_id(),
    name="New Vendor",
    # ... other fields
)
```

## API Structure

### Organization Management
- `POST /api/v1/organizations/` - Create organization (Super admin only)
- `GET /api/v1/organizations/` - List organizations (Super admin only)
- `GET /api/v1/organizations/current` - Get current organization
- `PUT /api/v1/organizations/{id}` - Update organization
- `DELETE /api/v1/organizations/{id}` - Delete organization (Super admin only)

### User Management
- `POST /api/v1/users/` - Create user (Admin only)
- `GET /api/v1/users/` - List users in organization
- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (Admin only)

### Authentication
- `POST /api/v1/auth/login` - Login with username/email
- `POST /api/v1/auth/login/email` - Login with email
- `POST /api/v1/auth/test-token` - Validate token

## Security Features

### Data Isolation
- Every query is automatically filtered by organization_id
- Cross-tenant data access is prevented at the database level
- API responses only include data from the user's organization

### Audit Logging
All operations are logged with tenant context:

```python
from app.services.security_service import SecurityService

SecurityService.log_audit_event(
    db=db,
    table_name="vendors",
    record_id=vendor.id,
    action="CREATE",
    user_id=current_user.id,
    changes=vendor_data,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent")
)
```

### Input Validation & Sanitization
```python
from app.services.security_service import SecurityService

# Validate and sanitize input data
allowed_fields = {"name", "email", "phone"}
validated_data = SecurityService.validate_input_data(input_data, allowed_fields)
```

### Rate Limiting
```python
# Check rate limits for sensitive operations
is_allowed, remaining = SecurityService.check_rate_limit(
    db=db,
    user_id=user.id,
    action="LOGIN_ATTEMPT",
    max_attempts=5,
    window_minutes=15
)
```

## Configuration Management

### Plan-Based Features
Different organization plans have different feature sets:

```python
from app.core.tenant_config import TenantConfig

# Check if organization has a feature
if TenantConfig.has_feature(org.plan_type, "advanced_reporting"):
    # Enable advanced reporting
    pass

# Get plan limits
max_users = TenantConfig.get_limit(org.plan_type, "max_users")
```

### Environment Configuration
```python
from app.core.tenant_config import EnvironmentConfig

if EnvironmentConfig.is_production():
    # Production-specific logic
    pass
```

## Database Migration

Run the migration script to set up the multi-tenant database:

```bash
cd fastapi_migration
python migrate.py
```

This will:
1. Create all necessary tables
2. Set up a default organization
3. Create a super admin user
4. Generate sample data for testing

## Testing

Run the test suite to verify multi-tenant functionality:

```bash
cd fastapi_migration
python -m pytest tests/test_multitenant.py -v
```

Tests cover:
- Organization isolation
- Data isolation between tenants
- User management with proper permissions
- Authentication with tenant context
- API access control

## Deployment Considerations

### Environment Variables
Required environment variables for production:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
SECRET_KEY=your-very-secure-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com

# Super Admin
SUPER_ADMIN_EMAILS=["admin@yourdomain.com"]

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Database Setup
1. Create PostgreSQL database
2. Set up database user with appropriate permissions
3. Run migration script to create tables and initial data
4. Set up regular backups

### Security Checklist
- [ ] Strong SECRET_KEY in production
- [ ] HTTPS enabled
- [ ] Database connections encrypted
- [ ] Regular security updates
- [ ] Audit log monitoring
- [ ] Backup and disaster recovery plan
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints

## API Usage Examples

### Creating an Organization (Super Admin)
```bash
curl -X POST "https://api.yourdomain.com/api/v1/organizations/" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ACME Corporation",
    "subdomain": "acme",
    "primary_email": "admin@acme.com",
    "primary_phone": "+1234567890",
    "address1": "123 Business St",
    "city": "Business City",
    "state": "Business State",
    "pin_code": "12345",
    "country": "India",
    "admin_email": "admin@acme.com",
    "admin_password": "securepassword123",
    "admin_full_name": "ACME Administrator"
  }'
```

### Logging in as Organization User
```bash
curl -X POST "https://acme.yourdomain.com/api/v1/auth/login/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "securepassword123"
  }'
```

### Creating a Vendor (Organization Context)
```bash
curl -X POST "https://acme.yourdomain.com/api/v1/vendors/" \
  -H "Authorization: Bearer ORG_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Supplier Inc",
    "contact_number": "+1234567891",
    "email": "contact@supplier.com",
    "address1": "456 Supplier Ave",
    "city": "Supplier City",
    "state": "Supplier State",
    "pin_code": "54321",
    "state_code": "SS"
  }'
```

## Troubleshooting

### Common Issues

1. **Organization context not set**
   - Ensure subdomain or X-Organization-ID header is provided
   - Check TenantMiddleware is properly configured

2. **Cross-tenant data access**
   - Verify TenantQueryMixin is used in all queries
   - Check organization_id is properly set on creation

3. **Authentication issues**
   - Verify JWT token includes organization_id
   - Check user belongs to the expected organization

4. **Permission denied errors**
   - Verify user role and permissions
   - Check if organization is active

### Logging
Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Advanced Features**
   - Single Sign-On (SSO) integration
   - Advanced audit reporting
   - Custom branding per organization
   - API key management

2. **Performance Optimizations**
   - Database query optimization
   - Caching strategies
   - Connection pooling
   - Read replicas for reporting

3. **Monitoring & Analytics**
   - Usage analytics per organization
   - Performance monitoring
   - Error tracking
   - Billing and usage reports

This multi-tenant architecture provides a solid foundation for a scalable SaaS application with proper data isolation, security, and feature management.