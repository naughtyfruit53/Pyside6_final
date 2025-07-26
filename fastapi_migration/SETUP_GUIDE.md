# TRITIQ ERP - FastAPI Migration Setup Guide

This guide will help you set up the FastAPI migration of the PySide6 ERP application with Supabase as the database backend.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for local development)
- Supabase account

### 1. Supabase Setup

1. **Create a Supabase Project**:
   - Go to [Supabase](https://supabase.com)
   - Create a new project
   - Note down your project URL and API keys

2. **Get Database Connection Details**:
   - Go to Project Settings → Database
   - Copy the connection string
   - Get your API keys from Project Settings → API

### 2. Backend Setup

1. **Clone and Setup Environment**:
   ```bash
   cd fastapi_migration
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables** (`.env`):
   ```env
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   SUPABASE_URL=https://[project-ref].supabase.co
   SUPABASE_KEY=[your-anon-key]
   SUPABASE_SERVICE_KEY=[your-service-role-key]
   
   SECRET_KEY=your-super-secret-key-change-this
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Email Configuration (Choose one)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAILS_FROM_EMAIL=your-email@gmail.com
   
   # OR use SendGrid
   # SENDGRID_API_KEY=your-sendgrid-api-key
   ```

4. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start the Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation at `http://localhost:8000/docs`

### 3. Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**:
   ```bash
   # Create .env.local
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

3. **Start the Frontend**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### 4. Using Docker (Alternative)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Database Migration from PySide6

### Current Issues Fixed

1. **✅ Voucher Session Errors**: 
   - Individual voucher tables eliminate session conflicts
   - Proper transaction handling in FastAPI

2. **✅ Separate Voucher Tables**: 
   - `purchase_vouchers` table for purchase vouchers
   - `sales_vouchers` table for sales vouchers
   - `purchase_orders` table for purchase orders
   - Each voucher type has its own dedicated table

3. **✅ Email Authentication**: 
   - Login with email address
   - JWT token-based authentication
   - Role-based access control maintained

4. **✅ Email Notifications**: 
   - Send vouchers to vendors/customers via email
   - Professional HTML email templates
   - Background email processing

### Data Migration Steps

1. **Export Data from SQLite**:
   ```bash
   # From the original PySide6 app directory
   sqlite3 erp_system.db .dump > data_export.sql
   ```

2. **Convert and Import to PostgreSQL**:
   ```bash
   # Process the export to separate voucher data
   python convert_voucher_data.py data_export.sql
   ```

3. **Create Initial Admin User**:
   ```bash
   python -c "
   from app.models.base import User
   from app.core.security import get_password_hash
   from app.core.database import SessionLocal
   
   db = SessionLocal()
   admin_user = User(
       email='admin@tritiq.com',
       username='admin',
       full_name='System Administrator',
       hashed_password=get_password_hash('admin123'),
       role='super_admin',
       is_active=True
   )
   db.add(admin_user)
   db.commit()
   print('Admin user created: admin@tritiq.com / admin123')
   "
   ```

## 🎯 Key Features & Improvements

### New Features
- **📧 Email Authentication**: Login with email instead of username
- **📬 Email Notifications**: Send vouchers directly to vendors/customers
- **🗃️ Individual Voucher Tables**: No more single voucher_instance table
- **🌐 Web Interface**: Modern responsive web UI
- **🔐 JWT Authentication**: Secure token-based auth
- **📊 RESTful API**: Complete REST API for all operations
- **🏗️ Modular Architecture**: Clean separation of concerns

### Preserved Features
- **👥 User Management**: Role-based authentication system
- **🏢 Company Management**: Company details and configuration
- **📋 Master Data**: Vendors, customers, products with GST compliance
- **📄 Voucher System**: All voucher types from original app
- **📦 Stock Management**: Inventory tracking and low-stock alerts
- **🏭 Manufacturing**: BOM, work orders (to be implemented)
- **📊 Audit Logging**: Enhanced with JSON change tracking
- **📈 Reporting**: PDF generation capabilities

## 🔧 API Usage Examples

### Authentication
```bash
# Login with email
curl -X POST "http://localhost:8000/api/v1/auth/login/email" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@tritiq.com", "password": "admin123"}'

# Use the returned token in subsequent requests
export TOKEN="your-jwt-token-here"
```

### Create Purchase Voucher
```bash
curl -X POST "http://localhost:8000/api/v1/vouchers/purchase-vouchers/?send_email=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voucher_number": "PV001",
    "date": "2024-01-15T10:00:00Z",
    "vendor_id": 1,
    "total_amount": 10000,
    "items": [
      {
        "product_id": 1,
        "quantity": 10,
        "unit": "PCS",
        "unit_price": 100,
        "taxable_amount": 1000,
        "total_amount": 1000
      }
    ]
  }'
```

### Send Email Notification
```bash
curl -X POST "http://localhost:8000/api/v1/vouchers/send-email/purchase_voucher/1" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Verify Supabase URL and credentials
   - Check network connectivity
   - Ensure database exists

2. **Email Not Sending**:
   - Verify SMTP settings or SendGrid API key
   - Check email provider settings
   - Review email notification logs

3. **Frontend API Connection**:
   - Ensure backend is running on port 8000
   - Check CORS settings
   - Verify API_URL environment variable

### Logs and Monitoring

```bash
# View application logs
tail -f app.log

# Monitor email notifications
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/emails/notifications"
```

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
   ```env
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=your-production-supabase-url
   ```

2. **Build and Deploy**:
   ```bash
   # Build frontend
   cd frontend && npm run build
   
   # Deploy to your hosting platform
   # (Vercel, Netlify, Railway, Render, etc.)
   ```

## 📞 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the application logs
- Ensure all environment variables are configured correctly

---

**Congratulations!** 🎉 You have successfully migrated from PySide6 to FastAPI with enhanced features like email authentication, individual voucher tables, and email notifications.