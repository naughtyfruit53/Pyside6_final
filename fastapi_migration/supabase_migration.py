#!/usr/bin/env python3
"""
Comprehensive Supabase Database Migration Script

This script performs a complete database reset and schema recreation for the FastAPI ERP system.
- Drops all existing tables in Supabase
- Creates new schema with strict organization-level separation
- Optionally seeds demo data
- Designed for PostgreSQL/Supabase
"""

import os
import sys
import logging
import argparse
from typing import Optional
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.base import Base, PlatformUser, Organization, User, Company, Vendor, Customer, Product, Stock
from app.models.vouchers import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SupabaseMigration:
    """Handles Supabase database migration operations"""
    
    def __init__(self, database_url: str, drop_all: bool = False):
        self.database_url = database_url
        self.drop_all = drop_all
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Create database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=True  # Show SQL statements
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def drop_all_tables(self):
        """Drop all existing tables in the database"""
        if not self.drop_all:
            logger.info("Skipping table drop (use --drop-all to enable)")
            return
            
        logger.warning("⚠️  DROPPING ALL TABLES - This will delete all data!")
        
        try:
            with self.engine.connect() as conn:
                # Check if we're using PostgreSQL or SQLite
                is_postgresql = self.database_url.startswith(("postgresql://", "postgres://"))
                is_sqlite = self.database_url.startswith("sqlite://")
                
                if is_postgresql:
                    # PostgreSQL specific commands
                    # Disable foreign key checks temporarily
                    conn.execute(text("SET session_replication_role = replica"))
                    
                    # Get all table names
                    result = conn.execute(text("""
                        SELECT tablename FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename NOT LIKE 'pg_%' 
                        AND tablename NOT LIKE 'sql_%'
                    """))
                    
                    tables = [row[0] for row in result.fetchall()]
                    
                    # Drop all tables
                    for table in tables:
                        try:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                            logger.info(f"Dropped table: {table}")
                        except Exception as e:
                            logger.warning(f"Failed to drop table {table}: {e}")
                    
                    # Drop all sequences
                    result = conn.execute(text("""
                        SELECT sequence_name FROM information_schema.sequences 
                        WHERE sequence_schema = 'public'
                    """))
                    
                    sequences = [row[0] for row in result.fetchall()]
                    
                    for sequence in sequences:
                        try:
                            conn.execute(text(f"DROP SEQUENCE IF EXISTS {sequence} CASCADE"))
                            logger.info(f"Dropped sequence: {sequence}")
                        except Exception as e:
                            logger.warning(f"Failed to drop sequence {sequence}: {e}")
                    
                    # Re-enable foreign key checks
                    conn.execute(text("SET session_replication_role = DEFAULT"))
                    
                elif is_sqlite:
                    # SQLite specific commands
                    # Enable foreign keys
                    conn.execute(text("PRAGMA foreign_keys = OFF"))
                    
                    # Get all table names
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """))
                    
                    tables = [row[0] for row in result.fetchall()]
                    
                    # Drop all tables
                    for table in tables:
                        try:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                            logger.info(f"Dropped table: {table}")
                        except Exception as e:
                            logger.warning(f"Failed to drop table {table}: {e}")
                    
                    # Re-enable foreign keys
                    conn.execute(text("PRAGMA foreign_keys = ON"))
                
                else:
                    logger.warning("Unknown database type, attempting generic table drop")
                    # Generic approach - just use SQLAlchemy metadata
                    Base.metadata.drop_all(bind=self.engine)
                
                conn.commit()
                logger.info("✅ All tables dropped successfully")
                
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def create_schema(self):
        """Create the new database schema"""
        logger.info("Creating new database schema...")
        
        try:
            # Create all tables from models
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database schema created successfully")
            
            # Create additional indexes for performance
            self._create_additional_indexes()
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise
    
    def _create_additional_indexes(self):
        """Create additional indexes for better performance"""
        logger.info("Creating additional performance indexes...")
        
        # Check database type for appropriate syntax
        is_postgresql = self.database_url.startswith(("postgresql://", "postgres://"))
        
        indexes = [
            # Voucher performance indexes
            "CREATE INDEX IF NOT EXISTS idx_voucher_org_date_status ON purchase_vouchers(organization_id, date, status)",
            "CREATE INDEX IF NOT EXISTS idx_voucher_org_vendor_date ON purchase_vouchers(organization_id, vendor_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_voucher_org_date_status ON sales_vouchers(organization_id, date, status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_voucher_org_customer_date ON sales_vouchers(organization_id, customer_id, date)",
            
            # Stock indexes
            "CREATE INDEX IF NOT EXISTS idx_stock_org_product_quantity ON stock(organization_id, product_id, quantity)",
        ]
        
        # Add PostgreSQL-specific indexes if needed
        if is_postgresql:
            indexes.extend([
                # Audit indexes
                "CREATE INDEX IF NOT EXISTS idx_audit_org_table_timestamp ON audit_logs(organization_id, table_name, timestamp)",
                # Email notification indexes
                "CREATE INDEX IF NOT EXISTS idx_email_org_status_created ON email_notifications(organization_id, status, created_at)",
            ])
        
        try:
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
                conn.commit()
            
            logger.info("✅ Additional indexes created")
            
        except Exception as e:
            logger.warning(f"Some indexes may have failed: {e}")
    
    def seed_platform_admin(self):
        """Create the platform super admin user"""
        logger.info("Seeding platform super admin...")
        
        db = self.SessionLocal()
        try:
            # Check if platform admin already exists
            existing_admin = db.query(PlatformUser).filter(
                PlatformUser.email == "naughtyfruit53@gmail.com"
            ).first()
            
            if existing_admin:
                logger.info("Platform admin already exists, skipping creation")
                return
            
            # Create platform super admin
            platform_admin = PlatformUser(
                email="naughtyfruit53@gmail.com",
                hashed_password=get_password_hash("123456"),
                full_name="Platform Super Administrator",
                role="super_admin",
                is_active=True
            )
            
            db.add(platform_admin)
            db.commit()
            db.refresh(platform_admin)
            
            logger.info("✅ Platform super admin created")
            logger.info("🔑 Login: naughtyfruit53@gmail.com / 123456")
            logger.warning("⚠️  IMPORTANT: Change the default password after first login!")
            
        except Exception as e:
            logger.error(f"Failed to seed platform admin: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def seed_demo_data(self):
        """Create demo organization and data"""
        logger.info("Seeding demo data...")
        
        db = self.SessionLocal()
        try:
            # Check if demo org already exists
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            
            if demo_org:
                logger.info("Demo organization already exists, skipping creation")
                return
            
            # Create demo organization
            demo_org = Organization(
                name="Demo Manufacturing Corp",
                subdomain="demo",
                status="active",
                business_type="Manufacturing",
                industry="Industrial Equipment",
                website="https://demo-manufacturing.com",
                description="Demo organization for testing ERP functionality",
                primary_email="admin@demo-manufacturing.com",
                primary_phone="+91-9876543210",
                address1="123 Industrial Estate",
                address2="Phase 2",
                city="Bangalore",
                state="Karnataka",
                pin_code="560100",
                country="India",
                gst_number="29DEMCO1234P1Z5",
                pan_number="DEMCO1234P",
                cin_number="U12345KA2020PTC123456",
                plan_type="premium",
                max_users=50,
                storage_limit_gb=10,
                company_details_completed=True
            )
            
            db.add(demo_org)
            db.flush()  # Get the ID
            
            # Create demo organization admin
            demo_admin = User(
                organization_id=demo_org.id,
                email="admin@demo-manufacturing.com",
                username="demo_admin",
                hashed_password=get_password_hash("demo123"),
                full_name="Demo Administrator",
                role="org_admin",
                department="IT",
                designation="System Administrator",
                is_active=True
            )
            
            # Create demo user
            demo_user = User(
                organization_id=demo_org.id,
                email="user@demo-manufacturing.com",
                username="demo_user",
                hashed_password=get_password_hash("user123"),
                full_name="Demo User",
                role="standard_user",
                department="Operations",
                designation="Operator",
                is_active=True
            )
            
            db.add(demo_admin)
            db.add(demo_user)
            
            # Create demo company profile
            demo_company = Company(
                organization_id=demo_org.id,
                name="Demo Manufacturing Corp",
                address1="123 Industrial Estate",
                address2="Phase 2",
                city="Bangalore",
                state="Karnataka",
                pin_code="560100",
                state_code="29",
                gst_number="29DEMCO1234P1Z5",
                pan_number="DEMCO1234P",
                contact_number="+91-9876543210",
                email="info@demo-manufacturing.com"
            )
            
            db.add(demo_company)
            
            # Create demo vendor
            demo_vendor = Vendor(
                organization_id=demo_org.id,
                name="Reliable Suppliers Pvt Ltd",
                contact_number="+91-8765432109",
                email="sales@reliablesuppliers.com",
                address1="456 Supply Chain Road",
                city="Mumbai",
                state="Maharashtra",
                pin_code="400001",
                state_code="27",
                gst_number="27RELSU5678Q1Z3",
                pan_number="RELSU5678Q"
            )
            
            db.add(demo_vendor)
            
            # Create demo customer
            demo_customer = Customer(
                organization_id=demo_org.id,
                name="Tech Solutions India Ltd",
                contact_number="+91-7654321098",
                email="procurement@techsolutions.in",
                address1="789 Technology Park",
                city="Delhi",
                state="Delhi",
                pin_code="110001",
                state_code="07",
                gst_number="07TECHSO9012R1Z7",
                pan_number="TECHSO9012"
            )
            
            db.add(demo_customer)
            
            # Create demo products
            products_data = [
                {
                    "name": "Steel Rod 12mm",
                    "hsn_code": "72142000",
                    "part_number": "SR-12-001",
                    "unit": "KG",
                    "unit_price": 55.0,
                    "gst_rate": 18.0,
                    "description": "High grade steel rod for construction"
                },
                {
                    "name": "Bearing SKF 6205",
                    "hsn_code": "84829100",
                    "part_number": "BRG-SKF-6205",
                    "unit": "PCS",
                    "unit_price": 250.0,
                    "gst_rate": 18.0,
                    "description": "SKF ball bearing 6205 series"
                },
                {
                    "name": "Motor 5HP 3-Phase",
                    "hsn_code": "85014010",
                    "part_number": "MOT-5HP-3P",
                    "unit": "PCS",
                    "unit_price": 12500.0,
                    "gst_rate": 18.0,
                    "description": "5HP 3-phase induction motor"
                }
            ]
            
            demo_products = []
            for prod_data in products_data:
                product = Product(
                    organization_id=demo_org.id,
                    **prod_data
                )
                db.add(product)
                demo_products.append(product)
            
            db.flush()  # Get product IDs
            
            # Create demo stock entries
            for product in demo_products:
                stock = Stock(
                    organization_id=demo_org.id,
                    product_id=product.id,
                    quantity=100.0,
                    unit=product.unit,
                    location="Main Warehouse"
                )
                db.add(stock)
            
            db.commit()
            
            logger.info("✅ Demo data created successfully")
            logger.info("🏢 Organization: Demo Manufacturing Corp (subdomain: demo)")
            logger.info("🔑 Admin Login: admin@demo-manufacturing.com / demo123")
            logger.info("👤 User Login: user@demo-manufacturing.com / user123")
            
        except Exception as e:
            logger.error(f"Failed to seed demo data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def run_migration(self, seed_demo: bool = False):
        """Run the complete migration process"""
        logger.info("🚀 Starting Supabase migration...")
        
        try:
            self.connect()
            
            if self.drop_all:
                self.drop_all_tables()
            
            self.create_schema()
            self.seed_platform_admin()
            
            if seed_demo:
                self.seed_demo_data()
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


def main():
    """Main function to run the migration"""
    parser = argparse.ArgumentParser(description="Supabase Database Migration Script")
    parser.add_argument(
        "--database-url",
        help="Database URL (default: from settings)",
        default=None
    )
    parser.add_argument(
        "--drop-all",
        action="store_true",
        help="Drop all existing tables before migration (DESTRUCTIVE)"
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Seed demo data after migration"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm destructive operations"
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or settings.DATABASE_URL
    if not database_url:
        logger.error("Database URL not provided. Set DATABASE_URL environment variable or use --database-url")
        sys.exit(1)
    
    # Safety check for destructive operations
    if args.drop_all and not args.confirm:
        logger.warning("⚠️  --drop-all will delete ALL data in the database!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Migration cancelled")
            sys.exit(0)
    
    # Validate environment variables
    required_env_vars = ["SMTP_USERNAME", "SMTP_PASSWORD", "EMAILS_FROM_EMAIL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("Setting dummy values for migration...")
        for var in missing_vars:
            os.environ[var] = "dummy@example.com" if "EMAIL" in var else "dummy_value"
    
    # Run migration
    migration = SupabaseMigration(database_url, drop_all=args.drop_all)
    migration.run_migration(seed_demo=args.seed_demo)


if __name__ == "__main__":
    main()