import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from app.core.config import settings

def setup_logging() -> logging.Logger:
    """Setup application logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("fastapi_migration")
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    # Prevent duplicate logs
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(
        log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(
        log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance"""
    if name:
        return logging.getLogger(f"fastapi_migration.{name}")
    return logging.getLogger("fastapi_migration")

def log_database_operation(operation: str, table: str, record_id: Optional[int] = None, user_id: Optional[int] = None):
    """Log database operations for auditing"""
    logger = get_logger("database")
    message = f"DB Operation: {operation} on {table}"
    if record_id:
        message += f" (ID: {record_id})"
    if user_id:
        message += f" by User ID: {user_id}"
    logger.info(message)

def log_security_event(event: str, user_email: Optional[str] = None, ip_address: Optional[str] = None, details: Optional[str] = None):
    """Log security-related events"""
    logger = get_logger("security")
    message = f"Security Event: {event}"
    if user_email:
        message += f" - User: {user_email}"
    if ip_address:
        message += f" - IP: {ip_address}"
    if details:
        message += f" - Details: {details}"
    logger.warning(message)

def log_password_reset(user_email: str, reset_by: Optional[str] = None, success: bool = True):
    """Log password reset events"""
    logger = get_logger("security")
    status = "SUCCESS" if success else "FAILED"
    message = f"Password Reset {status}: {user_email}"
    if reset_by:
        message += f" (Reset by: {reset_by})"
    logger.info(message)

def log_email_operation(operation: str, recipient: str, success: bool = True, error: Optional[str] = None):
    """Log email operations"""
    logger = get_logger("email")
    status = "SUCCESS" if success else "FAILED"
    message = f"Email {operation} {status}: {recipient}"
    if error:
        message += f" - Error: {error}"
    if success:
        logger.info(message)
    else:
        logger.error(message)

# Initialize logging when module is imported
app_logger = setup_logging()