from typing import Optional
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_public_db
from app.models.base import Organization
from app.core.tenant import TenantContext
import logging

logger = logging.getLogger(__name__)

def get_organization_from_subdomain(subdomain: str, db: Session) -> Optional[Organization]:
    """Get organization by subdomain"""
    return db.query(Organization).filter(
        Organization.subdomain == subdomain,
        Organization.status == "active"
    ).first()

def get_organization_from_request(request: Request, db: Session = Depends(get_public_db)) -> Optional[Organization]:
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
    db: Session = Depends(get_public_db)
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