"""
Enhanced database session management with automatic rollback and retry logic.
"""

from contextlib import contextmanager
from typing import Generator, Callable, Any, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from app.core.database import SessionLocal
from app.core.logging import get_logger, log_database_operation
import time
import logging

logger = get_logger("session")

class SessionManager:
    """Enhanced session manager with automatic error handling and rollback"""
    
    def __init__(self, session_factory: Callable = SessionLocal):
        self.session_factory = session_factory
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic rollback on error.
        
        Usage:
            with session_manager.get_session() as db:
                # perform database operations
                db.add(model_instance)
                db.commit()  # Explicit commit required
        """
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error occurred: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_transaction(self, auto_commit: bool = True) -> Generator[Session, None, None]:
        """
        Get a database session with transaction management.
        
        Args:
            auto_commit: If True, automatically commits on success
        
        Usage:
            with session_manager.get_transaction() as db:
                # perform database operations
                db.add(model_instance)
                # automatic commit on success, rollback on error
        """
        session = self.session_factory()
        try:
            yield session
            if auto_commit:
                session.commit()
                logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            session.rollback()
            logger.debug("Transaction rolled back")
            raise
        finally:
            session.close()
    
    def execute_with_retry(self, 
                          operation: Callable[[Session], Any], 
                          max_retries: int = 3,
                          retry_delay: float = 1.0,
                          exponential_backoff: bool = True) -> Any:
        """
        Execute a database operation with retry logic for transient failures.
        
        Args:
            operation: Function that takes a session and returns a result
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            exponential_backoff: Whether to use exponential backoff
        
        Returns:
            Result of the operation
        
        Raises:
            Final exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                with self.get_transaction() as session:
                    result = operation(session)
                    logger.debug(f"Operation succeeded on attempt {attempt + 1}")
                    return result
                    
            except (OperationalError, IntegrityError) as e:
                last_exception = e
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt) if exponential_backoff else retry_delay
                    logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
            except Exception as e:
                # Non-retryable exceptions
                logger.error(f"Non-retryable error in database operation: {e}")
                raise
        
        raise last_exception
    
    def safe_execute(self, operation: Callable[[Session], Any]) -> tuple[bool, Any, Optional[str]]:
        """
        Safely execute a database operation without raising exceptions.
        
        Args:
            operation: Function that takes a session and returns a result
        
        Returns:
            Tuple of (success: bool, result: Any, error_message: Optional[str])
        """
        try:
            with self.get_transaction() as session:
                result = operation(session)
                return True, result, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Safe execute failed: {error_msg}")
            return False, None, error_msg

# Global session manager instance
session_manager = SessionManager()

# Convenience functions for common patterns
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session (alias for session_manager.get_session)"""
    with session_manager.get_session() as session:
        yield session

@contextmanager
def get_db_transaction(auto_commit: bool = True) -> Generator[Session, None, None]:
    """Get a database transaction (alias for session_manager.get_transaction)"""
    with session_manager.get_transaction(auto_commit=auto_commit) as session:
        yield session

def execute_db_operation(operation: Callable[[Session], Any], 
                        with_retry: bool = False,
                        max_retries: int = 3) -> Any:
    """
    Execute a database operation with optional retry logic.
    
    Args:
        operation: Function that takes a session and returns a result
        with_retry: Whether to use retry logic for transient failures
        max_retries: Maximum retry attempts if with_retry is True
    
    Returns:
        Result of the operation
    """
    if with_retry:
        return session_manager.execute_with_retry(operation, max_retries=max_retries)
    else:
        with get_db_transaction() as session:
            return operation(session)

def safe_db_operation(operation: Callable[[Session], Any]) -> tuple[bool, Any, Optional[str]]:
    """
    Safely execute a database operation without raising exceptions.
    
    Returns:
        Tuple of (success, result, error_message)
    """
    return session_manager.safe_execute(operation)

# Decorators for automatic session management
def with_db_session(auto_commit: bool = True):
    """
    Decorator that provides a database session to the decorated function.
    
    Args:
        auto_commit: Whether to automatically commit the transaction
    
    Usage:
        @with_db_session()
        def my_function(db: Session, other_param: str):
            # db session is automatically provided
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with get_db_transaction(auto_commit=auto_commit) as session:
                return func(session, *args, **kwargs)
        return wrapper
    return decorator

def with_db_retry(max_retries: int = 3):
    """
    Decorator that adds retry logic to database operations.
    
    Args:
        max_retries: Maximum number of retry attempts
    
    Usage:
        @with_db_retry(max_retries=3)
        def my_db_function(db: Session):
            # This function will be retried on transient failures
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            def operation(session: Session):
                return func(session, *args, **kwargs)
            return session_manager.execute_with_retry(operation, max_retries=max_retries)
        return wrapper
    return decorator

# Audit logging helper
def log_db_operation(operation_type: str, table_name: str, record_id: Optional[int] = None):
    """
    Decorator to log database operations for auditing.
    
    Args:
        operation_type: Type of operation (CREATE, UPDATE, DELETE, SELECT)
        table_name: Name of the database table
        record_id: ID of the record (if applicable)
    
    Usage:
        @log_db_operation("CREATE", "users")
        def create_user(db: Session, user_data: dict):
            # Operation will be logged
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                log_database_operation(operation_type, table_name, record_id)
                return result
            except Exception as e:
                logger.error(f"Database operation {operation_type} on {table_name} failed: {e}")
                raise
        return wrapper
    return decorator

# Session health check
def check_session_health() -> dict:
    """
    Check the health of database sessions and connections.
    
    Returns:
        Dictionary with health status information
    """
    try:
        with get_db_session() as session:
            # Simple query to test connection
            result = session.execute("SELECT 1")
            result.fetchone()
            
            return {
                "status": "healthy",
                "message": "Database connection is working",
                "timestamp": time.time()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "timestamp": time.time()
        }

# Connection pool monitoring
def get_pool_status() -> dict:
    """
    Get the status of the database connection pool.
    
    Returns:
        Dictionary with pool status information
    """
    try:
        from app.core.database import engine
        pool = engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": "healthy"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }