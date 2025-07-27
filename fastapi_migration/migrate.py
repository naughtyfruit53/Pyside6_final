"""
Database migration script for multi-tenant architecture
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.base import Base, Organization, User, Company, Vendor, Customer, Product, Stock
import logging

logger = logging.getLogger(__name__)

def create_migration_engine():
    """Create database engine for migrations"""
    return create_engine(settings.DATABASE_URL, echo=True)

def run_migration():
    """Run the migration to add multi-tenant support"""
    engine = create_migration_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Create all tables (this will create new tables and skip existing ones)
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Check if we need to create a default super admin organization
        existing_orgs = db.query(Organization).count()
        
        if existing_orgs == 0:
            logger.info("Creating default organization and super admin user...")
            
            # Create default organization
            default_org = Organization(
                name="Default Organization",
                subdomain="default",
                status="active",
                business_type="Software",
                primary_email="admin@example.com",
                primary_phone="+1234567890",
                address1="123 Default Street",
                city="Default City",
                state="Default State",
                pin_code="12345",
                country="India",
                plan_type="enterprise",
                max_users=100,
                storage_limit_gb=50
            )
            
            db.add(default_org)
            db.flush()  # Get the organization ID
            
            # Create super admin user
            super_admin = User(
                organization_id=default_org.id,
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Super Administrator",
                role="org_admin",
                is_super_admin=True,
                is_active=True
            )
            
            db.add(super_admin)
            db.commit()
            
            logger.info(f"Created default organization '{default_org.name}' with super admin user")
            logger.info("Default login: admin@example.com / admin123")
        
        # Migration for existing data
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

def create_sample_data():
    """Create sample data for testing"""
    engine = create_migration_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        db = SessionLocal()
        
        # Check if sample organization already exists
        sample_org = db.query(Organization).filter(Organization.subdomain == "acme").first()
        
        if not sample_org:
            logger.info("Creating sample organization...")
            
            # Create sample organization
            sample_org = Organization(
                name="ACME Corporation",
                subdomain="acme",
                status="active",
                business_type="Manufacturing",
                industry="Electronics",
                website="https://acme-corp.com",
                description="Sample manufacturing company",
                primary_email="admin@acme-corp.com",
                primary_phone="+1234567891",
                address1="456 ACME Street",
                city="ACME City", 
                state="California",
                pin_code="90210",
                country="USA",
                plan_type="premium",
                max_users=50,
                storage_limit_gb=25
            )
            
            db.add(sample_org)
            db.flush()
            
            # Create organization admin
            org_admin = User(
                organization_id=sample_org.id,
                email="admin@acme-corp.com",
                username="acme_admin",
                hashed_password=get_password_hash("acme123"),
                full_name="ACME Administrator",
                role="org_admin",
                is_active=True
            )
            
            # Create regular user
            regular_user = User(
                organization_id=sample_org.id,
                email="user@acme-corp.com",
                username="acme_user",
                hashed_password=get_password_hash("user123"),
                full_name="ACME User",
                role="standard_user",
                department="Operations",
                designation="Operator",
                is_active=True
            )
            
            db.add(org_admin)
            db.add(regular_user)
            
            # Create sample company details
            company = Company(
                organization_id=sample_org.id,
                name="ACME Corporation",
                address1="456 ACME Street",
                city="ACME City",
                state="California",
                pin_code="90210",
                state_code="CA",
                contact_number="+1234567891",
                email="info@acme-corp.com",
                gst_number="GST123456789",
                pan_number="PAN123456"
            )
            
            db.add(company)
            
            # Create sample vendor
            vendor = Vendor(
                organization_id=sample_org.id,
                name="Sample Vendor Inc",
                contact_number="+1234567892",
                email="vendor@example.com",
                address1="789 Vendor Lane",
                city="Vendor City",
                state="Texas",
                pin_code="75001",
                state_code="TX",
                gst_number="VENDORGST123"
            )
            
            db.add(vendor)
            
            # Create sample customer
            customer = Customer(
                organization_id=sample_org.id,
                name="Sample Customer LLC",
                contact_number="+1234567893",
                email="customer@example.com", 
                address1="321 Customer Ave",
                city="Customer City",
                state="Florida",
                pin_code="33101",
                state_code="FL",
                gst_number="CUSTOMERGST123"
            )
            
            db.add(customer)
            
            # Create sample product
            product = Product(
                organization_id=sample_org.id,
                name="Sample Widget",
                hsn_code="8421",
                unit="PCS",
                unit_price=100.0,
                gst_rate=18.0,
                description="A sample widget for testing"
            )
            
            db.add(product)
            db.flush()
            
            # Create sample stock
            stock = Stock(
                organization_id=sample_org.id,
                product_id=product.id,
                quantity=100.0,
                unit="PCS",
                location="Warehouse A"
            )
            
            db.add(stock)
            
            db.commit()
            logger.info("Sample data created successfully!")
            logger.info("Sample login: admin@acme-corp.com / acme123")
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting database migration...")
    run_migration()
    create_sample_data()
    logger.info("Migration and sample data creation completed!")