# Test Guide for TRITIQ ERP FastAPI Application

This document provides a comprehensive guide to run all tests in the TRITIQ ERP FastAPI application.

## Test Structure

The project contains tests in two main directories:
- `app/tests/` - Application-specific tests  
- `tests/` - General integration and system tests

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio httpx
   ```

2. **Environment Setup**
   ```bash
   # Ensure you're in the fastapi_migration directory
   cd fastapi_migration
   
   # Set up environment variables (optional)
   cp .env.example .env
   ```

3. **Database Setup**
   ```bash
   # The app uses SQLite by default for testing
   # Database tables are created automatically on startup
   ```

## Running Tests

### 1. Run All Tests
```bash
# Run all tests with verbose output
python -m pytest -v

# Run all tests with detailed output and warnings
python -m pytest -v --tb=short
```

### 2. Run Tests by Category

#### Authentication Tests
```bash
# Core authentication functionality
python -m pytest tests/test_auth.py -v

# Temporary master password tests
python -m pytest tests/test_temporary_master_password.py -v

# Password management tests  
python -m pytest tests/test_password_management.py -v
```

#### Admin and User Management Tests
```bash
# Admin functionality tests
python -m pytest app/tests/test_admin.py -v

# Super admin seeding tests
python -m pytest tests/test_super_admin_seeding.py -v

# Super admin reset tests
python -m pytest tests/test_superadmin_reset.py -v
```

#### Voucher and Transaction Tests
```bash
# Voucher functionality tests
python -m pytest app/tests/test_vouchers.py -v

# Voucher add/select tests
python -m pytest tests/test_voucher_add_select.py -v
```

#### Organization and Multi-tenancy Tests
```bash
# API organization scoping tests
python -m pytest tests/test_api_organization_scoping.py -v

# Multi-tenant functionality tests
python -m pytest tests/test_multitenant.py -v

# Organization license tests
python -m pytest tests/test_organization_license.py -v

# License management tests
python -m pytest tests/test_license_management.py -v
```

#### Business Module Tests
```bash
# Company management tests
python -m pytest tests/test_companies.py -v

# Vendor and customer tests
python -m pytest tests/test_vendor_customer_save.py -v

# Stock management tests
python -m pytest tests/test_stock.py -v

# Product name consistency tests
python -m pytest tests/test_product_name_consistency.py -v
python -m pytest tests/test_product_name_standardization.py -v
```

#### Data and Import Tests
```bash
# Excel features tests
python -m pytest tests/test_excel_features.py -v

# Pincode lookup tests
python -m pytest tests/test_pincode_lookup.py -v
```

#### System and Integration Tests
```bash
# Complete migration workflow tests
python -m pytest tests/test_complete_migration_workflow.py -v

# Database reset functionality tests
python -m pytest tests/test_database_reset.py -v

# Settings module visibility tests
python -m pytest tests/test_settings_module_visibility.py -v

# Supabase migration tests
python -m pytest tests/test_supabase_migration.py -v
```

### 3. Run Tests with Coverage
```bash
# Install coverage if not already installed
pip install pytest-cov

# Run tests with coverage report
python -m pytest --cov=app --cov-report=html --cov-report=term

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

### 4. Run Specific Test Functions
```bash
# Run a specific test function
python -m pytest tests/test_auth.py::test_login_success -v

# Run tests matching a pattern
python -m pytest -k "test_auth" -v

# Run tests with specific markers (if configured)
python -m pytest -m "auth" -v
```

## Test Environment Configuration

### Database
- Tests use SQLite by default for isolation
- Each test may create its own database session
- Database is automatically cleaned up after tests

### Authentication
- Tests may use mock authentication or test users
- Super admin credentials for testing: `naughtyfruit53@gmail.com`

### API Testing
- Tests use FastAPI's TestClient for HTTP requests
- Base URL: `http://testserver`
- API endpoints are tested with proper authentication headers

## Common Test Issues and Solutions

### 1. Import Errors
```bash
# If you get import errors, ensure Python path is set correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m pytest tests/
```

### 2. Database Errors
```bash
# Clear test database if needed
rm -f test.db tritiq_erp.db

# Run tests with fresh database
python -m pytest tests/ --tb=short
```

### 3. Missing Dependencies
```bash
# Install missing test dependencies
pip install pytest pytest-asyncio httpx pytest-cov
pip install pandas openpyxl  # For Excel tests
pip install sib_api_v3_sdk   # For email service tests
```

### 4. Permission Errors
```bash
# Ensure proper permissions for test files
chmod +x tests/*.py
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
# Fast test run for CI
python -m pytest tests/ --tb=short --maxfail=5

# Generate JUnit XML for CI reporting
python -m pytest tests/ --junitxml=test-results.xml
```

## Test Development Guidelines

1. **Write focused tests** - Each test should test one specific functionality
2. **Use descriptive names** - Test names should clearly indicate what is being tested
3. **Clean up resources** - Ensure tests clean up any created data/files
4. **Mock external services** - Use mocks for email, external APIs, etc.
5. **Test edge cases** - Include tests for error conditions and boundary cases

## New Endpoint Testing

After the refactor, pay special attention to testing:

1. **New Voucher Endpoints**
   ```bash
   # Test the new sales and purchase endpoints
   curl -X GET "http://localhost:8000/api/vouchers/sales" -H "Authorization: Bearer <token>"
   curl -X GET "http://localhost:8000/api/vouchers/purchase" -H "Authorization: Bearer <token>"
   ```

2. **Consolidated Auth Endpoints**
   ```bash
   # Test v1 auth endpoints
   curl -X POST "http://localhost:8000/api/v1/auth/login" -H "Content-Type: application/json" -d '{"username": "test@example.com", "password": "password"}'
   ```

3. **Password Management**
   ```bash
   # Test password reset functionality for superadmin
   curl -X POST "http://localhost:8000/api/v1/admin/password/reset" -H "Authorization: Bearer <admin-token>" -H "Content-Type: application/json" -d '{"target_email": "user@example.com"}'
   ```

## Documentation

- API documentation: `http://localhost:8000/docs` (when server is running)
- Interactive API: `http://localhost:8000/redoc`
- Test coverage reports: `htmlcov/index.html` (after running with coverage)

---

**Note**: Some tests may require specific configuration or may be temporarily disabled due to dependencies. Check individual test files for specific requirements or skip conditions.