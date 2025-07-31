# Platform Super Admin Setup

## Overview

The TRITIQ ERP system now supports a **Platform Super Admin** functionality for first-run setup and multi-tenant management. This super admin is not tied to any specific organization and has global access to create and manage organizations.

## How It Works

### 1. Database Schema Changes

- The `users.organization_id` field is **nullable** to support platform super admins
- Only platform super admins should have `organization_id = NULL` (enforced in application logic)
- The `users.is_super_admin` field identifies platform-level administrators
- All other users must belong to an organization

### 2. Default Super Admin Creation

After database migration and on first application startup, the system automatically creates a default platform super admin:

- **Email**: `naughtyfruit53@gmail.com`
- **Password**: `123456` (must be changed on first login)
- **Username**: `super_admin`
- **Role**: `super_admin`
- **Organization**: None (organization_id = NULL)
- **Permissions**: Platform-wide access

⚠️ **SECURITY WARNING**: The default password is `123456`. This must be changed immediately after first login!

### 3. Seeding Logic

The seeding logic (`app/core/seed_super_admin.py`) ensures:
- Only one platform super admin is created
- Seeding only runs if no platform super admin exists
- The user is forced to change password on first login (`must_change_password = True`)
- Gracefully handles cases where database schema is not yet updated

## Setup Instructions

### Option 1: Fresh Installation (Recommended)

For new installations, use the provided setup script:

```bash
cd fastapi_migration
python setup_fresh_db.py
```

This creates a new database file `tritiq_erp_fresh.db` with the correct schema and seeds the super admin.

Then start the application:
```bash
# Set the database URL to use the fresh database
export DATABASE_URL="sqlite:///./tritiq_erp_fresh.db"
python -m uvicorn app.main:app --reload
```

### Option 2: Using Alembic Migrations

For existing installations that need to be migrated:

1. **Run Migration**: Apply the new migration to update schema
   ```bash
   cd fastapi_migration
   alembic upgrade head
   ```

2. **Start Application**: The app will automatically seed the super admin on startup
   ```bash
   python -m uvicorn app.main:app --reload
   ```

### Option 3: After Database Reset

If you've reset the database and want to start fresh:

1. Delete existing database files
2. Run the fresh setup script (Option 1), or
3. Run alembic migrations and start the app (Option 2)

## First Login Process

1. **Access the Application**: Navigate to the login page
2. **Login Credentials**: 
   - Email: `naughtyfruit53@gmail.com`
   - Password: `123456`
3. **Change Password**: You will be prompted to change the password
4. **Create Organizations**: As platform super admin, you can now:
   - Create new organizations
   - Create organization-level super admins
   - Manage multi-tenant settings

## User Hierarchy

```
Platform Super Admin (organization_id = NULL)
├── Organization A
│   ├── Organization Super Admin
│   ├── Admin Users
│   └── Standard Users
├── Organization B
│   ├── Organization Super Admin
│   ├── Admin Users
│   └── Standard Users
└── Organization C
    └── ...
```

## Database Migration Details

The migration `004_add_organization_support.py` adds:

1. **Organizations table** - Core multi-tenant table
2. **Users table modifications**:
   - `organization_id` (nullable for platform super admin)
   - `is_super_admin` field
   - Additional user profile fields (department, designation, etc.)
3. **Multi-tenant support** for existing tables (companies, vendors, etc.)

## Files Created/Modified

### New Files:
- `migrations/versions/004_add_organization_support.py` - Migration script
- `app/core/seed_super_admin.py` - Super admin seeding logic
- `setup_fresh_db.py` - Fresh database setup script
- `PLATFORM_SUPER_ADMIN.md` - This documentation

### Modified Files:
- `app/models/base.py` - Added comment clarifying nullable organization_id
- `app/main.py` - Updated startup event to call seeding logic
- `requirements.txt` - Added alembic and email-validator dependencies

## Security Considerations

1. **Organization Isolation**: All data is isolated by organization_id except for platform super admin
2. **Role-based Access**: Platform super admin has unrestricted access
3. **Password Policy**: Default password must be changed on first login
4. **Audit Trail**: All super admin actions should be logged (implement as needed)

## API Endpoints

Platform super admins have access to additional endpoints:
- `/api/v1/organizations` - Manage organizations
- `/api/v1/users` - Manage users across organizations (with proper filtering)
- Organization creation and management endpoints

## Development Notes

- The seeding logic runs on every startup but only creates the super admin if none exists
- The system gracefully handles cases where the database schema is outdated
- Use `setup_fresh_db.py` for development and testing with a clean database
- For production, always use proper Alembic migrations

## Troubleshooting

### Issue: "Database schema appears to be outdated"
**Solution**: Run `alembic upgrade head` to update the database schema

### Issue: "No super admin seeded on startup"
**Solution**: Check that the database schema includes `organization_id` and `is_super_admin` columns in the users table

### Issue: "Cannot login with super admin credentials"
**Solution**: Verify the super admin was created by checking the database or running the fresh setup script