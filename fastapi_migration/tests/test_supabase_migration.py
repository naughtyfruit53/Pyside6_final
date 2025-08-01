#!/usr/bin/env python3
"""
Test suite for Supabase migration and database schema validation
"""

import os
import sys
import pytest
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import Base, PlatformUser, Organization, User, Company, Vendor, Customer, Product, Stock
from app.models.vouchers import *
from supabase_migration import SupabaseMigration

class TestSupabaseMigration:
    """Test suite for Supabase migration functionality"""
    
    @pytest.fixture
    def temp_db_url(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            yield db_url
            # Cleanup
            try:
                os.unlink(tmp.name)
            except:
                pass
    
    @pytest.fixture
    def migration(self, temp_db_url):
        """Create a migration instance for testing"""
        # Set required env vars
        os.environ['SMTP_USERNAME'] = 'test@example.com'
        os.environ['SMTP_PASSWORD'] = 'testpass'
        os.environ['EMAILS_FROM_EMAIL'] = 'test@example.com'
        
        return SupabaseMigration(temp_db_url, drop_all=True)
    
    def test_database_connection(self, migration):
        """Test database connection establishment"""
        migration.connect()
        assert migration.engine is not None
        assert migration.SessionLocal is not None
    
    def test_schema_creation(self, migration):
        """Test that all tables are created correctly"""
        migration.connect()
        migration.create_schema()
        
        # Check that all expected tables exist
        with migration.engine.connect() as conn:
            # Get all table names
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """))
            tables = {row[0] for row in result.fetchall()}
            
            # Expected core tables
            expected_tables = {
                'platform_users', 'organizations', 'users', 'companies',
                'vendors', 'customers', 'products', 'stock',
                'purchase_orders', 'purchase_order_items',
                'goods_receipt_notes', 'goods_receipt_note_items',
                'purchase_vouchers', 'purchase_voucher_items',
                'sales_orders', 'sales_order_items',
                'delivery_challans', 'delivery_challan_items',
                'sales_vouchers', 'sales_voucher_items',
                'quotations', 'quotation_items',
                'proforma_invoices', 'proforma_invoice_items',
                'credit_notes', 'credit_note_items',
                'debit_notes', 'debit_note_items',
                'payment_vouchers', 'receipt_vouchers',
                'purchase_returns', 'purchase_return_items',
                'sales_returns', 'sales_return_items',
                'audit_logs', 'email_notifications', 'payment_terms',
                'otp_verifications'
            }
            
            # Check all expected tables are present
            missing_tables = expected_tables - tables
            assert not missing_tables, f"Missing tables: {missing_tables}"
    
    def test_platform_admin_seeding(self, migration):
        """Test platform admin user creation"""
        migration.connect()
        migration.create_schema()
        migration.seed_platform_admin()
        
        db = migration.SessionLocal()
        try:
            # Check platform admin was created
            admin = db.query(PlatformUser).filter(
                PlatformUser.email == "naughtyfruit53@gmail.com"
            ).first()
            
            assert admin is not None
            assert admin.role == "super_admin"
            assert admin.is_active is True
            assert admin.full_name == "Platform Super Administrator"
        finally:
            db.close()
    
    def test_demo_data_seeding(self, migration):
        """Test demo data creation"""
        migration.connect()
        migration.create_schema()
        migration.seed_platform_admin()
        migration.seed_demo_data()
        
        db = migration.SessionLocal()
        try:
            # Check demo organization
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            assert demo_org is not None
            assert demo_org.name == "Demo Manufacturing Corp"
            
            # Check demo users
            admin_user = db.query(User).filter(
                User.email == "admin@demo-manufacturing.com",
                User.organization_id == demo_org.id
            ).first()
            assert admin_user is not None
            assert admin_user.role == "org_admin"
            
            regular_user = db.query(User).filter(
                User.email == "user@demo-manufacturing.com",
                User.organization_id == demo_org.id
            ).first()
            assert regular_user is not None
            assert regular_user.role == "standard_user"
            
            # Check demo data
            vendors = db.query(Vendor).filter(
                Vendor.organization_id == demo_org.id
            ).count()
            assert vendors > 0
            
            customers = db.query(Customer).filter(
                Customer.organization_id == demo_org.id
            ).count()
            assert customers > 0
            
            products = db.query(Product).filter(
                Product.organization_id == demo_org.id
            ).count()
            assert products > 0
            
            stock_entries = db.query(Stock).filter(
                Stock.organization_id == demo_org.id
            ).count()
            assert stock_entries > 0
            
        finally:
            db.close()
    
    def test_organization_level_isolation(self, migration):
        """Test that organization-level data isolation is enforced"""
        migration.connect()
        migration.create_schema()
        migration.seed_platform_admin()
        migration.seed_demo_data()
        
        db = migration.SessionLocal()
        try:
            # Get demo organization
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            
            # Create a second organization
            test_org = Organization(
                name="Test Organization",
                subdomain="test",
                status="active",
                business_type="Testing",
                primary_email="test@test.com",
                primary_phone="+1-555-0123",
                address1="123 Test Street",
                city="Test City",
                state="Test State",
                pin_code="12345",
                country="Test Country"
            )
            db.add(test_org)
            db.flush()
            
            # Add test data to second org
            test_vendor = Vendor(
                organization_id=test_org.id,
                name="Test Vendor",
                contact_number="+1-555-0124",
                email="vendor@test.com",
                address1="456 Test Avenue",
                city="Test City",
                state="Test State",
                pin_code="12345",
                state_code="TS"
            )
            db.add(test_vendor)
            db.commit()
            
            # Check isolation: demo org should not see test org's vendor
            demo_vendors = db.query(Vendor).filter(
                Vendor.organization_id == demo_org.id
            ).all()
            
            test_vendors = db.query(Vendor).filter(
                Vendor.organization_id == test_org.id
            ).all()
            
            # Ensure vendors are isolated by organization
            demo_vendor_names = {v.name for v in demo_vendors}
            test_vendor_names = {v.name for v in test_vendors}
            
            assert "Test Vendor" not in demo_vendor_names
            assert "Test Vendor" in test_vendor_names
            assert len(test_vendors) == 1
            
        finally:
            db.close()
    
    def test_voucher_relationships(self, migration):
        """Test voucher relationship constraints and auto-population support"""
        migration.connect()
        migration.create_schema()
        migration.seed_demo_data()
        
        db = migration.SessionLocal()
        try:
            # Get demo org and its data
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            
            vendor = db.query(Vendor).filter(
                Vendor.organization_id == demo_org.id
            ).first()
            
            product = db.query(Product).filter(
                Product.organization_id == demo_org.id
            ).first()
            
            user = db.query(User).filter(
                User.organization_id == demo_org.id
            ).first()
            
            # Create a purchase order
            po = PurchaseOrder(
                organization_id=demo_org.id,
                vendor_id=vendor.id,
                voucher_number="PO-2025-001",
                date=func.now(),
                total_amount=1000.0,
                status="confirmed",
                created_by=user.id
            )
            db.add(po)
            db.flush()
            
            # Add item to PO
            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=product.id,
                quantity=10.0,
                unit=product.unit,
                unit_price=product.unit_price,
                total_amount=10.0 * product.unit_price,
                pending_quantity=10.0
            )
            db.add(po_item)
            db.flush()
            
            # Create GRN linked to PO
            grn = GoodsReceiptNote(
                organization_id=demo_org.id,
                purchase_order_id=po.id,
                vendor_id=vendor.id,
                voucher_number="GRN-2025-001",
                date=func.now(),
                grn_date=func.now(),
                total_amount=800.0,
                status="confirmed",
                created_by=user.id
            )
            db.add(grn)
            db.flush()
            
            # Add GRN item linked to PO item
            grn_item = GoodsReceiptNoteItem(
                grn_id=grn.id,
                product_id=product.id,
                po_item_id=po_item.id,
                ordered_quantity=10.0,
                received_quantity=8.0,
                accepted_quantity=8.0,
                rejected_quantity=0.0,
                unit=product.unit,
                unit_price=product.unit_price,
                total_cost=8.0 * product.unit_price
            )
            db.add(grn_item)
            db.flush()
            
            # Create Purchase Voucher linked to GRN
            pv = PurchaseVoucher(
                organization_id=demo_org.id,
                vendor_id=vendor.id,
                purchase_order_id=po.id,
                grn_id=grn.id,
                voucher_number="PV-2025-001",
                date=func.now(),
                total_amount=800.0,
                status="confirmed",
                created_by=user.id
            )
            db.add(pv)
            db.flush()
            
            # Add PV item linked to GRN item
            pv_item = PurchaseVoucherItem(
                purchase_voucher_id=pv.id,
                grn_item_id=grn_item.id,
                product_id=product.id,
                quantity=8.0,
                unit=product.unit,
                unit_price=product.unit_price,
                taxable_amount=8.0 * product.unit_price,
                total_amount=8.0 * product.unit_price
            )
            db.add(pv_item)
            db.commit()
            
            # Verify relationships
            assert po.vendor.name == vendor.name
            assert grn.purchase_order.voucher_number == "PO-2025-001"
            assert pv.grn.voucher_number == "GRN-2025-001"
            assert pv_item.grn_item.grn_id == grn.id
            
            # Verify organization isolation
            assert po.organization_id == demo_org.id
            assert grn.organization_id == demo_org.id
            assert pv.organization_id == demo_org.id
            
        finally:
            db.close()
    
    def test_unique_constraints(self, migration):
        """Test unique constraints per organization"""
        migration.connect()
        migration.create_schema()
        migration.seed_demo_data()
        
        db = migration.SessionLocal()
        try:
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            
            # Try to create duplicate voucher number in same org (should fail)
            po1 = PurchaseOrder(
                organization_id=demo_org.id,
                vendor_id=1,
                voucher_number="PO-DUPLICATE-001",
                date=func.now(),
                total_amount=1000.0
            )
            db.add(po1)
            db.flush()
            
            po2 = PurchaseOrder(
                organization_id=demo_org.id,
                vendor_id=1,
                voucher_number="PO-DUPLICATE-001",  # Same voucher number
                date=func.now(),
                total_amount=2000.0
            )
            db.add(po2)
            
            # This should raise an integrity error
            with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
                db.commit()
                
        finally:
            db.close()
    
    def test_complete_migration_workflow(self, migration):
        """Test the complete migration workflow"""
        # Test full migration
        migration.run_migration(seed_demo=True)
        
        db = migration.SessionLocal()
        try:
            # Verify platform admin exists
            platform_admin = db.query(PlatformUser).filter(
                PlatformUser.email == "naughtyfruit53@gmail.com"
            ).first()
            assert platform_admin is not None
            
            # Verify demo org exists with all data
            demo_org = db.query(Organization).filter(
                Organization.subdomain == "demo"
            ).first()
            assert demo_org is not None
            
            # Verify all entity counts
            assert db.query(User).filter(User.organization_id == demo_org.id).count() >= 2
            assert db.query(Vendor).filter(Vendor.organization_id == demo_org.id).count() >= 1
            assert db.query(Customer).filter(Customer.organization_id == demo_org.id).count() >= 1
            assert db.query(Product).filter(Product.organization_id == demo_org.id).count() >= 3
            assert db.query(Stock).filter(Stock.organization_id == demo_org.id).count() >= 3
            
        finally:
            db.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])