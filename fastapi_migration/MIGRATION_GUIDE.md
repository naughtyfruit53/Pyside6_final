# FastAPI ERP Backend Migration Guide

This guide describes the comprehensive backend migration from PySide6-integrated backend to a pure FastAPI + Supabase architecture with strict multi-tenancy.

## Overview

The migration includes:
- Complete database schema redesign for strict organization-level separation
- Supabase PostgreSQL integration
- Enhanced multi-tenant architecture
- Auto-population workflows for vouchers
- Organization-scoped API endpoints
- Platform admin capabilities

## Migration Components

### 1. Database Schema Migration

The new schema enforces strict organization-level data isolation:

#### Core Tables
- `platform_users` - Platform administrators (no organization)
- `organizations` - Tenant organizations
- `users` - Organization users (required organization_id)
- `companies`, `vendors`, `customers`, `products`, `stock` - All scoped to organization

#### Voucher Tables
Enhanced voucher workflow with auto-population:
- `purchase_orders` → `goods_receipt_notes` → `purchase_vouchers`
- `sales_orders` → `delivery_challans` → `sales_vouchers`
- Relationship tracking for auto-population
- Quantity validation and pending tracking

#### Key Features
- **Unique constraints per organization** (voucher numbers, vendor names, etc.)
- **Foreign key relationships** for workflow integrity
- **Comprehensive indexes** for performance
- **Audit logging** per organization

### 2. Migration Script

Use `supabase_migration.py` for database migration:

```bash
# Basic migration (creates schema only)
python supabase_migration.py --database-url postgresql://user:pass@host/db

# Full reset with demo data
python supabase_migration.py --database-url postgresql://user:pass@host/db --drop-all --seed-demo --confirm

# SQLite testing
python supabase_migration.py --database-url sqlite:///./test.db --seed-demo
```

#### Migration Options
- `--drop-all` - Drop all existing tables (DESTRUCTIVE)
- `--seed-demo` - Create demo organization with sample data
- `--confirm` - Confirm destructive operations
- `--database-url` - Override database URL

### 3. Environment Configuration

Required environment variables:

```env
# Database (Supabase)
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Email (Required for OTP)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com

# JWT Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## API Changes

### 1. Authentication

#### Platform Users
- Email: `naughtyfruit53@gmail.com` / Password: `123456` (default platform admin)
- Access to all organizations
- Can specify `organization_id` in requests

#### Organization Users
- Automatically scoped to their organization
- Cannot access other organizations' data
- Enforced at database query level

### 2. Organization Scoping

All API endpoints now enforce organization-level data isolation:

```python
# Old (unsafe)
vendors = db.query(Vendor).all()

# New (organization-scoped)
vendors = TenantQueryFilter.apply_organization_filter(
    db.query(Vendor), Vendor, org_id, current_user
).all()
```

### 3. Voucher Workflows

Enhanced auto-population workflows:

#### Purchase Flow
1. **Create Purchase Order**
   ```
   POST /api/v1/vouchers/purchase-orders
   ```

2. **Auto-populate GRN from PO**
   ```
   GET /api/v1/vouchers/purchase-orders/{id}/grn-auto-populate
   ```

3. **Create GRN with PO data**
   ```
   POST /api/v1/vouchers/goods-receipt-notes
   ```

4. **Auto-populate Purchase Voucher from GRN**
   ```
   GET /api/v1/vouchers/goods-receipt-notes/{id}/purchase-voucher-auto-populate
   ```

5. **Create Purchase Voucher**
   ```
   POST /api/v1/vouchers/purchase-vouchers
   ```

#### Sales Flow
Similar workflow: SO → Delivery Challan → Sales Voucher

### 4. Search and Dropdown APIs

Organization-scoped search for dropdowns:

```
POST /api/v1/vendors/search?search_term=vendor_name
POST /api/v1/products/search?search_term=product_name
```

## Testing

### Migration Tests
```bash
python -m pytest tests/test_supabase_migration.py -v
```

### API Tests  
```bash
python -m pytest tests/test_api_organization_scoping.py -v
```

### Manual Testing

1. **Run Migration**
   ```bash
   python supabase_migration.py --database-url sqlite:///./test.db --seed-demo
   ```

2. **Start Server**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test Authentication**
   ```bash
   # Platform admin login
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=naughtyfruit53@gmail.com&password=123456"

   # Organization admin login  
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@demo-manufacturing.com&password=demo123"
   ```

4. **Test Organization Scoping**
   ```bash
   # Get vendors (organization-scoped)
   curl -X GET "http://localhost:8000/api/v1/vendors/" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Key Changes from Previous Architecture

### Removed Components
- PySide6 integration code
- Legacy user tables
- Non-scoped database queries
- Manual voucher number generation

### Enhanced Components
- **Strict multi-tenancy** - All data scoped to organizations
- **Auto-population workflows** - PO→GRN→Voucher with validation
- **Platform administration** - Separate platform users
- **Enhanced validation** - Quantity tracking, business rules
- **Performance optimization** - Strategic indexes, query optimization

### New Features
- **Voucher relationship tracking** - Full audit trail
- **Quantity management** - Pending/delivered tracking
- **Advanced search** - Organization-scoped dropdowns
- **Business logic validation** - Prevent invalid operations
- **Comprehensive logging** - Operation audit trails

## Deployment

### Production Deployment

1. **Database Setup**
   ```sql
   -- Create Supabase database
   -- Run migration script
   python supabase_migration.py --database-url $DATABASE_URL --confirm
   ```

2. **Environment Configuration**
   ```bash
   # Set production environment variables
   export DATABASE_URL="postgresql://..."
   export SECRET_KEY="production-secret-key"
   export DEBUG=false
   ```

3. **Application Deployment**
   ```bash
   # Docker deployment
   docker build -t erp-backend .
   docker run -p 8000:8000 --env-file .env erp-backend
   ```

### Development Setup

1. **Clone and Install**
   ```bash
   git clone <repository>
   cd fastapi_migration
   pip install -r requirements.txt
   ```

2. **Database Migration**
   ```bash
   python supabase_migration.py --database-url sqlite:///./dev.db --seed-demo
   ```

3. **Run Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path and module imports

2. **Database Connection**
   - Verify DATABASE_URL format
   - Check database permissions
   - Ensure Supabase service is running

3. **Authentication Issues**
   - Verify JWT SECRET_KEY
   - Check token expiration
   - Validate user organization access

4. **Organization Scoping**
   - Ensure organization_id is set in context
   - Verify user belongs to organization
   - Check TenantQueryFilter usage

### Testing Issues

1. **Schema Validation**
   ```bash
   # Validate database schema
   python -c "from app.models.base import *; from app.models.vouchers import *; print('Schema OK')"
   ```

2. **API Connectivity**
   ```bash
   # Test API health
   curl http://localhost:8000/health
   ```

3. **Data Isolation**
   ```bash
   # Run organization scoping tests
   python -m pytest tests/test_api_organization_scoping.py::TestOrganizationScoping::test_vendor_organization_isolation -v
   ```

## Support and Maintenance

### Monitoring

- Monitor organization data isolation
- Track voucher workflow completion
- Validate business rule enforcement
- Check performance metrics

### Backup and Recovery

- Regular database backups
- Test migration rollback procedures
- Document data recovery processes
- Maintain audit trails

For additional support, refer to the codebase documentation and test suites.