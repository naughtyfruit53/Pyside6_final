#!/usr/bin/env python3
"""
Integration test for complete migration workflow
"""

import os
import sys
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_migration import SupabaseMigration
from app.models.base import *
from app.models.vouchers import *
from app.core.tenant import TenantQueryFilter, TenantContext
from app.services.voucher_service import VoucherNumberService

class TestCompleteMigrationWorkflow:
    """Test complete migration workflow with all components"""
    
    @pytest.fixture
    def migrated_db(self):
        """Setup migrated database with demo data"""
        # Set env vars
        os.environ['SMTP_USERNAME'] = 'test@example.com' 
        os.environ['SMTP_PASSWORD'] = 'testpass'
        os.environ['EMAILS_FROM_EMAIL'] = 'test@example.com'
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"
            
            # Run complete migration
            migration = SupabaseMigration(db_url, drop_all=True)
            migration.run_migration(seed_demo=True)
            
            # Create session
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
                try:
                    os.unlink(tmp.name)
                except:
                    pass
    
    def test_platform_admin_exists(self, migrated_db):
        """Verify platform admin was created"""
        platform_admin = migrated_db.query(PlatformUser).filter(
            PlatformUser.email == "naughtyfruit53@gmail.com"
        ).first()
        
        assert platform_admin is not None
        assert platform_admin.role == "super_admin"
        assert platform_admin.is_active is True
    
    def test_demo_organization_structure(self, migrated_db):
        """Verify demo organization structure"""
        demo_org = migrated_db.query(Organization).filter(
            Organization.subdomain == "demo"
        ).first()
        
        assert demo_org is not None
        assert demo_org.name == "Demo Manufacturing Corp"
        assert demo_org.status == "active"
        
        # Check users
        users = migrated_db.query(User).filter(
            User.organization_id == demo_org.id
        ).all()
        assert len(users) >= 2  # Admin and regular user
        
        # Check vendors
        vendors = migrated_db.query(Vendor).filter(
            Vendor.organization_id == demo_org.id
        ).all()
        assert len(vendors) >= 1
        
        # Check products
        products = migrated_db.query(Product).filter(
            Product.organization_id == demo_org.id
        ).all()
        assert len(products) >= 3  # Steel Rod, Bearing, Motor
        
        # Check stock
        stock_entries = migrated_db.query(Stock).filter(
            Stock.organization_id == demo_org.id
        ).all()
        assert len(stock_entries) >= 3
    
    def test_organization_data_isolation(self, migrated_db):
        """Test strict organization data isolation"""
        demo_org = migrated_db.query(Organization).filter(
            Organization.subdomain == "demo"
        ).first()
        
        # Create second organization
        test_org = Organization(
            name="Test Organization",
            subdomain="test",
            status="active",
            business_type="Testing",
            primary_email="test@test.com",
            primary_phone="+1-555-TEST",
            address1="Test Address",
            city="Test City",
            state="Test State", 
            pin_code="00000",
            country="Test Country"
        )
        migrated_db.add(test_org)
        migrated_db.flush()
        
        # Add test vendor to second org
        test_vendor = Vendor(
            organization_id=test_org.id,
            name="Test Vendor",
            contact_number="+1-555-VENDOR",
            email="vendor@test.com",
            address1="Test Vendor Address",
            city="Test City",
            state="Test State",
            pin_code="00000",
            state_code="TS"
        )
        migrated_db.add(test_vendor)
        migrated_db.commit()
        
        # Test isolation: demo org query should not see test org vendor
        demo_vendors = TenantQueryFilter.apply_organization_filter(
            migrated_db.query(Vendor), Vendor, demo_org.id
        ).all()
        
        test_vendors = TenantQueryFilter.apply_organization_filter(
            migrated_db.query(Vendor), Vendor, test_org.id
        ).all()
        
        # Verify isolation
        demo_vendor_names = {v.name for v in demo_vendors}
        test_vendor_names = {v.name for v in test_vendors}
        
        assert "Test Vendor" not in demo_vendor_names
        assert "Test Vendor" in test_vendor_names
        assert len(test_vendors) == 1
    
    def test_voucher_number_generation(self, migrated_db):
        """Test voucher number generation service"""
        demo_org = migrated_db.query(Organization).filter(
            Organization.subdomain == "demo"
        ).first()
        
        # Generate first PO number
        po1_number = VoucherNumberService.generate_voucher_number(
            migrated_db, "PO", demo_org.id, PurchaseOrder
        )
        
        # Create actual PO to persist the number
        po1 = PurchaseOrder(
            organization_id=demo_org.id,
            vendor_id=1,
            voucher_number=po1_number,
            date=func.now(),
            total_amount=100.0
        )
        migrated_db.add(po1)
        migrated_db.commit()
        
        # Generate second PO number
        po2_number = VoucherNumberService.generate_voucher_number(
            migrated_db, "PO", demo_org.id, PurchaseOrder
        )
        
        assert po1_number.startswith(f"PO-2025-{demo_org.id}-")
        assert po2_number.startswith(f"PO-2025-{demo_org.id}-")
        assert po1_number != po2_number
        
        # Verify format: PO-YEAR-ORG-SEQUENCE
        parts1 = po1_number.split('-')
        assert len(parts1) == 4
        assert parts1[0] == "PO"
        assert parts1[1] == "2025"
        assert parts1[2] == str(demo_org.id)
        assert parts1[3] == "001"
        
        parts2 = po2_number.split('-')
        assert parts2[3] == "002"
    
    def test_complete_purchase_workflow(self, migrated_db):
        """Test complete purchase workflow: PO → GRN → Purchase Voucher"""
        demo_org = migrated_db.query(Organization).filter(
            Organization.subdomain == "demo"
        ).first()
        
        vendor = migrated_db.query(Vendor).filter(
            Vendor.organization_id == demo_org.id
        ).first()
        
        product = migrated_db.query(Product).filter(
            Product.organization_id == demo_org.id
        ).first()
        
        user = migrated_db.query(User).filter(
            User.organization_id == demo_org.id
        ).first()
        
        # 1. Create Purchase Order
        po_number = VoucherNumberService.generate_voucher_number(
            migrated_db, "PO", demo_org.id, PurchaseOrder
        )
        
        po = PurchaseOrder(
            organization_id=demo_org.id,
            vendor_id=vendor.id,
            voucher_number=po_number,
            date=func.now(),
            total_amount=1000.0,
            status="confirmed",
            created_by=user.id
        )
        migrated_db.add(po)
        migrated_db.flush()
        
        # Add PO item
        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product.id,
            quantity=10.0,
            unit=product.unit,
            unit_price=product.unit_price,
            total_amount=10.0 * product.unit_price,
            pending_quantity=10.0
        )
        migrated_db.add(po_item)
        migrated_db.flush()
        
        # 2. Create GRN from PO
        grn_number = VoucherNumberService.generate_voucher_number(
            migrated_db, "GRN", demo_org.id, GoodsReceiptNote
        )
        
        grn = GoodsReceiptNote(
            organization_id=demo_org.id,
            purchase_order_id=po.id,
            vendor_id=vendor.id,
            voucher_number=grn_number,
            date=func.now(),
            grn_date=func.now(),
            total_amount=800.0,
            status="confirmed",
            created_by=user.id
        )
        migrated_db.add(grn)
        migrated_db.flush()
        
        # Add GRN item
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
        migrated_db.add(grn_item)
        
        # Update PO item quantities
        po_item.delivered_quantity = 8.0
        po_item.pending_quantity = 2.0
        
        migrated_db.flush()
        
        # 3. Create Purchase Voucher from GRN
        pv_number = VoucherNumberService.generate_voucher_number(
            migrated_db, "PV", demo_org.id, PurchaseVoucher
        )
        
        pv = PurchaseVoucher(
            organization_id=demo_org.id,
            vendor_id=vendor.id,
            purchase_order_id=po.id,
            grn_id=grn.id,
            voucher_number=pv_number,
            date=func.now(),
            total_amount=944.0,  # 800 + 18% GST
            cgst_amount=72.0,
            sgst_amount=72.0,
            status="confirmed",
            created_by=user.id
        )
        migrated_db.add(pv)
        migrated_db.flush()
        
        # Add PV item
        pv_item = PurchaseVoucherItem(
            purchase_voucher_id=pv.id,
            grn_item_id=grn_item.id,
            product_id=product.id,
            quantity=8.0,
            unit=product.unit,
            unit_price=product.unit_price,
            taxable_amount=800.0,
            gst_rate=18.0,
            cgst_amount=72.0,
            sgst_amount=72.0,
            total_amount=944.0
        )
        migrated_db.add(pv_item)
        migrated_db.commit()
        
        # 4. Verify workflow relationships
        assert po.vendor.name == vendor.name
        assert grn.purchase_order.voucher_number == po.voucher_number
        assert pv.grn.voucher_number == grn.voucher_number
        assert pv_item.grn_item.grn_id == grn.id
        
        # Verify organization isolation throughout workflow
        assert po.organization_id == demo_org.id
        assert grn.organization_id == demo_org.id
        assert pv.organization_id == demo_org.id
        
        # Verify quantity tracking
        assert po_item.delivered_quantity == 8.0
        assert po_item.pending_quantity == 2.0
        assert grn_item.accepted_quantity == 8.0
        assert pv_item.quantity == 8.0
    
    def test_unique_constraints_per_organization(self, migrated_db):
        """Test unique constraints are enforced per organization"""
        demo_org = migrated_db.query(Organization).filter(
            Organization.subdomain == "demo"
        ).first()
        
        # Try to create duplicate vendor name (should fail)
        existing_vendor = migrated_db.query(Vendor).filter(
            Vendor.organization_id == demo_org.id
        ).first()
        
        duplicate_vendor = Vendor(
            organization_id=demo_org.id,
            name=existing_vendor.name,  # Same name
            contact_number="+1-555-DUP",
            email="duplicate@test.com",
            address1="Duplicate Address",
            city="Duplicate City",
            state="Duplicate State",
            pin_code="99999",
            state_code="DS"
        )
        migrated_db.add(duplicate_vendor)
        
        # Should raise integrity error
        with pytest.raises(Exception):
            migrated_db.commit()
        
        migrated_db.rollback()
    
    def test_migration_completeness(self, migrated_db):
        """Test that migration created all expected tables and relationships"""
        # Check critical tables exist and have data
        assert migrated_db.query(PlatformUser).count() >= 1
        assert migrated_db.query(Organization).count() >= 1
        assert migrated_db.query(User).count() >= 2
        assert migrated_db.query(Vendor).count() >= 1
        assert migrated_db.query(Product).count() >= 3
        assert migrated_db.query(Stock).count() >= 3
        
        # Verify relationships work
        demo_org = migrated_db.query(Organization).first()
        assert len(demo_org.users) >= 2
        assert len(demo_org.vendors) >= 1
        assert len(demo_org.products) >= 3
        
        # Check all foreign keys are properly set
        for vendor in demo_org.vendors:
            assert vendor.organization_id == demo_org.id
        
        for product in demo_org.products:
            assert product.organization_id == demo_org.id
        
        for stock in demo_org.stock_entries:
            assert stock.organization_id == demo_org.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])