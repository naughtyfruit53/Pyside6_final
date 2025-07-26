# src/erp/logic/database/voucher.py
# Modified to use SQLAlchemy. Removed VOUCHER_TABLE_SCHEMAS as they are in models.py.
# Use session.query, add, etc., for all operations.

import logging
import json
import os
from sqlalchemy import text
from sqlalchemy import func
from src.erp.logic.database.session import engine, Session
from sqlalchemy.exc import SQLAlchemyError
from src.core.config import get_database_url, get_log_path  # Updated to get_database_url
from src.erp.logic.utils.utils import suggest_calculation_logic, suggest_data_type
from src.erp.logic.utils.sequence_utils import get_next_doc_sequence, commit_doc_sequence, get_fiscal_year
from src.erp.logic.database.models import Base, VoucherType, VoucherColumn, VoucherInstance, VoucherSequence

# Ensure log directory exists
log_dir = os.path.dirname(get_log_path())
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VOUCHER_TYPES = [
    "Purchase Voucher", "GRN (Goods Received Note)", "Debit Note", "Purchase Order", "Sales Voucher", "Proforma Invoice", "Delivery Challan",
    "Credit Note", "Non-Sales Credit Note", "Sales Order", "Quotation",
    "Payment Voucher", "Receipt Voucher", "Contra Voucher", "Journal Voucher",
    "Rejection In", "Rejection Out", "Inter Department Voucher"
]

MODULE_VOUCHER_TYPES = {
    "purchase": ["Purchase Order", "GRN (Goods Received Note)", "Debit Note", "Purchase Voucher", "Rejection In"],
    "sales": ["Sales Voucher", "Proforma Invoice", "Delivery Challan", "Credit Note", "Non-Sales Credit Note", "Sales Order", "Quotation", "Rejection Out"],
    "financial": ["Payment Voucher", "Receipt Voucher", "Contra Voucher", "Journal Voucher"],
    "internal": ["Inter Department Voucher"],
    "inward": ["GRN (Goods Received Note)", "Rejection In"],
    "outward": ["Delivery Challan", "Rejection Out"]
}

item_based_vouchers = [
    "Sales Voucher", "Purchase Voucher", "Proforma Invoice",
    "Delivery Challan", "Quotation", "Purchase Order", "Sales Order",
    "GRN (Goods Received Note)", "Rejection In", "Rejection Out", "Internal Return"  # Added GRN and others for consistency
]

PRODUCT_COLUMNS = [
    ("Name", "TEXT", True, 1, False, None),
    ("HSN Code", "TEXT", False, 2, False, None),
    ("Qty", "REAL", True, 3, False, None),
    ("Unit", "TEXT", True, 4, False, None),
    ("Unit Price", "REAL", True, 5, False, None),
    ("GST Rate", "REAL", False, 6, False, None),
    ("Amount", "REAL", True, 7, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Qty"], "output": "Amount"}))
]

PRODUCT_VOUCHER_COLUMNS = [
    "Discount Amount", "Tax Amount", "GST Rate", "CGST Amount", "SGST Amount",
    "IGST Amount", "Batch Number", "TDS Amount", "Freight Charges", "E-Way Bill Number",
    "Serial Number", "Expiry Date"
]

VOUCHER_COLUMNS = [
    "Voucher Number", "Voucher Date", "Due Date", "Reference Number", "Party Name",
    "Ledger Account", "Item Description", "Item Code", "HSN/SAC Code", "Quantity",
    "Unit of Measure", "Unit Price", "Total Amount", "Discount Percentage", "Discount Amount",
    "Tax Rate", "Tax Amount", "CGST Amount", "SGST Amount", "IGST Amount", "Cess Amount",
    "GSTIN", "Narration", "Payment Terms", "Shipping Address", "Billing Address",
    "Place of Supply", "Terms and Conditions", "Round Off", "Net Amount", "Freight Charges",
    "Packing Charges", "Insurance Charges", "Batch Number", "Expiry Date", "Serial Number",
    "Warranty Period", "E-Way Bill Number", "Transport Mode", "Vehicle Number", "LR/RR Number",
    "PO Number", "GRN Number", "Invoice Number", "Credit Period", "TDS Amount", "TCS Amount",
    "Cost Center", "Project Code", "Currency", "Exchange Rate", "Bank Details", "Reverse Charge",
    "Export Type", "Port Code", "Shipping Bill Number", "Country of Origin"
]

VOUCHER_INDEXES = {
    "voucher_types": [text("CREATE INDEX IF NOT EXISTS idx_voucher_types_type_code ON voucher_types (type_code)")],
    "voucher_columns": [text("CREATE INDEX IF NOT EXISTS idx_voucher_columns_voucher_type_id ON voucher_columns (voucher_type_id)")],
    "voucher_instances": [
        text("CREATE INDEX IF NOT EXISTS idx_voucher_instances_voucher_number ON voucher_instances (voucher_number)"),
        text("CREATE INDEX IF NOT EXISTS idx_voucher_instances_voucher_type_id ON voucher_instances (voucher_type_id)")
    ],
    "voucher_sequence": [text("CREATE INDEX IF NOT EXISTS idx_voucher_sequence_voucher_type_id ON voucher_sequence (voucher_type_id)")]
}

VOUCHER_DEFINITIONS = {
    "Purchase Voucher": {
        "type_code": "PURCHASE_VOUCHER",
        "category": "purchase",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Supplier Name", "TEXT", True, 3, False, None),
            ("Supplier GSTIN", "TEXT", False, 4, False, None),
            ("Item Name", "TEXT", True, 5, False, None),
            ("HSN/SAC Code", "TEXT", False, 6, False, None),
            ("Quantity", "REAL", True, 7, False, None),
            ("Unit Price", "REAL", True, 8, False, None),
            ("Discount Amount", "REAL", False, 9, False, None),
            ("Tax Rate", "REAL", False, 10, False, None),
            ("Tax Amount", "REAL", False, 11, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 12, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Discount Amount", "Tax Amount"], "output": "Total Amount"})),
            ("Payment Terms", "TEXT", False, 13, False, None),
            ("Mode of Payment", "TEXT", False, 14, False, None),
            ("Purchase Order Reference", "TEXT", False, 15, False, None),
            ("Narration", "TEXT", False, 16, False, None)
        ]
    },
    "GRN (Goods Received Note)": {
        "type_code": "GRN",
        "category": "purchase",
        "is_active": 1,
        "columns": [
            ("GRN No", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Supplier Name", "TEXT", True, 3, False, None),
            ("PO Reference", "TEXT", True, 4, False, None),
            ("Item Name", "TEXT", True, 5, False, None),
            ("Quantity Received", "REAL", True, 6, False, None),
            ("Quantity Accepted", "REAL", True, 7, False, None),
            ("Quantity Rejected", "REAL", False, 8, False, None),
            ("Unit Price", "REAL", True, 9, False, None),
            ("Store Location", "TEXT", False, 10, False, None),
            ("Narration", "TEXT", False, 11, False, None)
        ]
    },
    "Debit Note": {
        "type_code": "DEBIT_NOTE",
        "category": "financial",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Supplier Name", "TEXT", True, 3, False, None),
            ("Original Invoice Reference", "TEXT", True, 4, False, None),
            ("Item(s) Returned", "TEXT", True, 5, False, None),
            ("Quantity", "REAL", True, 6, False, None),
            ("Unit Price", "REAL", True, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Narration", "TEXT", False, 10, False, None)
        ]
    },
    "Purchase Order": {
        "type_code": "PURCHASE_ORDER",
        "category": "purchase",
        "is_active": 1,
        "columns": [
            ("PO Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Supplier Name", "TEXT", True, 3, False, None),
            ("Item Name", "TEXT", True, 4, False, None),
            ("Quantity", "REAL", True, 5, False, None),
            ("Unit Price", "REAL", True, 6, False, None),
            ("Tax Rate", "REAL", False, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Delivery Date", "DATE", False, 10, False, None),
            ("Payment Terms", "TEXT", False, 11, False, None),
            ("Narration", "TEXT", False, 12, False, None)
        ]
    },
    "Sales Voucher": {
        "type_code": "SALES_VOUCHER",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Customer GSTIN", "TEXT", False, 4, False, None),
            ("Item Name", "TEXT", True, 5, False, None),
            ("HSN/SAC Code", "TEXT", False, 6, False, None),
            ("Quantity", "REAL", True, 7, False, None),
            ("Unit Price", "REAL", True, 8, False, None),
            ("Discount Amount", "REAL", False, 9, False, None),
            ("Tax Rate", "REAL", False, 10, False, None),
            ("Tax Amount", "REAL", False, 11, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 12, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Discount Amount", "Tax Amount"], "output": "Total Amount"})),
            ("Payment Terms", "TEXT", False, 13, False, None),
            ("Narration", "TEXT", False, 14, False, None)
        ]
    },
    "Proforma Invoice": {
        "type_code": "PROFORMA_INVOICE",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Proforma Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Item Name", "TEXT", True, 4, False, None),
            ("Quantity", "REAL", True, 5, False, None),
            ("Unit Price", "REAL", True, 6, False, None),
            ("Tax Rate", "REAL", False, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Validity Date", "DATE", False, 10, False, None),
            ("Narration", "TEXT", False, 11, False, None)
        ]
    },
    "Delivery Challan": {
        "type_code": "DELIVERY_CHALLAN",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Challan Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Item Name", "TEXT", True, 4, False, None),
            ("Quantity", "REAL", True, 5, False, None),
            ("Unit Price", "REAL", True, 6, False, None),
            ("Narration", "TEXT", False, 7, False, None)
        ]
    },
    "Credit Note": {
        "type_code": "CREDIT_NOTE",
        "category": "financial",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Original Invoice Reference", "TEXT", True, 4, False, None),
            ("Item(s) Returned", "TEXT", True, 5, False, None),
            ("Quantity", "REAL", True, 6, False, None),
            ("Unit Price", "REAL", True, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Narration", "TEXT", False, 10, False, None)
        ]
    },
    "Non-Sales Credit Note": {
        "type_code": "NON_SALES_CREDIT_NOTE",
        "category": "financial",
        "is_active": 0,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Reason", "TEXT", True, 4, False, None),
            ("Total Amount", "REAL", True, 5, False, None),
            ("Narration", "TEXT", False, 6, False, None)
        ]
    },
    "Sales Order": {
        "type_code": "SALES_ORDER",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Sales Order Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Item Name", "TEXT", True, 4, False, None),
            ("Quantity", "REAL", True, 5, False, None),
            ("Unit Price", "REAL", True, 6, False, None),
            ("Tax Rate", "REAL", False, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Delivery Date", "DATE", False, 10, False, None),
            ("Payment Terms", "TEXT", False, 11, False, None),
            ("Narration", "TEXT", False, 12, False, None)
        ]
    },
    "Quotation": {
        "type_code": "QUOTATION",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Quotation Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Item Name", "TEXT", True, 4, False, None),
            ("Quantity", "REAL", True, 5, False, None),
            ("Unit Price", "REAL", True, 6, False, None),
            ("Tax Rate", "REAL", False, 7, False, None),
            ("Tax Amount", "REAL", False, 8, True, json.dumps({"type": "tax_amount", "inputs": ["Unit Price", "Quantity", "Tax Rate"], "output": "Tax Amount"})),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Unit Price", "Quantity", "Tax Amount"], "output": "Total Amount"})),
            ("Validity Date", "DATE", False, 10, False, None),
            ("Narration", "TEXT", False, 11, False, None)
        ]
    },
    "Payment Voucher": {
        "type_code": "PAYMENT_VOUCHER",
        "category": "financial",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Payee Name", "TEXT", True, 3, False, None),
            ("Amount", "REAL", True, 4, False, None),
            ("Mode of Payment", "TEXT", False, 5, False, None),
            ("Reference", "TEXT", False, 6, False, None),
            ("Narration", "TEXT", False, 7, False, None)
        ]
    },
    "Receipt Voucher": {
        "type_code": "RECEIPT_VOUCHER",
        "category": "financial",
        "is_active": 0,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Payer Name", "TEXT", True, 3, False, None),
            ("Amount", "REAL", True, 4, False, None),
            ("Mode of Payment", "TEXT", False, 5, False, None),
            ("Reference", "TEXT", False, 6, False, None),
            ("Narration", "TEXT", False, 7, False, None)
        ]
    },
    "Contra Voucher": {
        "type_code": "CONTRA_VOUCHER",
        "category": "financial",
        "is_active": 0,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Account From", "TEXT", True, 3, False, None),
            ("Account To", "TEXT", True, 4, False, None),
            ("Amount", "REAL", True, 5, False, None),
            ("Narration", "TEXT", False, 6, False, None)
        ]
    },
    "Journal Voucher": {
        "type_code": "JOURNAL_VOUCHER",
        "category": "financial",
        "is_active": 0,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Debit Account", "TEXT", True, 3, False, None),
            ("Credit Account", "TEXT", True, 4, False, None),
            ("Amount", "REAL", True, 5, False, None),
            ("Narration", "TEXT", False, 6, False, None)
        ]
    },
    "Rejection In": {
        "type_code": "REJECTION_IN",
        "category": "purchase",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Supplier Name", "TEXT", True, 3, False, None),
            ("GRN Reference", "TEXT", True, 4, False, None),
            ("Item Name", "TEXT", True, 5, False, None),
            ("Quantity Rejected", "REAL", True, 6, False, None),
            ("Unit Price", "REAL", True, 7, False, None),
            ("Reason for Rejection", "TEXT", False, 8, False, None),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Quantity Rejected", "Unit Price"], "output": "Total Amount"})),
            ("Narration", "TEXT", False, 10, False, None)
        ]
    },
    "Rejection Out": {
        "type_code": "REJECTION_OUT",
        "category": "sales",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("Customer Name", "TEXT", True, 3, False, None),
            ("Delivery Challan Reference", "TEXT", True, 4, False, None),
            ("Item Name", "TEXT", True, 5, False, None),
            ("Quantity Rejected", "REAL", True, 6, False, None),
            ("Unit Price", "REAL", True, 7, False, None),
            ("Reason for Rejection", "TEXT", False, 8, False, None),
            ("Total Amount", "REAL", True, 9, True, json.dumps({"type": "net_amount", "inputs": ["Quantity Rejected", "Unit Price"], "output": "Total Amount"})),
            ("Narration", "TEXT", False, 10, False, None)
        ]
    },
    "Inter Department Voucher": {
        "type_code": "INTER_DEPARTMENT_VOUCHER",
        "category": "internal",
        "is_active": 1,
        "columns": [
            ("Voucher Number", "TEXT", True, 1, False, None),
            ("Date", "DATE", True, 2, False, None),
            ("From Department", "TEXT", True, 3, False, None),
            ("To Department", "TEXT", True, 4, False, None),
            ("Amount", "REAL", True, 5, False, None),
            ("Narration", "TEXT", False, 6, False, None)
        ]
    }
}

def initialize_voucher_tables():
    """Initialize voucher-related tables in the database."""
    try:
        Base.metadata.create_all(engine)  # This creates all tables, but since voucher tables are in Base, it's fine
        with engine.connect() as conn:
            for table_name, index_sqls in VOUCHER_INDEXES.items():
                for index_sql in index_sqls:
                    try:
                        conn.execute(index_sql)
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.error(f"Failed to create index for {table_name}: {e}")
        logger.info("Voucher tables and indexes initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize voucher tables: {e}")
        raise

def initialize_vouchers():
    """Initialize voucher types and their columns in the database."""
    session = Session()
    try:
        for voucher_name in VOUCHER_TYPES:
            if voucher_name not in VOUCHER_DEFINITIONS:
                logger.warning(f"Voucher type {voucher_name} not in VOUCHER_DEFINITIONS, skipping")
                continue
            details = VOUCHER_DEFINITIONS[voucher_name]
            type_code = details["type_code"]
            category = details["category"]
            is_active = details["is_active"]
            existing = session.query(VoucherType).filter_by(voucher_name=voucher_name).first()
            if not existing:
                session.add(VoucherType(
                    voucher_name=voucher_name,
                    type_code=type_code,
                    category=category,
                    is_active=is_active
                ))
        session.commit()
        logger.info("Voucher types initialized successfully")
        initialize_voucher_columns()
        verify_voucher_columns_schema()
        logger.info("Vouchers fully initialized")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to initialize vouchers: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in initialize_vouchers: {e}")
        raise
    finally:
        session.close()

def verify_voucher_columns_schema():
    """Verify that voucher columns in the database match VOUCHER_DEFINITIONS."""
    session = Session()
    try:
        for voucher_name, details in VOUCHER_DEFINITIONS.items():
            type_code = details["type_code"]
            voucher_type = session.query(VoucherType).filter_by(type_code=type_code).first()
            if not voucher_type:
                logger.error(f"Skipping voucher {voucher_name} due to missing voucher_type_id")
                continue
            voucher_type_id = voucher_type.id
            db_columns = session.query(VoucherColumn).filter_by(voucher_type_id=voucher_type_id).order_by(VoucherColumn.display_order).all()
            expected_columns = details["columns"]
            if len(db_columns) != len(expected_columns):
                logger.warning(f"Column count mismatch for {voucher_name}: expected {len(expected_columns)}, found {len(db_columns)}")
                session.query(VoucherColumn).filter_by(voucher_type_id=voucher_type_id).delete()
                for column in expected_columns:
                    session.add(VoucherColumn(
                        voucher_type_id=voucher_type_id,
                        column_name=column[0],
                        data_type=column[1],
                        is_mandatory=column[2],
                        display_order=column[3],
                        is_calculated=column[4],
                        calculation_logic=column[5]
                    ))
                logger.info(f"Corrected voucher columns for {voucher_name}")
            else:
                for db_col, exp_col in zip(db_columns, expected_columns):
                    if (db_col.column_name, db_col.data_type, db_col.is_mandatory, db_col.display_order, db_col.is_calculated, db_col.calculation_logic) != exp_col:
                        logger.warning(f"Column mismatch for {voucher_name}: {db_col.column_name} vs {exp_col[0]}")
                        db_col.column_name = exp_col[0]
                        db_col.data_type = exp_col[1]
                        db_col.is_mandatory = exp_col[2]
                        db_col.display_order = exp_col[3]
                        db_col.is_calculated = exp_col[4]
                        db_col.calculation_logic = exp_col[5]
                        logger.info(f"Updated column {db_col.column_name} for {voucher_name}")
        session.commit()
        logger.info("Voucher columns schema verified and corrected if necessary")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to verify voucher columns schema: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in verify_voucher_columns_schema: {e}")
        raise
    finally:
        session.close()

def get_voucher_type_id(voucher_name):
    """Retrieve the voucher type ID for a given voucher name or type code."""
    session = Session()
    try:
        if isinstance(voucher_name, int):
            return voucher_name
        voucher_type = session.query(VoucherType).filter(
            (func.lower(VoucherType.type_code) == func.lower(voucher_name)) |
            (func.lower(VoucherType.voucher_name) == func.lower(voucher_name))
        ).first()
        if voucher_type:
            logger.debug(f"Found voucher type ID {voucher_type.id} for voucher_name {voucher_name}")
            return voucher_type.id
        available_types = session.query(VoucherType.voucher_name, VoucherType.type_code).all()
        logger.error(f"Voucher type code or name '{voucher_name}' not found. Available types: {available_types}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Failed to get voucher type ID for {voucher_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_voucher_type_id for {voucher_name}: {e}")
        return None
    finally:
        session.close()

def get_voucher_types(category=None, is_active=None):
    """Retrieve all voucher types, optionally filtered by category and/or is_active status."""
    session = Session()
    try:
        query = session.query(VoucherType.id, VoucherType.voucher_name, VoucherType.type_code, VoucherType.category, VoucherType.is_active)
        if category:
            query = query.filter(VoucherType.category == category)
        if is_active is not None:
            query = query.filter(VoucherType.is_active == is_active)
        query = query.order_by(VoucherType.voucher_name)
        voucher_types = query.all()
        logger.debug(f"Retrieved {len(voucher_types)} voucher types with category={category}, is_active={is_active}")
        return voucher_types
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve voucher types: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_voucher_types: {e}")
        return None
    finally:
        session.close()

def get_voucher_types_by_module(module):
    session = Session()
    try:
        voucher_names = session.query(VoucherType.voucher_name).filter_by(category=module).all()
        return [row[0] for row in voucher_names]
    except SQLAlchemyError as e:
        logger.error(f"Failed to get voucher types for module {module}: {e}")
        return []
    finally:
        session.close()

def get_default_voucher_type_id_for_module(module_name):
    """Get the default voucher type ID for a given module."""
    try:
        default_voucher_types = {
            "purchase": "PURCHASE_VOUCHER",
            "sales": "SALES_VOUCHER",
            "financial": "PAYMENT_VOUCHER"
        }
        if module_name not in default_voucher_types:
            logger.error(f"No default voucher type defined for module {module_name}")
            return None
        type_code = default_voucher_types[module_name]
        voucher_type_id = get_voucher_type_id(type_code)
        if voucher_type_id:
            logger.debug(f"Found default voucher type ID {voucher_type_id} for module {module_name} (type_code: {type_code})")
            return voucher_type_id
        logger.error(f"Default voucher type {type_code} not found for module {module_name}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_default_voucher_type_id_for_module for {module_name}: {e}")
        return None

def add_voucher_column(voucher_type_code, column_name, data_type, is_mandatory=False, is_calculated=False, calculation_logic=None):
    """Add a new column to a voucher type."""
    session = Session()
    try:
        if data_type not in ('TEXT', 'INTEGER', 'REAL', 'DATE'):
            logger.error(f"Invalid data type {data_type} for column {column_name}")
            return False
        voucher_type_id = get_voucher_type_id(voucher_type_code)
        if not voucher_type_id:
            logger.error(f"Invalid voucher type code: {voucher_type_code}")
            return False
        max_order = session.query(func.max(VoucherColumn.display_order)).filter_by(voucher_type_id=voucher_type_id).scalar() or 0
        display_order = max_order + 1
        session.add(VoucherColumn(
            voucher_type_id=voucher_type_id,
            column_name=column_name,
            data_type=data_type,
            is_mandatory=is_mandatory,
            display_order=display_order,
            is_calculated=is_calculated,
            calculation_logic=calculation_logic
        ))
        session.commit()
        logger.info(f"Added column {column_name} to voucher type {voucher_type_code}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to add column {column_name} to {voucher_type_code}: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in add_voucher_column for {voucher_type_code}, {column_name}: {e}")
        return False
    finally:
        session.close()

def initialize_voucher_columns():
    """Initialize voucher columns based on VOUCHER_DEFINITIONS."""
    session = Session()
    try:
        for voucher_name, details in VOUCHER_DEFINITIONS.items():
            type_code = details["type_code"]
            voucher_type_id = get_voucher_type_id(type_code)
            if not voucher_type_id:
                logger.error(f"Skipping voucher {voucher_name} due to missing voucher_type_id")
                continue
            session.query(VoucherColumn).filter_by(voucher_type_id=voucher_type_id).delete()
            for column in details["columns"]:
                session.add(VoucherColumn(
                    voucher_type_id=voucher_type_id,
                    column_name=column[0],
                    data_type=column[1],
                    is_mandatory=column[2],
                    display_order=column[3],
                    is_calculated=column[4],
                    calculation_logic=column[5]
                ))
        session.commit()
        logger.info("Voucher columns initialized successfully")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to initialize voucher columns: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in initialize_voucher_columns: {e}")
        raise
    finally:
        session.close()

def get_next_voucher_number(voucher_type_code):
    """Generate the next voucher number for a given voucher type (e.g., PV/2526/0001)."""
    try:
        fiscal_year = get_fiscal_year()
        sequence = get_next_doc_sequence(voucher_type_code, fiscal_year)
        if sequence is None:
            logger.error(f"Failed to generate sequence for voucher type {voucher_type_code}")
            return None
        prefix = voucher_type_code[:2] if voucher_type_code != "REJECTION_IN_OUT" else "RIO"
        return f"{prefix}/{fiscal_year}/{sequence:04d}"
    except Exception as e:
        logger.error(f"Error in get_next_voucher_number for {voucher_type_code}: {e}")
        return None

def commit_voucher_sequence(voucher_number, voucher_type_code):
    """Commit a voucher sequence number to the database."""
    try:
        parts = voucher_number.split('/')
        if len(parts) != 3:
            logger.error(f"Invalid voucher number format: {voucher_number}")
            return
        prefix, fiscal_year, sequence = parts[0], parts[1], int(parts[2])
        expected_prefix = voucher_type_code[:2] if voucher_type_code != "REJECTION_IN_OUT" else "RIO"
        if prefix != expected_prefix:
            logger.error(f"Voucher number {voucher_number} does not match expected prefix {expected_prefix}")
            return
        commit_doc_sequence(voucher_type_code, fiscal_year, sequence)
        logger.info(f"Committed voucher sequence {voucher_number} for {voucher_type_code}")
    except ValueError as e:
        logger.error(f"Failed to parse voucher number {voucher_number}: {e}")
    except Exception as e:
        logger.error(f"Error in commit_voucher_sequence for {voucher_number}: {e}")
        raise

def create_voucher_instance(voucher_type_code, date, data, module_name, record_id, total_amount=None, cgst_amount=None, sgst_amount=None, igst_amount=None):
    """Create a voucher instance and store it in the database."""
    session = Session()
    try:
        voucher_type_id = get_voucher_type_id(voucher_type_code)
        if not voucher_type_id:
            logger.error(f"Invalid voucher type code: {voucher_type_code}")
            return None
        voucher_number = get_next_voucher_number(voucher_type_code)
        if not voucher_number:
            logger.error(f"Failed to generate voucher number for {voucher_type_code}")
            return None
        data_json = json.dumps(data)
        instance = VoucherInstance(
            voucher_type_id=voucher_type_id,
            voucher_number=voucher_number,
            date=date,
            data=data_json,
            module_name=module_name,
            record_id=record_id,
            total_amount=total_amount,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount
        )
        session.add(instance)
        session.commit()
        voucher_id = instance.id
        commit_voucher_sequence(voucher_number, voucher_type_code)
        logger.info(f"Created voucher instance {voucher_number} (ID: {voucher_id}) for {voucher_type_code}")
        return voucher_id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to create voucher instance for {voucher_type_code}: {e}")
        return None
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in create_voucher_instance for {voucher_type_code}: {e}")
        return None
    finally:
        session.close()

def get_voucher_columns(voucher_type_code):
    """Retrieve the columns for a given voucher type."""
    session = Session()
    try:
        voucher_type_id = get_voucher_type_id(voucher_type_code)
        if not voucher_type_id:
            logger.error(f"Invalid voucher type code: {voucher_type_code}")
            return None
        columns = session.query(
            VoucherColumn.id, VoucherColumn.column_name, VoucherColumn.data_type,
            VoucherColumn.is_mandatory, VoucherColumn.display_order, VoucherColumn.is_calculated,
            VoucherColumn.calculation_logic
        ).filter_by(voucher_type_id=voucher_type_id).order_by(VoucherColumn.display_order).all()
        logger.debug(f"Retrieved {len(columns)} columns for voucher type {voucher_type_code}")
        return columns
    except SQLAlchemyError as e:
        logger.error(f"Failed to get voucher columns for {voucher_type_code}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_voucher_columns for {voucher_type_code}: {e}")
        return None
    finally:
        session.close()

def get_voucher_instances(voucher_type_code=None, module_name=None):
    """Retrieve voucher instances, optionally filtered by voucher type code and/or module name."""
    session = Session()
    try:
        query = session.query(
            VoucherInstance.id, VoucherInstance.voucher_type_id, VoucherInstance.voucher_number,
            VoucherInstance.created_at, VoucherInstance.date, VoucherInstance.data,
            VoucherInstance.module_name, VoucherInstance.record_id, VoucherInstance.total_amount,
            VoucherInstance.cgst_amount, VoucherInstance.sgst_amount, VoucherInstance.igst_amount,
            VoucherType.voucher_name, VoucherType.type_code, VoucherType.category
        ).join(VoucherType)
        if voucher_type_code:
            query = query.filter(VoucherType.type_code == voucher_type_code)
        if module_name:
            query = query.filter(VoucherInstance.module_name == module_name)
        query = query.order_by(VoucherInstance.created_at.desc())
        instances = query.all()
        logger.debug(f"Retrieved {len(instances)} voucher instances with voucher_type_code={voucher_type_code}, module_name={module_name}")
        return instances
    except SQLAlchemyError as e:
        logger.error(f"Failed to retrieve voucher instances: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_voucher_instances: {e}")
        return None
    finally:
        session.close()

def create_voucher_type(type_name, type_code, category, is_active=1):
    """Create a new voucher type in the database."""
    session = Session()
    try:
        voucher_type = VoucherType(
            voucher_name=type_name,
            type_code=type_code,
            category=category,
            is_active=is_active
        )
        session.add(voucher_type)
        session.commit()
        logger.info(f"Created voucher type {type_name} (ID: {voucher_type.id}, code: {type_code})")
        return voucher_type.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to create voucher type {type_name}: {e}")
        return None
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in create_voucher_type for {type_name}: {e}")
        return None
    finally:
        session.close()

def delete_voucher_column(voucher_type_code, column_name):
    """Delete a column from a voucher type."""
    session = Session()
    try:
        voucher_type_id = get_voucher_type_id(voucher_type_code)
        if not voucher_type_id:
            logger.error(f"Invalid voucher type code: {voucher_type_code}")
            return False
        deleted = session.query(VoucherColumn).filter_by(voucher_type_id=voucher_type_id, column_name=column_name).delete()
        if deleted == 0:
            logger.warning(f"No column {column_name} found for voucher type {voucher_type_code}")
            return False
        session.commit()
        logger.info(f"Deleted column {column_name} from voucher type {voucher_type_code}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Failed to delete column {column_name} from {voucher_type_code}: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in delete_voucher_column for {voucher_type_code}, {column_name}: {e}")
        return False
    finally:
        session.close()