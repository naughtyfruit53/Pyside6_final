# FastAPI ERP Migration

This directory contains the FastAPI migration of the PySide6 ERP application.

## Migration Overview

### Original PySide6 Application Features:
1. **User Management**: Role-based authentication (super_admin, admin, standard_user)
2. **Company Management**: Company details, default directory setup
3. **Master Data**: Vendors, customers, products with GST compliance
4. **Voucher System**: Multiple voucher types with dynamic columns
5. **Stock Management**: Inventory tracking and management
6. **Manufacturing**: BOM, work orders, material in/out
7. **Financial**: Payment, receipt, contra, journal vouchers
8. **Audit**: Comprehensive audit logging
9. **Reporting**: PDF generation for vouchers

### New FastAPI Features:
1. **Email Authentication**: Login with email instead of username
2. **Separate Voucher Tables**: Individual tables for each voucher type
3. **Email Notifications**: Send vouchers to vendors/customers via email
4. **Web Interface**: Responsive web UI replacing PySide6
5. **Supabase Integration**: PostgreSQL database hosted on Supabase
6. **JWT Authentication**: Secure token-based authentication
7. **RESTful API**: Complete REST API for all operations

### Database Schema Changes:
- Individual tables for each voucher type instead of single `voucher_instances` table
- Email-based user authentication
- Enhanced audit logging
- Email notification tracking

## Directory Structure

```
fastapi_migration/
├── app/
│   ├── api/              # API routes
│   ├── core/            # Core configuration
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── main.py         # FastAPI application
├── frontend/           # Web interface
├── migrations/         # Database migrations
├── tests/             # Test files
├── requirements.txt   # Python dependencies
└── docker-compose.yml # Docker setup
```

## Setup Instructions

1. **Supabase Setup**:
   - Create Supabase project
   - Run database migrations
   - Configure environment variables

2. **Backend Setup**:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Migration Progress

- [x] Project structure created
- [ ] Database models migration
- [ ] API endpoints implementation
- [ ] Authentication system
- [ ] Email integration
- [ ] Frontend development
- [ ] Testing
- [ ] Deployment setup