# Enhanced core.tenant.py for strict organization-level data scoping

"""
Multi-tenant context and middleware for strict tenant isolation
"""
from typing import Optional, Any, Type, TypeVar, List
from contextvars import ContextVar
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_
from app.core.database import get_db
from app.models.base import Organization, User
import logging

logger = logging.getLogger(__name__)

# Context variables for tenant isolation
_current_organization_id: ContextVar[Optional[int]] = ContextVar("current_organization_id", default=None)
_current_user_id: ContextVar[Optional[int]] = ContextVar("current_user_id", default=None)

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType")

class TenantContext:
    """Enhanced tenant context manager for strict tenant isolation"""
    
    @staticmethod
    def get_organization_id() -> Optional[int]:
        """Get current organization ID from context"""
        return _current_organization_id.get()
    
    @staticmethod
    def set_organization_id(org_id: int) -> None:
        """Set current organization ID in context"""
        _current_organization_id.set(org_id)
        logger.debug(f"Set tenant context: organization_id={org_id}")
    
    @staticmethod
    def get_user_id() -> Optional[int]:
        """Get current user ID from context"""
        return _current_user_id.get()
    
    @staticmethod
    def set_user_id(user_id: int) -> None:
        """Set current user ID in context"""
        _current_user_id.set(user_id)
        logger.debug(f"Set tenant context: user_id={user_id}")
    
    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _current_organization_id.set(None)
        _current_user_id.set(None)
        logger.debug("Cleared tenant context")
    
    @staticmethod
    def validate_organization_access(organization_id: int, user: User) -> bool:
        """Validate that user has access to the specified organization"""
        if user.organization_id is None:
            # Platform users (no organization) have access to all organizations
            return True
        return user.organization_id == organization_id

class TenantQueryFilter:
    """Enhanced query filter for strict organization-level data isolation"""
    
    @staticmethod
    def apply_organization_filter(
        query: Query, 
        model: Type[ModelType], 
        organization_id: Optional[int] = None,
        user: Optional[User] = None
    ) -> Query:
        """
        Apply organization filter to a query with strict enforcement
        
        Args:
            query: SQLAlchemy query
            model: Model class
            organization_id: Organization ID to filter by (optional, uses context if not provided)
            user: Current user (for validation)
        
        Returns:
            Filtered query
        
        Raises:
            HTTPException: If organization access is denied
        """
        # Get organization ID from parameter or context
        org_id = organization_id or TenantContext.get_organization_id()
        
        # Check if model has organization_id field
        if not hasattr(model, 'organization_id'):
            logger.warning(f"Model {model.__name__} does not have organization_id field")
            return query
        
        # For platform users (no organization), allow access if organization_id is explicitly provided
        if user and user.organization_id is None:
            if org_id is not None:
                return query.filter(model.organization_id == org_id)
            else:
                # Platform user without specific organization - return empty result for safety
                return query.filter(model.organization_id.is_(None))
        
        # For organization users, enforce strict filtering
        if org_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization context is required"
            )
        
        # Validate user has access to this organization
        if user and not TenantContext.validate_organization_access(org_id, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to organization {org_id}"
            )
        
        return query.filter(model.organization_id == org_id)
    
    @staticmethod
    def validate_organization_data(data: dict, user: User) -> dict:
        """
        Validate and set organization_id in data for create/update operations
        
        Args:
            data: Data dictionary
            user: Current user
        
        Returns:
            Data with validated organization_id
        """
        current_org_id = TenantContext.get_organization_id()
        
        # Platform users must specify organization_id
        if user.organization_id is None:
            if 'organization_id' not in data or data['organization_id'] is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Platform users must specify organization_id"
                )
            # Platform user can set any organization_id
            return data
        
        # Organization users: enforce their organization
        if 'organization_id' in data and data['organization_id'] != user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot create/update data for organization {data['organization_id']} - user belongs to organization {user.organization_id}"
            )
        
        # Set organization_id from user context
        data['organization_id'] = user.organization_id
        return data

class TenantQueryMixin:
    """Enhanced mixin for tenant-aware queries (backward compatibility)"""
    
    @staticmethod
    def filter_by_tenant(query: Query, model: Type[ModelType], organization_id: int) -> Query:
        """Filter query by tenant/organization (legacy method)"""
        return TenantQueryFilter.apply_organization_filter(query, model, organization_id)
    
    @staticmethod
    def scoped_query(db: Session, model: Type[ModelType], user: User) -> Query:
        """Create a tenant-scoped query for the given model"""
        query = db.query(model)
        return TenantQueryFilter.apply_organization_filter(query, model, user=user)

class TenantMiddleware:
    """Enhanced middleware to extract and set tenant context from requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract organization context from various sources
            org_id = self._extract_organization_id(request)
            
            if org_id:
                TenantContext.set_organization_id(org_id)
                logger.debug(f"Middleware set organization context: {org_id}")
        
        await self.app(scope, receive, send)
    
    def _extract_organization_id(self, request: Request) -> Optional[int]:
        """Extract organization ID from request headers, subdomain, or path"""
        # Try X-Organization-ID header
        org_header = request.headers.get("X-Organization-ID")
        if org_header:
            try:
                return int(org_header)
            except ValueError:
                logger.warning(f"Invalid organization ID in header: {org_header}")
        
        # Try subdomain-based extraction (e.g., tenant1.api.example.com)
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            # Look up organization by subdomain (would need database access)
            # This is a placeholder - implement based on your subdomain strategy
            pass
        
        # Try path-based extraction (e.g., /org/123/api/...)
        path = request.url.path
        if path.startswith("/org/"):
            try:
                org_id = int(path.split("/")[2])
                return org_id
            except (IndexError, ValueError):
                pass
        
        return None

def get_organization_from_request(request: Request, db: Session = Depends(get_db)) -> Optional[Organization]:
    """Get organization from request context (legacy function)"""
    org_id = TenantContext.get_organization_id()
    if org_id:
        return db.query(Organization).filter(Organization.id == org_id).first()
    return None

# Enhanced dependency functions for strict organization scoping
def require_organization_context() -> int:
    """Require organization context to be set"""
    org_id = TenantContext.get_organization_id()
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required"
        )
    return org_id

def get_tenant_scoped_db(
    model: Type[ModelType],
    db: Session = Depends(get_db)
) -> Query:
    """Get a tenant-scoped database query for the specified model"""
    org_id = require_organization_context()
    query = db.query(model)
    return TenantQueryFilter.apply_organization_filter(query, model, org_id)
    
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