# src/erp/logic/utils/voucher_utils.py
# Converted to use SQLAlchemy.

import logging
from typing import List, Tuple, Dict, Optional
from sqlalchemy import text, func
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path
from src.erp.logic.database.voucher import VOUCHER_TYPES, MODULE_VOUCHER_TYPES, item_based_vouchers, PRODUCT_COLUMNS, PRODUCT_VOUCHER_COLUMNS, VOUCHER_COLUMNS

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_voucher_types(module_name: str) -> List[Tuple[int, str]]:
    """Fetch voucher types for a given module from the database."""
    session = Session()
    try:
        if module_name not in MODULE_VOUCHER_TYPES:
            logger.error(f"Module {module_name} not found in MODULE_VOUCHER_TYPES")
            return []
        voucher_names = MODULE_VOUCHER_TYPES[module_name]
        placeholders = ','.join(['?'] * len(voucher_names))
        result = session.execute(text(f"""
            SELECT id, voucher_name
            FROM voucher_types
            WHERE voucher_name IN ({placeholders})
            ORDER BY voucher_name
        """), voucher_names).fetchall()
        return result
    except Exception as e:
        logger.error(f"Failed to fetch voucher types for module {module_name}: {e}")
        return []
    finally:
        session.close()

def create_voucher_type(name: str, description: str, module_name: str, is_default: bool) -> Optional[int]:
    """Create a new voucher type in the database."""
    session = Session()
    try:
        # Use a generated type_code based on the name (uppercase, underscores)
        type_code = name.replace(' (Goods Receipt Note)', '').replace(' ', '_').upper()
        category = module_name  # Use module_name as category for consistency
        session.execute(text("""
            INSERT INTO voucher_types (voucher_name, type_code, category, is_active)
            VALUES (:name, :type_code, :category, :is_active)
        """), {"name": name, "type_code": type_code, "category": category, "is_active": 1 if is_default else 0})
        voucher_type_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
        session.commit()
        logger.info(f"Created voucher type: {name} (ID: {voucher_type_id}, type_code: {type_code})")
        return voucher_type_id
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create voucher type {name}: {e}")
        return None
    finally:
        session.close()

def get_voucher_type_id(voucher_name: str) -> Optional[int]:
    """Fetch the ID of a voucher type by its name."""
    session = Session()
    try:
        result = session.execute(text("SELECT id FROM voucher_types WHERE voucher_name = :voucher_name"), {"voucher_name": voucher_name}).fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Failed to get voucher type ID for {voucher_name}: {e}")
        return None
    finally:
        session.close()

def get_voucher_instances(module_name: str) -> List[Dict]:
    """Fetch all voucher instances for a given module."""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT vi.*
            FROM voucher_instances vi
            JOIN voucher_types vt ON vi.voucher_type_id = vt.id
            WHERE vt.category = :module_name
        """), {"module_name": module_name}).fetchall()
        return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Failed to fetch voucher instances for module {module_name}: {e}")
        return []
    finally:
        session.close()

def get_products() -> List[Tuple[int, str, str, str, float, float]]:
    """Fetch all products from the database."""
    session = Session()
    try:
        result = session.execute(text("SELECT id, name, hsn_code, unit, unit_price, gst_rate FROM products")).fetchall()
        return result
    except Exception as e:
        logger.error(f"Failed to load products: {e}")
        return []
    finally:
        session.close()

def get_payment_terms() -> List[str]:
    """Fetch all payment terms from the database."""
    session = Session()
    try:
        result = session.execute(text("SELECT term FROM payment_terms ORDER BY term")).fetchall()
        return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Failed to load payment terms: {e}")
        return []
    finally:
        session.close()

def get_product_stock(product_id):
    session = Session()
    try:
        result = session.execute(text("SELECT quantity FROM stock WHERE product_id = :product_id"), {"product_id": product_id}).fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Failed to fetch stock for product_id {product_id}: {e}")
        return None
    finally:
        session.close()

def get_vendors() -> List[str]:
    session = Session()
    try:
        result = session.execute(text("SELECT name FROM vendors ORDER BY name")).fetchall()
        return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Failed to fetch vendors: {e}")
        return []
    finally:
        session.close()

def get_customers() -> List[str]:
    session = Session()
    try:
        result = session.execute(text("SELECT name FROM customers ORDER BY name")).fetchall()
        return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Failed to fetch customers: {e}")
        return []
    finally:
        session.close()