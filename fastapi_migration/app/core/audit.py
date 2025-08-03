"""
Audit logging system for security-sensitive operations
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging audit events"""
    
    @staticmethod
    def log_login_attempt(
        db: Session,
        email: str,
        success: bool,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[object]:
        """Log login attempt"""
        return AuditLogger._create_security_audit_log(
            db=db,
            event_type="LOGIN",
            action="LOGIN_ATTEMPT",
            user_email=email,
            user_id=user_id,
            user_role=user_role,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="SUCCESS" if success else "FAILED",
            error_message=error_message,
            details=details
        )
    
    @staticmethod
    def log_master_password_usage(
        db: Session,
        email: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[object]:
        """Log temporary master password usage"""
        return AuditLogger._create_security_audit_log(
            db=db,
            event_type="SECURITY",
            action="MASTER_PASSWORD_USED",
            user_email=email,
            user_id=user_id,
            user_role="super_admin",
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="SUCCESS",
            details=details
        )
    
    @staticmethod
    def log_password_reset(
        db: Session,
        admin_email: str,
        target_email: str,
        admin_user_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        reset_type: str = "SINGLE_USER"
    ) -> Optional[object]:
        """Log password reset operation"""
        details = {
            "target_email": target_email,
            "target_user_id": target_user_id,
            "reset_type": reset_type
        }
        
        return AuditLogger._create_security_audit_log(
            db=db,
            event_type="PASSWORD_RESET",
            action="ADMIN_PASSWORD_RESET",
            user_email=admin_email,
            user_id=admin_user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="SUCCESS" if success else "FAILED",
            error_message=error_message,
            details=details
        )
    
    @staticmethod
    def log_data_reset(
        db: Session,
        admin_email: str,
        admin_user_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        reset_scope: str = "ORGANIZATION",
        affected_organizations: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[object]:
        """Log data reset operation"""
        log_details = {
            "reset_scope": reset_scope,
            "affected_organizations": affected_organizations or [],
            **(details or {})
        }
        
        return AuditLogger._create_security_audit_log(
            db=db,
            event_type="DATA_RESET",
            action="ADMIN_DATA_RESET",
            user_email=admin_email,
            user_id=admin_user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="SUCCESS" if success else "FAILED",
            error_message=error_message,
            details=log_details
        )
    
    @staticmethod
    def log_permission_denied(
        db: Session,
        user_email: str,
        attempted_action: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[object]:
        """Log permission denied events"""
        log_details = {
            "attempted_action": attempted_action,
            **(details or {})
        }
        
        return AuditLogger._create_security_audit_log(
            db=db,
            event_type="SECURITY",
            action="PERMISSION_DENIED",
            user_email=user_email,
            user_id=user_id,
            user_role=user_role,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success="FAILED",
            error_message="Insufficient permissions",
            details=log_details
        )
    
    @staticmethod
    def _create_security_audit_log(
        db: Session,
        event_type: str,
        action: str,
        user_email: str,
        success: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        organization_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[object]:
        """Create and save security audit log entry using the existing AuditLog model"""
        try:
            # For now, let's create a simple log entry using the existing model structure
            # We'll adapt it to work with the existing audit log table
            from app.models.base import AuditLog
            
            # Use organization_id as is (can be None for super admin/platform events)
            audit_org_id = organization_id
            
            audit_log = AuditLog(
                organization_id=audit_org_id,
                table_name="security_events",  # Use a generic table name for security events
                record_id=user_id or 0,  # Use user_id as record_id
                action=f"{event_type}:{action}",  # Combine event_type and action
                user_id=user_id,
                changes={
                    "event_type": event_type,
                    "action": action,
                    "user_email": user_email,
                    "user_role": user_role,
                    "success": success,
                    "error_message": error_message,
                    "details": details,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(f"Security audit log created: {event_type}:{action} by {user_email}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create security audit log: {e}")
            db.rollback()
            # Don't raise exception to avoid disrupting main operation
            return None


def get_client_ip(request) -> Optional[str]:
    """Extract client IP address from request"""
    try:
        # Check for forwarded headers first (for reverse proxy scenarios)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    except Exception:
        return None


def get_user_agent(request) -> Optional[str]:
    """Extract user agent from request"""
    try:
        return request.headers.get("User-Agent")
    except Exception:
        return None