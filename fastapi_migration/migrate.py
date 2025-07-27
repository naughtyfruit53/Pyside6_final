# migrate.py (revised)

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

def add_missing_columns(engine):
    """Explicitly add missing organization_id columns to all tables"""
    tables_to_update = [
        'companies', 'vendors', 'customers', 'products', 'stock',
        'purchase_vouchers', 'purchase_voucher_items',
        'sales_vouchers', 'sales_voucher_items',
        'purchase_orders', 'purchase_order_items',
        'sales_orders', 'sales_order_items',
        'goods_receipt_notes', 'goods_receipt_note_items',
        'delivery_challans', 'delivery_challan_items',
        'proforma_invoices', 'proforma_invoice_items',
        'quotations', 'quotation_items',
        'credit_notes', 'credit_note_items',
        'debit_notes', 'debit_note_items'
    ]
    
    with engine.connect() as conn:
        for table in tables_to_update:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND column_name = 'organization_id';
                """))
                if result.fetchone() is None:
                    conn.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
                    """))
                    logger.info(f"Added organization_id to {table}")
                else:
                    logger.info(f"organization_id already exists in {table}")
                conn.commit()
            except Exception as e:
                logger.error(f"Failed to add column to {table}: {e}")
                conn.rollback()
        
        # For users
        try:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'organization_id';
            """))
            if result.fetchone() is None:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
                """))
                logger.info("Added organization_id to users")
            else:
                logger.info("organization_id already exists in users")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to add column to users: {e}")
            conn.rollback()

def run_migration():
    """Run the migration to add multi-tenant support"""
    engine = create_migration_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add missing columns
        add_missing_columns(engine)
        
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
                primary_email="naughtyfruit53@gmail.com",
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
                email="naughtyfruit53@gmail.com",
                username="admin",
                hashed_password=get_password_hash("123456"),
                full_name="Super Administrator",
                role="org_admin",
                is_super_admin=True,
                is_active=True,
                must_change_password=True  # Prompt to change password
            )
            
            db.add(super_admin)
            db.commit()
            
            logger.info(f"Created default organization '{default_org.name}' with super admin user")
            logger.info("Default login: naughtyfruit53@gmail.com / 123456")
        
        # Set default org_id for existing records
        default_org_id = db.query(Organization.id).first()[0] if db.query(Organization).count() > 0 else 1
        tables_to_update = [
            'companies', 'vendors', 'customers', 'products', 'stock',
            'purchase_vouchers', 'purchase_voucher_items',
            'sales_vouchers', 'sales_voucher_items',
            'purchase_orders', 'purchase_order_items',
            'sales_orders', 'sales_order_items',
            'goods_receipt_notes', 'goods_receipt_note_items',
            'delivery_challans', 'delivery_challan_items',
            'proforma_invoices', 'proforma_invoice_items',
            'quotations', 'quotation_items',
            'credit_notes', 'credit_note_items',
            'debit_notes', 'debit_note_items'
        ]
        for table in tables_to_update:
            db.execute(text(f"""
                UPDATE {table} 
                SET organization_id = {default_org_id}
                WHERE organization_id IS NULL;
            """))
        db.execute(text(f"""
            UPDATE users 
            SET organization_id = {default_org_id}
            WHERE organization_id IS NULL;
        """))
        db.commit()
        
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
        sample_org = db.query(Organization).filter(Organization.subdomain == "tritiq").first()
        
        if not sample_org:
            logger.info("Creating sample Indian organization...")
            
            # Create sample Indian organization
            sample_org = Organization(
                name="Tritiq India Pvt Ltd",
                subdomain="tritiq",
                status="active",
                business_type="Software Services",
                industry="Information Technology",
                website="https://tritiq.in",
                description="Sample Indian software company",
                primary_email="admin@tritiq.in",
                primary_phone="+91-9876543210",
                address1="456 Tech Park",
                city="Bangalore",
                state="Karnataka",
                pin_code="560001",
                country="India",
                plan_type="premium",
                max_users=50,
                storage_limit_gb=25
            )
            
            db.add(sample_org)
            db.flush()
            
            # Create organization admin
            org_admin = User(
                organization_id=sample_org.id,
                email="admin@tritiq.in",
                username="tritiq_admin",
                hashed_password=get_password_hash("tritiq123"),
                full_name="Tritiq Administrator",
                role="org_admin",
                is_active=True
            )
            
            # Create regular user
            regular_user = User(
                organization_id=sample_org.id,
                email="user@tritiq.in",
                username="tritiq_user",
                hashed_password=get_password_hash("user123"),
                full_name="Tritiq User",
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
                name="Tritiq India Pvt Ltd",
                address1="456 Tech Park",
                address2=None,
                city="Bangalore",
                state="Karnataka",
                pin_code="560001",
                state_code="29",
                gst_number="29AAACT1234P1Z5",
                pan_number="AAACT1234P",
                contact_number="+91-9876543210",
                email="info@tritiq.in",
                logo_path=None
            )
            
            db.add(company)
            
            # Create sample vendor
            vendor = Vendor(
                organization_id=sample_org.id,
                name="Sample Vendor India",
                contact_number="+91-8765432109",
                email="vendor@sample.in",
                address1="789 Vendor Street",
                address2=None,
                city="Mumbai",
                state="Maharashtra",
                pin_code="400001",
                state_code="27",
                gst_number="27BBBVT5678Q1Z3"
            )
            
            db.add(vendor)
            
            # Create sample customer
            customer = Customer(
                organization_id=sample_org.id,
                name="Sample Customer India",
                contact_number="+91-7654321098",
                email="customer@sample.in", 
                address1="321 Customer Road",
                address2=None,
                city="Delhi",
                state="Delhi",
                pin_code="110001",
                state_code="07",
                gst_number="07CCCCT9012R1Z7"
            )
            
            db.add(customer)
            
            # Create sample product
            product = Product(
                organization_id=sample_org.id,
                name="Sample Software License",
                hsn_code="998314",
                unit="UNIT",
                unit_price=5000.0,
                gst_rate=18.0,
                description="A sample software license for testing"
            )
            
            db.add(product)
            db.flush()
            
            # Create sample stock
            stock = Stock(
                organization_id=sample_org.id,
                product_id=product.id,
                quantity=50.0,
                unit="UNIT",
                location="Bangalore Office"
            )
            
            db.add(stock)
            
            db.commit()
            logger.info("Sample Indian organization data created successfully!")
            logger.info("Sample login: admin@tritiq.in / tritiq123")
        
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