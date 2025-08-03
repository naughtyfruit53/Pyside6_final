from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.config import settings as config_settings
from app.core.database import create_tables, SessionLocal
from app.core.tenant import TenantMiddleware
from app.core.seed_super_admin import seed_super_admin
from app.api import users, companies, vendors, customers, products, stock, organizations, reports, platform, settings, pincode
from app.api.vouchers import router as vouchers_router
from app.api.routes import admin
import logging

# Import enhanced v1 routers
from app.api.v1 import auth as v1_auth, admin as v1_admin, reset as v1_reset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=config_settings.PROJECT_NAME,
    version=config_settings.VERSION,
    description=config_settings.DESCRIPTION,
    openapi_url=f"{config_settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy
app.add_middleware(TenantMiddleware)

# ------------------------------------------------------------------------------
# ENHANCED V1 API ROUTERS
# ------------------------------------------------------------------------------
app.include_router(
    v1_auth.router, 
    prefix=f"{config_settings.API_V1_STR}/auth", 
    tags=["authentication-v1"]
)
app.include_router(
    v1_admin.router, 
    prefix=f"{config_settings.API_V1_STR}/admin", 
    tags=["admin-v1"]
)
app.include_router(
    v1_reset.router, 
    prefix=f"{config_settings.API_V1_STR}/reset", 
    tags=["reset-v1"]
)

# ------------------------------------------------------------------------------
# LEGACY API ROUTERS (business modules)
# ------------------------------------------------------------------------------
app.include_router(platform.router, prefix=f"{config_settings.API_V1_STR}/platform", tags=["platform"])
app.include_router(organizations.router, prefix=f"{config_settings.API_V1_STR}/organizations", tags=["organizations"])
app.include_router(users.router, prefix=f"{config_settings.API_V1_STR}/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin-legacy"])
app.include_router(companies.router, prefix=f"{config_settings.API_V1_STR}/companies", tags=["companies"])
app.include_router(vendors.router, prefix=f"{config_settings.API_V1_STR}/vendors", tags=["vendors"])
app.include_router(customers.router, prefix=f"{config_settings.API_V1_STR}/customers", tags=["customers"])
app.include_router(products.router, prefix=f"{config_settings.API_V1_STR}/products", tags=["products"])
app.include_router(stock.router, prefix=f"{config_settings.API_V1_STR}/stock", tags=["stock"])
app.include_router(vouchers_router, prefix=f"{config_settings.API_V1_STR}/vouchers", tags=["vouchers"])
app.include_router(reports.router, prefix=f"{config_settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(settings.router, prefix=f"{config_settings.API_V1_STR}/settings", tags=["settings"])
app.include_router(pincode.router, prefix=f"{config_settings.API_V1_STR}/pincode", tags=["pincode"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables on startup"""
    logger.info("Starting up TRITIQ ERP API...")
    try:
        create_tables()
        logger.info("Database tables created successfully")
        # Check if database schema is updated and seed super admin if possible
        from app.core.seed_super_admin import check_database_schema_updated
        db = SessionLocal()
        try:
            if check_database_schema_updated(db):
                seed_super_admin(db)
                logger.info("Super admin seeding completed")
            else:
                logger.warning("Database schema is not updated. Run 'alembic upgrade head' to enable super admin seeding.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down TRITIQ ERP API...")

@app.get("/")
async def root():
    return {
        "message": "Welcome to TRITIQ ERP API",
        "version": config_settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": config_settings.VERSION}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config_settings.DEBUG
    )