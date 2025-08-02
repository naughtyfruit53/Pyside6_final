# TRITIQ ERP - FastAPI Migration

A modern, scalable FastAPI-based backend with Next.js Turbopack frontend for the TRITIQ ERP system.

## 🌟 Latest Enhancements

### ⚡ Frontend: Turbopack Integration
- **10x Faster Development**: Turbopack enabled for lightning-fast builds
- **Instant Hot Reload**: Changes reflect immediately without losing state
- **Enhanced Developer Experience**: Improved error reporting and debugging

### 🔐 Backend: Security & Reliability Improvements
- **Secure Password Reset**: Admin-controlled password reset with email notifications
- **Advanced Session Management**: Automatic rollback and retry logic
- **Enhanced Email Service**: HTML templates with robust error handling
- **Comprehensive Logging**: Security auditing and database operation tracking

📖 **[View Complete Enhancement Documentation](./docs/ENHANCEMENTS.md)**

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI 0.111.0 with Python 3.12+
- **Frontend**: Next.js 15.4.4 with Turbopack
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based access
- **Email**: SMTP with HTML template support
- **Testing**: pytest with comprehensive coverage

### Key Features
- 🏢 **Multi-tenant Architecture**: Organization-based data isolation
- 👥 **Role-based Access Control**: Super admin, org admin, and user roles
- 📧 **Email Notifications**: Automated notifications with custom templates
- 📊 **Voucher Management**: Complete voucher lifecycle management
- 🔍 **Audit Logging**: Comprehensive security and operation auditing
- 📱 **Responsive UI**: Modern Material-UI interface

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18.17+
- PostgreSQL (or SQLite for development)

### Backend Setup

1. **Clone and navigate to backend**:
   ```bash
   git clone <repository-url>
   cd fastapi_migration
   ```

2. **Install dependencies**:
   ```bash
   pip install -r ../requirements.txt
   pip install pydantic-settings sqlalchemy alembic pandas openpyxl
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the backend**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server** (with Turbopack):
   ```bash
   npm run dev
   ```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/tritiq_erp
# Or for development:
# DATABASE_URL=sqlite:///./tritiq_erp.db

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
PROJECT_NAME="TRITIQ ERP API"
VERSION="1.0.0"
DEBUG=true
API_V1_STR="/api/v1"

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Email (Optional - for password reset functionality)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME="TRITIQ ERP"
```

## 🔧 Development

### Backend Development

#### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest app/tests/test_admin.py
pytest app/tests/test_vouchers.py
```

#### Database Management
```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

#### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Frontend Development

#### Turbopack Benefits
- ⚡ **10x faster** than Webpack in development
- 🔄 **Instant hot reload** without losing component state
- 📦 **Optimized bundling** with incremental compilation

#### Development Commands
```bash
# Start with Turbopack (default)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

## 🏢 Multi-tenant Architecture

### Organization Management
- **Subdomain-based Routing**: Each organization has a unique subdomain
- **Data Isolation**: Complete separation of organizational data
- **User Management**: Organization-specific user accounts
- **License Management**: Flexible licensing and subscription management

### User Roles
- **Super Admin**: Platform-level administration
- **Organization Admin**: Organization management and user administration
- **Licenseholder Admin**: Limited administrative privileges
- **Standard User**: Basic application access

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-based Access**: Granular permission system
- **Password Security**: Secure password generation and reset
- **Session Management**: Automatic session timeout and cleanup

### Password Reset System
- **Admin-controlled**: Only super admins can reset passwords
- **Dual Notification**: Email to user + display to admin
- **Security Auditing**: All operations logged
- **Force Password Change**: Users must change password on next login

### Audit Logging
- **Security Events**: Login attempts, password resets, permission changes
- **Database Operations**: All CRUD operations tracked
- **Email Operations**: Email sending results and errors
- **API Access**: Request logging and rate limiting

## 📧 Email System

### Features
- **HTML Templates**: Professional email templates with variable substitution
- **Error Handling**: Robust error handling with detailed logging
- **Template System**: Reusable templates for different notification types
- **Configuration Validation**: Email settings validated before sending

### Supported Templates
- **Password Reset**: Secure password reset notifications
- **Voucher Notifications**: Voucher creation and updates
- **System Alerts**: Security and system notifications

## 📊 API Endpoints

### Core Endpoints
```
# Authentication
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout

# User Management
GET  /api/v1/users/
POST /api/v1/users/
PUT  /api/v1/users/{id}

# Admin Operations
POST /api/v1/admin/reset-password
GET  /api/v1/admin/users
PUT  /api/v1/admin/users/{id}
DELETE /api/v1/admin/users/{id}

# Organizations
GET  /api/v1/organizations/
POST /api/v1/organizations/
PUT  /api/v1/organizations/{id}

# Vouchers
GET  /api/v1/vouchers/purchase
POST /api/v1/vouchers/purchase
GET  /api/v1/vouchers/sales
POST /api/v1/vouchers/sales

# Products, Vendors, Customers
GET  /api/v1/products/
GET  /api/v1/vendors/
GET  /api/v1/customers/
```

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Individual function and method testing
- **Integration Tests**: API endpoint testing
- **Security Tests**: Authentication and authorization
- **Database Tests**: Transaction and rollback testing

### Running Tests
```bash
# Backend tests
cd fastapi_migration
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment

#### Backend (FastAPI)
```bash
# Using uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Frontend (Next.js)
```bash
# Build and start
npm run build
npm run start

# Or deploy to Vercel, Netlify, etc.
```

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./fastapi_migration
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tritiq
    depends_on:
      - db
  
  frontend:
    build: ./fastapi_migration/frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=tritiq
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 📈 Monitoring and Health Checks

### Health Endpoints
```bash
# Database health
GET /api/v1/health/db

# Application health
GET /api/v1/health/

# Session pool status
GET /api/v1/health/pool
```

### Logging
- **Application Logs**: `logs/app_YYYYMMDD.log`
- **Error Logs**: `logs/errors_YYYYMMDD.log`
- **Security Logs**: Dedicated security event logging
- **Database Logs**: Transaction and operation logging

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

### Code Standards
- **Backend**: Follow PEP 8 with black formatting
- **Frontend**: ESLint with Next.js recommended rules
- **Testing**: Maintain high test coverage
- **Documentation**: Update docs for new features

## 📞 Support and Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check database connectivity
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### Email Configuration
```bash
# Test email configuration
python -c "from app.services.email_service import email_service; print(email_service._validate_email_config())"
```

#### Frontend Build Issues
```bash
# Clear Next.js cache
rm -rf .next
npm install
npm run dev
```

### Getting Help
- **Documentation**: Check `/docs/ENHANCEMENTS.md` for detailed guides
- **API Docs**: Visit `/docs` endpoint for interactive API documentation
- **Logs**: Check application logs for detailed error information
- **Health Checks**: Use health endpoints to verify system status

## 📄 License

This project is proprietary software for TRITIQ ERP system.

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- Next.js team for Turbopack innovation
- SQLAlchemy team for robust ORM
- Material-UI team for beautiful components

---

**Note**: This is a modern, production-ready ERP system with enterprise-grade security, scalability, and developer experience. The Turbopack integration provides the best-in-class development experience while maintaining production reliability.