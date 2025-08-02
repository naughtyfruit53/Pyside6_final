from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Determine database URL with fallback to SQLite
database_url = settings.DATABASE_URL
if not database_url:
    database_url = "sqlite:///./tritiq_erp.db"
    logger.info("No DATABASE_URL configured, using SQLite: tritiq_erp.db")

# Database engine configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": settings.DEBUG
}

# PostgreSQL/Supabase specific configuration
if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    })
    logger.info("Using PostgreSQL/Supabase database configuration")
elif database_url.startswith("sqlite://"):
    # SQLite specific configuration
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False}
    })
    logger.info("Using SQLite database configuration")

# Database engine
engine = create_engine(database_url, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session with enhanced error handling
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Enhanced context manager for database transactions
class DatabaseTransaction:
    """Context manager for database transactions with automatic rollback on error"""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session or SessionLocal()
        self.should_close = db_session is None
        
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                logger.error(f"Transaction failed: {exc_val}")
                self.db.rollback()
            else:
                self.db.commit()
        except Exception as e:
            logger.error(f"Error during transaction cleanup: {e}")
            self.db.rollback()
        finally:
            if self.should_close:
                self.db.close()
        
        # Don't suppress exceptions
        return False

def get_db_transaction():
    """Get database session with transaction management"""
    with DatabaseTransaction() as db:
        yield db

# Utility functions for session management
def safe_database_operation(operation_func, *args, **kwargs):
    """
    Safely execute a database operation with automatic rollback on error.
    
    Args:
        operation_func: Function to execute that takes db as first parameter
        *args: Additional arguments for the operation function
        **kwargs: Additional keyword arguments for the operation function
    
    Returns:
        Result of the operation function or None if error occurred
    """
    try:
        with DatabaseTransaction() as db:
            return operation_func(db, *args, **kwargs)
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        return None

def execute_with_retry(operation_func, max_retries: int = 3, *args, **kwargs):
    """
    Execute database operation with retry logic for transient failures.
    
    Args:
        operation_func: Function to execute
        max_retries: Maximum number of retry attempts
        *args: Arguments for the operation function
        **kwargs: Keyword arguments for the operation function
    
    Returns:
        Result of the operation or raises the final exception
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return safe_database_operation(operation_func, *args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Database operation failed after {max_retries + 1} attempts: {e}")
    
    raise last_exception

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)