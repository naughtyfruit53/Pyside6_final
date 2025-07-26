# src/erp/logic/database/schema.py
# Modified to use SQLAlchemy for table creation and verification. Removed direct SQL schemas, as they are now in models.py.
# Also handle indexes via SQLAlchemy's Index if possible, but for custom ones, execute raw SQL.

import os
import logging
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path  # Updated to get_database_url
from src.erp.logic.database.models import Base  # Import Base from new models.py
from src.erp.logic.database.voucher import initialize_voucher_tables, initialize_vouchers

log_dir = os.path.dirname(get_log_path())
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define indexes here since some are custom (e.g., LOWER(name))
INDEXES = [
    text("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_name_lower ON products (LOWER(name))"),
    text("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendors_name_lower ON vendors (LOWER(name))"),
    text("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_name_lower ON customers (LOWER(name))"),
    text("CREATE UNIQUE INDEX IF NOT EXISTS idx_default_directory_path ON default_directory (directory_path)"),
    text("CREATE INDEX IF NOT EXISTS idx_material_transactions_type ON material_transactions (type)"),
    text("CREATE INDEX IF NOT EXISTS idx_material_transactions_doc_number ON material_transactions (doc_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_material_transactions_delivery_challan_number ON material_transactions (delivery_challan_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_material_transactions_product_id ON material_transactions (product_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_purchase_orders_po_number ON purchase_orders (po_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_purchase_orders_vendor_id ON purchase_orders (vendor_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_po_items_po_id ON po_items (po_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_grn_grn_number ON grn (grn_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_grn_po_id ON grn (po_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_grn_items_grn_id ON grn_items (grn_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_stock_product_id ON stock (product_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_rejections_grn_id ON rejections (grn_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_credit_notes_cn_number ON credit_notes (cn_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_credit_notes_vendor_id ON credit_notes (vendor_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_cn_items_cn_id ON cn_items (cn_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_purchase_inv_pur_inv_number ON purchase_inv (pur_inv_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_purchase_inv_vendor_id ON purchase_inv (vendor_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_pur_inv_items_pur_inv_id ON purchase_inv_items (pur_inv_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_invoices_sales_inv_number ON sales_invoices (sales_inv_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_invoices_customer_id ON sales_invoices (customer_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_invoices_sales_order_id ON sales_invoices (sales_order_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_inv_items_sales_inv_id ON sales_inv_items (sales_inv_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_quotes_quotation_number ON quotes (quotation_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_quotes_customer_id ON quotes (customer_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON quote_items (quote_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_bom_manufactured_product_id ON bom (manufactured_product_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_bom_components_bom_id ON bom_components (bom_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_work_orders_bom_id ON work_orders (bom_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_orders_sales_order_number ON sales_orders (sales_order_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_orders_customer_id ON sales_orders (customer_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_sales_order_items_sales_order_id ON sales_order_items (sales_order_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_proforma_invoices_proforma_number ON proforma_invoices (proforma_number)"),
    text("CREATE INDEX IF NOT EXISTS idx_proforma_invoices_customer_id ON proforma_invoices (customer_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_proforma_invoices_quotation_id ON proforma_invoices (quotation_id)"),
    text("CREATE INDEX IF NOT EXISTS idx_proforma_invoice_items_proforma_id ON proforma_invoice_items (proforma_id)"),
]

def create_tables_and_indexes():
    try:
        Base.metadata.create_all(engine)
        with engine.connect() as conn:
            for index in INDEXES:
                try:
                    conn.execute(index)
                    logger.debug(f"Created index: {index}")
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
            # Removed PRAGMA foreign_keys (PostgreSQL enforces via schema).
            # Removed integrity_check (use PostgreSQL's \dt or manual checks if needed).
        logger.debug("Tables and indexes created or verified successfully")
    except Exception as e:
        logger.error(f"Failed to create tables and indexes: {e}")
        raise

def verify_voucher_columns_schema():
    required_columns = {
        "credit_notes": ["id", "cn_number", "grn_id", "po_id", "vendor_id", "cn_date", "total_amount", "cgst_amount", "sgst_amount", "igst_amount", "created_at", "voucher_type_id"],
        "cn_items": ["id", "cn_id", "product_id", "quantity", "unit", "unit_price", "gst_rate", "amount"],
        "purchase_inv": ["id", "pur_inv_number", "invoice_number", "invoice_date", "grn_id", "po_id", "vendor_id", "pur_inv_date", "total_amount", "cgst_amount", "sgst_amount", "igst_amount", "created_at", "voucher_type_id"],
        "purchase_inv_items": ["id", "pur_inv_id", "product_id", "quantity", "unit", "unit_price", "gst_rate", "amount"],
        "sales_invoices": ["id", "sales_inv_number", "invoice_date", "sales_order_id", "customer_id", "total_amount", "cgst_amount", "sgst_amount", "igst_amount", "created_at", "voucher_type_id", "voucher_data"],
        "sales_inv_items": ["id", "sales_inv_id", "product_id", "quantity", "unit", "unit_price", "gst_rate", "amount"],
        "quotes": ["id", "quotation_number", "customer_id", "quotation_date", "validity_date", "total_amount", "cgst_amount", "sgst_amount", "igst_amount", "is_deleted", "payment_terms", "voucher_type_id"],
        "quote_items": ["id", "quote_id", "product_id", "quantity", "unit", "unit_price", "gst_rate", "amount"],
        "proforma_invoices": ["id", "proforma_number", "quotation_id", "customer_id", "proforma_date", "validity_date", "total_amount", "cgst_amount", "sgst_amount", "igst_amount", "is_deleted", "payment_terms", "voucher_type_id"],
        "proforma_invoice_items": ["id", "proforma_id", "product_id", "quantity", "unit", "unit_price", "gst_rate", "amount"]
    }
    try:
        metadata = Base.metadata
        for table, expected_columns in required_columns.items():
            if table in metadata.tables:
                actual_columns = [col.name for col in metadata.tables[table].columns]
                if not all(col in actual_columns for col in expected_columns):
                    missing = [col for col in expected_columns if col not in actual_columns]
                    logger.error(f"Table {table} missing columns: {missing}")
                    raise ValueError(f"Table {table} missing columns: {missing}")
                logger.debug(f"Verified schema for table {table}")
    except Exception as e:
        logger.error(f"Failed to verify columns: {e}")
        raise

def initialize_database():
    """Initialize the PostgreSQL database and create necessary tables."""
    logger.debug("Initializing PostgreSQL database")
    try:
        create_tables_and_indexes()
        initialize_voucher_tables()
        initialize_vouchers()
        verify_voucher_columns_schema()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise