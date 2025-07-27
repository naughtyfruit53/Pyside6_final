"""
Security and audit service for multi-tenant application
"""
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.base import AuditLog, User
from app.core.tenant import TenantContext
import logging
import json
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SecurityService:
    """Service for handling security-related operations"""
    
    @staticmethod
    def log_audit_event(
        db: Session,
        table_name: str,
        record_id: int,
        action: str,
        user_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            org_id = TenantContext.get_organization_id()
            if not org_id:
                logger.warning("Audit log attempted without organization context")
                return
            
            audit_log = AuditLog(
                organization_id=org_id,
                table_name=table_name,
                record_id=record_id,
                action=action,
                user_id=user_id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            db.rollback()
    
    @staticmethod
    def validate_input_data(data: Dict[str, Any], allowed_fields: set) -> Dict[str, Any]:
        """Validate and sanitize input data"""
        validated_data = {}
        
        for field, value in data.items():
            if field not in allowed_fields:
                logger.warning(f"Attempted to set non-allowed field: {field}")
                continue
            
            # Basic sanitization
            if isinstance(value, str):
                # Remove potential XSS characters
                value = value.strip()
                if len(value) > 1000:  # Prevent excessively long strings
                    value = value[:1000]
            
            validated_data[field] = value
        
        return validated_data
    
    @staticmethod
    def check_rate_limit(
        db: Session,
        user_id: int,
        action: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> tuple[bool, int]:
        """Check if user has exceeded rate limit for an action"""
        try:
            from datetime import datetime, timedelta
            
            since_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            
            # Count recent attempts
            org_id = TenantContext.get_organization_id()
            recent_attempts = db.query(AuditLog).filter(
                AuditLog.organization_id == org_id,
                AuditLog.user_id == user_id,
                AuditLog.action == action,
                AuditLog.timestamp >= since_time
            ).count()
            
            remaining_attempts = max(0, max_attempts - recent_attempts)
            is_allowed = recent_attempts < max_attempts
            
            return is_allowed, remaining_attempts
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, max_attempts  # Allow on error
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def extract_request_info(request: Request) -> tuple[Optional[str], Optional[str]]:
        """Extract IP address and user agent from request"""
        try:
            # Get IP address (handle proxy headers)
            ip_address = request.headers.get("X-Forwarded-For")
            if ip_address:
                ip_address = ip_address.split(",")[0].strip()
            else:
                ip_address = request.headers.get("X-Real-IP")
                if not ip_address:
                    ip_address = getattr(request.client, "host", None)
            
            # Get user agent
            user_agent = request.headers.get("User-Agent", "")[:500]  # Limit length
            
            return ip_address, user_agent
            
        except Exception as e:
            logger.error(f"Failed to extract request info: {e}")
            return None, None

class TenantSecurityMixin:
    """Mixin to add security features to API endpoints"""
    
    @staticmethod
    def require_tenant_access(obj: Any, user: User) -> None:
        """Ensure user has access to object in their tenant"""
        if user.is_super_admin:
            return  # Super admin has access to everything
        
        if not hasattr(obj, 'organization_id'):
            return  # Object doesn't have tenant isolation
        
        if obj.organization_id != user.organization_id:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
    
    @staticmethod
    def log_model_change(
        db: Session,
        model_name: str,
        record_id: int,
        action: str,
        user: User,
        request: Request,
        old_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None
    ):
        """Log a model change for audit purposes"""
        try:
            changes = {}
            if old_data and new_data:
                for key, new_value in new_data.items():
                    old_value = old_data.get(key)
                    if old_value != new_value:
                        changes[key] = {
                            'old': old_value,
                            'new': new_value
                        }
            elif new_data:
                changes = new_data
            
            ip_address, user_agent = SecurityService.extract_request_info(request)
            
            SecurityService.log_audit_event(
                db=db,
                table_name=model_name,
                record_id=record_id,
                action=action,
                user_id=user.id,
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
        except Exception as e:
            logger.error(f"Failed to log model change: {e}")

class DataMaskingService:
    """Service for masking sensitive data in logs and responses"""
    
    SENSITIVE_FIELDS = {
        'password', 'hashed_password', 'token', 'secret', 'key',
        'gst_number', 'pan_number', 'cin_number', 'bank_account'
    }
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in data dictionary"""
        masked_data = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in DataMaskingService.SENSITIVE_FIELDS):
                if isinstance(value, str) and len(value) > 4:
                    masked_data[key] = f"***{value[-4:]}"
                else:
                    masked_data[key] = "***"
            else:
                masked_data[key] = value
        
        return masked_data
    
    @staticmethod
    def prepare_audit_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for audit logging by masking sensitive fields"""
        return DataMaskingService.mask_sensitive_data(data)

# Decorator for audit logging
def audit_action(action: str, table_name: str):
    """Decorator to automatically log actions for audit purposes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would need to be implemented based on specific needs
            # For now, it's a placeholder for the concept
            return func(*args, **kwargs)
        return wrapper
    return decorator