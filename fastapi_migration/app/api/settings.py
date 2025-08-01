from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.core.database import get_db
from app.api.auth import get_current_active_user, get_current_super_admin
from app.models.base import User, Organization
from app.services.reset_service import ResetService
from app.core.tenant import require_current_organization_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/reset/organization")
async def reset_organization_data(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Reset all data for the current organization (Super Admin only)"""
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required. Set confirm=true to proceed."
        )
    
    try:
        org_id = require_current_organization_id()
        
        # Use reset service to perform the reset
        result = ResetService.reset_organization_data(db, org_id)
        
        logger.info(f"Organization {org_id} data reset by user {current_user.id}")
        
        return {
            "message": "Organization data reset successfully",
            "organization_id": org_id,
            "reset_details": result
        }
        
    except Exception as e:
        logger.error(f"Failed to reset organization data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset organization data: {str(e)}"
        )

@router.post("/reset/entity")
async def reset_entity_data(
    entity_id: int,
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Reset all data for a specific entity/organization (Entity Super Admin only)"""
    
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required. Set confirm=true to proceed."
        )
    
    try:
        # Verify the organization exists
        organization = db.query(Organization).filter(Organization.id == entity_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check if user has permission (super admin or entity superadmin for this org)
        if not current_user.is_super_admin:
            if current_user.organization_id != entity_id or current_user.role != "org_admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
        
        # Use reset service to perform the reset
        result = ResetService.reset_organization_data(db, entity_id)
        
        logger.info(f"Entity {entity_id} data reset by user {current_user.id}")
        
        return {
            "message": "Entity data reset successfully",
            "entity_id": entity_id,
            "organization_name": organization.name,
            "reset_details": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset entity data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset entity data: {str(e)}"
        )

@router.post("/organization/{org_id}/suspend")
async def suspend_organization(
    org_id: int,
    reason: str = "Administrative action",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Suspend an organization account (Super Admin only)"""
    
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if organization.status == "suspended":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization is already suspended"
            )
        
        # Update organization status
        organization.status = "suspended"
        db.commit()
        
        logger.info(f"Organization {org_id} suspended by user {current_user.id}. Reason: {reason}")
        
        return {
            "message": "Organization suspended successfully",
            "organization_id": org_id,
            "organization_name": organization.name,
            "status": "suspended",
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend organization: {str(e)}"
        )

@router.post("/organization/{org_id}/activate")
async def activate_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Activate a suspended organization (Super Admin only)"""
    
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if organization.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization is already active"
            )
        
        # Update organization status
        organization.status = "active"
        db.commit()
        
        logger.info(f"Organization {org_id} activated by user {current_user.id}")
        
        return {
            "message": "Organization activated successfully",
            "organization_id": org_id,
            "organization_name": organization.name,
            "status": "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate organization: {str(e)}"
        )

@router.put("/organization/{org_id}/max-users")
async def update_max_users(
    org_id: int,
    max_users: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Update the maximum number of users allowed for an organization"""
    
    if max_users <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum users must be greater than 0"
        )
    
    try:
        organization = db.query(Organization).filter(Organization.id == org_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        old_max_users = organization.max_users
        organization.max_users = max_users
        db.commit()
        
        logger.info(f"Organization {org_id} max users updated from {old_max_users} to {max_users} by user {current_user.id}")
        
        return {
            "message": "Maximum users updated successfully",
            "organization_id": org_id,
            "organization_name": organization.name,
            "old_max_users": old_max_users,
            "new_max_users": max_users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update max users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update max users: {str(e)}"
        )