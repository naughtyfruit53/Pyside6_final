# src/erp/logic/utils/products_utils.py
# Converted validate_schema to use SQLAlchemy.

import logging
from typing import List
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url

logger = logging.getLogger(__name__)

def validate_schema(table_name: str, expected_columns: List[str]) -> bool:
    """Validate that the table exists and has the expected_columns."""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = :table_name
        """), {"table_name": table_name}).fetchall()
        columns = [row[0] for row in result]
        if not columns:
            logger.error(f"Table {table_name} does not exist")
            return False
        missing = [col for col in expected_columns if col not in columns]
        if missing:
            logger.error(f"Missing columns in {table_name}: {missing}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating schema for {table_name}: {e}")
        return False
    finally:
        session.close()

def validate_product_name(name: str) -> bool:
    """Validate product name to prevent SQL injection and ensure it's not empty."""
    if not name:
        return False
    # Disallow dangerous characters
    dangerous_chars = [';', '--', '/*', '*/']
    if any(char in name for char in dangerous_chars):
        logger.warning(f"Invalid characters in product name: {name}")
        return False
    return True