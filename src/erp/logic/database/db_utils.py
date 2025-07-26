# src/erp/logic/database/db_utils.py
# Modified to use SQLAlchemy sessions instead of sqlite3 connections.
# Removed create_table calls, as they are handled by Base.metadata.create_all in schema.py.
# For reset, drop_all and create_all.

import os
import logging
from datetime import datetime
import shutil
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path  # Updated to use get_database_url
from src.erp.logic.database.schema import create_tables_and_indexes, verify_voucher_columns_schema
from src.erp.logic.database.models import Base, AuditLog, PaymentTerm
from src.erp.logic.database.voucher import initialize_voucher_tables, initialize_vouchers

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In reset_database: Removed file operations (os.remove, shutil.copy) as PostgreSQL isn't file-based. Just drop/create schema.
def reset_database(confirm=False):
    """Drop all tables and recreate them, resetting the database."""
    if not confirm:
        logger.warning("Database reset attempted without confirmation. Aborting.")
        raise ValueError("Database reset requires explicit confirmation")
    logger.warning("Resetting PostgreSQL database")
    try:
        Base.metadata.drop_all(engine)
        create_tables_and_indexes()
        initialize_voucher_tables()
        initialize_vouchers()
        session = Session()
        try:
            session.add(AuditLog(
                table_name="database",
                record_id=0,
                action="DATABASE_RESET",
                username="system_user",
                timestamp=datetime.now()
            ))
            session.commit()
            logger.info("Database reset and initialized successfully")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise

# In initialize_database: Removed PRAGMA and integrity_check as they are SQLite-specific.
def initialize_database():
    """Initialize the PostgreSQL database and create necessary tables."""
    logger.debug("Initializing PostgreSQL database")
    try:
        create_tables_and_indexes()
        initialize_voucher_tables()
        initialize_vouchers()
        verify_voucher_columns_schema()
        session = Session()
        try:
            for term in ['Net 30', 'Net 60', 'Due on Receipt', 'Custom']:
                existing = session.query(PaymentTerm).filter_by(term=term).first()
                if not existing:
                    session.add(PaymentTerm(term=term))
            session.commit()
            logger.info("Database initialized successfully with payment terms")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise