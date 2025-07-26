# src/erp/logic/backup_restore.py
# Adapted to use SQLAlchemy for table metadata and data export.

import logging
from datetime import datetime
import os
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from sqlalchemy.exc import SQLAlchemyError
from src.core.config import get_database_url, get_log_path, get_backup_path
from src.erp.logic.database.models import Base  # Assuming all models are defined here

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_table_names():
    """Retrieve all table names from the database metadata."""
    try:
        metadata = Base.metadata
        return [table.name for table in metadata.sorted_tables]
    except Exception as e:
        logger.error(f"Failed to get table names: {e}")
        return []

def export_table_data(session, table_name):
    """Export data from a table as SQL INSERT statements."""
    try:
        table = Base.metadata.tables[table_name]
        result = session.execute(table.select()).fetchall()
        if not result:
            return []
        
        columns = [col.name for col in table.columns]
        
        insert_statements = []
        for row in result:
            values = ', '.join(["'" + str(v).replace("'", "''") + "'" if v is not None else 'NULL' for v in row])
            insert_statements.append(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values});")
        return insert_statements
    except Exception as e:
        logger.error(f"Failed to export data from {table_name}: {e}")
        return []

def get_column_info(session, table_name):
    """Retrieve column information for a table."""
    try:
        result = session.execute(text(f"""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
        """), {"table_name": table_name}).fetchall()
        return {row[0]: row[1] for row in result}
    except Exception as e:
        logger.error(f"Failed to get column info for {table_name}: {e}")
        return {}