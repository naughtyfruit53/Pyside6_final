# Revised core.tenant.py

"""
Multi-tenant context and middleware for tenant isolation
"""
from typing import Optional, Any
from contextvars import ContextVar
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.base import Organization, User
import logging

logger = logging.getLogger(__name__)

# Context variables for tenant isolation
_current_organization_id: ContextVar[Optional[int]] = ContextVar("current_organization_id", default=None)
_current_user_id: ContextVar[Optional[int]] = ContextVar("current_user_id", default=None)

class TenantContext:
    """Tenant context manager for maintaining tenant isolation"""
    
    @staticmethod
    def get_organization_id() -> Optional[int]:
        """Get current organization ID from context"""
        return _current_organization_id.get()
    
    @staticmethod
    def set_organization_id(org_id: int) -> None:
        """Set current organization ID in context"""
        _current_organization_id.set(org_id)
    
    @staticmethod
    def get_user_id() -> Optional[int]:
        """Get current user ID from context"""
        return _current_user_id.get()
    
    @staticmethod
    def set_user_id(user_id: int) -> None:
        """Set current user ID in context"""
        _current_user_id.set(user_id)
    
    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _current_organization_id.set(None)
        _current_user_id.set(None)

class TenantMiddleware:
    """Middleware to extract and set tenant context from requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract tenant context from subdomain or header
            org_id = await self._extract_organization_id(request)
            if org_id:
                TenantContext.set_organization_id(org_id)
        
        # Process request
        await self.app(scope, receive, send)
        
        # Clear context after request
        TenantContext.clear()
    
    async def _extract_organization_id(self, request: Request) -> Optional[int]:
        """Extract organization ID from request"""
        try:
            # Method 1: From subdomain
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain and subdomain != "www":
                    # Look up organization by subdomain
                    # Note: This would require database access in middleware
                    # For now, we'll handle this in the authentication dependency
                    pass
            
            # Method 2: From custom header
            org_id = request.headers.get("X-Organization-ID")
            if org_id and org_id.isdigit():
                return int(org_id)
            
            # Method 3: From path parameter (e.g., /api/v1/org/{org_id}/...)
            path_parts = request.url.path.split("/")
            if len(path_parts) >= 5 and path_parts[3] == "org":
                if path_parts[4].isdigit():
                    return int(path_parts[4])
            
        except Exception as e:
            logger.warning(f"Error extracting organization ID: {e}")
        
        return None

def get_organization_from_subdomain(subdomain: str, db: Session) -> Optional[Organization]:
    """Get organization by subdomain"""
    return db.query(Organization).filter(
        Organization.subdomain == subdomain,
        Organization.status == "active"
    ).first()

def get_organization_from_request(request: Request, db: Session = Depends(get_db)) -> Optional[Organization]:
    """Get organization from request context"""
    try:
        # Try subdomain first
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain and subdomain not in ["www", "api", "admin"]:
                org = get_organization_from_subdomain(subdomain, db)
                if org:
                    return org
        
        # Try X-Organization-ID header
        org_id = request.headers.get("X-Organization-ID")
        if org_id and org_id.isdigit():
            org = db.query(Organization).filter(
                Organization.id == int(org_id),
                Organization.status == "active"
            ).first()
            if org:
                return org
        
        # Try path parameter
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 5 and path_parts[3] == "org":
            if path_parts[4].isdigit():
                org_id = int(path_parts[4])
                org = db.query(Organization).filter(
                    Organization.id == org_id,
                    Organization.status == "active"
                ).first()
                if org:
                    return org
    
    except Exception as e:
        logger.error(f"Error getting organization from request: {e}")
    
    return None

async def require_organization(
    request: Request, 
    db: Session = Depends(get_db)
) -> Organization:
    """Dependency to require valid organization context"""
    org = get_organization_from_request(request, db)
    if not org:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing organization context"
        )
    
    # Set in context for later use
    TenantContext.set_organization_id(org.id)
    return org

def require_current_organization_id() -> int:
    """Require and get current organization ID from context"""
    org_id = TenantContext.get_organization_id()
    if org_id is None:
        raise HTTPException(
            status_code=400,
            detail="No current organization specified"
        )
    return org_id

class TenantQueryMixin:
    """Mixin to add tenant filtering to database queries"""
    
    @staticmethod
    def filter_by_tenant(query, model_class, org_id: Optional[int] = None):
        """Add tenant filter to query"""
        if org_id is None:
            org_id = TenantContext.get_organization_id()
        
        if org_id is None:
            raise HTTPException(
                status_code=500,
                detail="No organization context available for query"
            )
        
        # Check if model has organization_id field
        if hasattr(model_class, 'organization_id'):
            return query.filter(model_class.organization_id == org_id)
        
        return query
    
    @staticmethod
    def ensure_tenant_access(obj: Any, org_id: Optional[int] = None) -> None:
        """Ensure object belongs to current tenant"""
        if org_id is None:
            org_id = TenantContext.get_organization_id()
        
        if org_id is None:
            raise HTTPException(
                status_code=500,
                detail="No organization context available"
            )
        
        if hasattr(obj, 'organization_id') and obj.organization_id != org_id:
            raise HTTPException(
                status_code=404,
                detail="Resource not found"
            )