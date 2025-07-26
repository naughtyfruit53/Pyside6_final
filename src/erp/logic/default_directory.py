# src/erp/logic/default_directory.py
# Converted to SQLAlchemy.

import os
import logging
from datetime import datetime
from sqlalchemy import text
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_default_directory(directory: str):
    """Save the default directory to the database."""
    session = Session()
    try:
        directory = os.path.abspath(directory)
        session.execute(text("""
            INSERT INTO default_directory (id, directory_path, created_at)
            VALUES (1, :directory_path, :created_at)
            ON CONFLICT (id) DO UPDATE SET directory_path = EXCLUDED.directory_path, created_at = EXCLUDED.created_at
        """), {"directory_path": directory, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        session.commit()
        # Verify
        result = session.execute(text("SELECT directory_path FROM default_directory WHERE id = 1")).fetchone()
        if result and result[0] == directory:
            logger.debug(f"Default directory saved and verified: {directory}")
            return True
        else:
            logger.error(f"Failed to verify default directory: {directory}")
            return False
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save default directory {directory}: {e}")
        return False
    finally:
        session.close()

def get_default_directory():
    """Retrieve the default directory from the database."""
    session = Session()
    try:
        result = session.execute(text("SELECT directory_path FROM default_directory WHERE id = 1")).fetchone()
        if result and result[0]:
            logger.debug(f"Retrieved default directory: {result[0]}")
            return result[0]
        logger.debug("No default directory found in database")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve default directory: {e}")
        return None
    finally:
        session.close()