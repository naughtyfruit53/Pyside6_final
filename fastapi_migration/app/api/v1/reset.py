"""
Data reset endpoints (API v1) with comprehensive permission checking and audit logging
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.api.v1.auth import get_current_active_user, get_current_super_admin, get_current_admin_user
from app.core.permissions import (
    PermissionChecker, Permission, require_super_admin, require_org_admin, 
    require_data_reset_permission
)
from app.core.audit import AuditLogger, get_client_ip, get_user_agent
from app.models.base import User, Organization
from app.schemas.reset import (
    DataResetRequest, DataResetResponse, OrganizationDataResetResponse,
    ResetScope, DataResetType, ResetStatusRequest, ResetStatusResponse,
    EmergencyAccessRequest, EmergencyAccessResponse
)
from app.services.reset_service import ResetService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/data/preview")
async def preview_data_reset(
    reset_request: DataResetRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_data_reset_permission)
):
    """Preview what data would be deleted without actually deleting"""
    try:
        if reset_request.scope == ResetScope.ORGANIZATION:
            if not reset_request.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="organization_id is required for organization scope"
                )
            
            # Check if user can reset data for this organization
            if not PermissionChecker.can_reset_organization_data(current_user, reset_request.organization_id):
                PermissionChecker.require_permission(
                    Permission.RESET_ANY_DATA,
                    current_user,
                    db,
                    request,
                    reset_request.organization_id
                )
            
            # Get preview for specific organization
            preview = ResetService.get_reset_preview(
                db=db,
                organization_id=reset_request.organization_id,
                reset_request=reset_request
            )
            
        elif reset_request.scope == ResetScope.ALL_ORGANIZATIONS:
            # Only super admin can preview global reset
            PermissionChecker.require_permission(
                Permission.RESET_ANY_DATA,
                current_user,
                db,
                request
            )
            
            # Get preview for all organizations
            preview = ResetService.get_reset_preview(
                db=db,
                organization_id=None,
                reset_request=reset_request
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset scope"
            )
        
        # Log preview request
        AuditLogger.log_data_reset(
            db=db,
            admin_email=current_user.email,
            admin_user_id=current_user.id,
            organization_id=reset_request.organization_id if reset_request.scope == ResetScope.ORGANIZATION else None,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_scope=reset_request.scope.value,
            details={
                "action": "reset_preview",
                "reset_type": reset_request.reset_type,
                "preview_data": preview
            }
        )
        
        return {
            "message": "Reset preview generated successfully",
            "scope": reset_request.scope,
            "reset_type": reset_request.reset_type,
            "preview": preview,
            "warning": "This preview shows the number of records that would be permanently deleted."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset preview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate reset preview"
        )


@router.post("/data/organization/{organization_id}", response_model=OrganizationDataResetResponse)
async def reset_organization_data(
    organization_id: int,
    reset_request: DataResetRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_data_reset_permission)
):
    """Reset data for a specific organization"""
    try:
        # Verify organization exists
        organization = db.query(Organization).filter(Organization.id == organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )
        
        # Check if user can reset data for this organization
        if not PermissionChecker.can_reset_organization_data(current_user, organization_id):
            PermissionChecker.require_permission(
                Permission.RESET_ANY_DATA,
                current_user,
                db,
                request,
                organization_id
            )
        
        # Validate safety confirmation
        if not reset_request.confirm_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="confirm_reset must be True to proceed with data reset"
            )
        
        # Set the organization ID in the request
        reset_request.organization_id = organization_id
        reset_request.scope = ResetScope.ORGANIZATION
        
        # Perform the reset
        reset_response = ResetService.reset_organization_data(
            db=db,
            organization_id=organization_id,
            admin_user=current_user,
            reset_request=reset_request,
            request=request
        )
        
        logger.info(f"Organization {organization_id} data reset completed by {current_user.email}")
        return reset_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Organization data reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset organization data"
        )


@router.post("/data/all", response_model=DataResetResponse)
async def reset_all_organizations_data(
    reset_request: DataResetRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Reset data for all organizations (super admin only)"""
    try:
        # Only super admin can perform global reset
        PermissionChecker.require_permission(
            Permission.RESET_ANY_DATA,
            current_user,
            db,
            request
        )
        
        # Validate safety confirmation
        if not reset_request.confirm_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="confirm_reset must be True to proceed with global data reset"
            )
        
        # Additional safety check for global reset
        if reset_request.reset_type == DataResetType.FULL_RESET:
            logger.warning(f"DANGEROUS OPERATION: Full global data reset initiated by {current_user.email}")
        
        # Set the scope
        reset_request.scope = ResetScope.ALL_ORGANIZATIONS
        
        # Perform the reset
        reset_response = ResetService.reset_all_organizations_data(
            db=db,
            admin_user=current_user,
            reset_request=reset_request,
            request=request
        )
        
        logger.info(f"Global data reset completed by {current_user.email}")
        return reset_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global data reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset global data"
        )


@router.get("/data/organizations/{organization_id}/summary")
async def get_organization_data_summary(
    organization_id: int,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get summary of data in an organization"""
    try:
        # Verify organization exists
        organization = db.query(Organization).filter(Organization.id == organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {organization_id} not found"
            )
        
        # Check organization access
        if not PermissionChecker.can_access_organization(current_user, organization_id):
            PermissionChecker.require_organization_access(current_user, organization_id, db, request)
        
        # Get data counts
        from app.models.base import Stock, Product, Customer, Vendor, Company
        
        summary = {
            "organization_id": organization_id,
            "organization_name": organization.name,
            "data_counts": {
                "users": db.query(User).filter(User.organization_id == organization_id).count(),
                "products": db.query(Product).filter(Product.organization_id == organization_id).count(),
                "customers": db.query(Customer).filter(Customer.organization_id == organization_id).count(),
                "vendors": db.query(Vendor).filter(Vendor.organization_id == organization_id).count(),
                "companies": db.query(Company).filter(Company.organization_id == organization_id).count(),
                "stock_entries": db.query(Stock).filter(Stock.organization_id == organization_id).count(),
            }
        }
        
        # Calculate total records
        summary["total_records"] = sum(summary["data_counts"].values())
        
        # Log data summary access
        AuditLogger.log_data_reset(
            db=db,
            admin_email=current_user.email,
            admin_user_id=current_user.id,
            organization_id=organization_id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_scope="ORGANIZATION_SUMMARY",
            details={
                "action": "get_data_summary",
                "summary": summary
            }
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data summary"
        )


@router.get("/data/summary")
async def get_global_data_summary(
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Get summary of data across all organizations (super admin only)"""
    try:
        # Get all organizations
        organizations = db.query(Organization).all()
        
        from app.models.base import Stock, Product, Customer, Vendor, Company
        
        global_summary = {
            "total_organizations": len(organizations),
            "organizations": []
        }
        
        total_counts = {
            "users": 0,
            "products": 0,
            "customers": 0,
            "vendors": 0,
            "companies": 0,
            "stock_entries": 0,
        }
        
        for org in organizations:
            org_counts = {
                "users": db.query(User).filter(User.organization_id == org.id).count(),
                "products": db.query(Product).filter(Product.organization_id == org.id).count(),
                "customers": db.query(Customer).filter(Customer.organization_id == org.id).count(),
                "vendors": db.query(Vendor).filter(Vendor.organization_id == org.id).count(),
                "companies": db.query(Company).filter(Company.organization_id == org.id).count(),
                "stock_entries": db.query(Stock).filter(Stock.organization_id == org.id).count(),
            }
            
            # Add to totals
            for key, count in org_counts.items():
                total_counts[key] += count
            
            global_summary["organizations"].append({
                "id": org.id,
                "name": org.name,
                "status": org.status,
                "data_counts": org_counts,
                "total_records": sum(org_counts.values())
            })
        
        global_summary["global_totals"] = total_counts
        global_summary["total_records"] = sum(total_counts.values())
        
        # Log global summary access
        AuditLogger.log_data_reset(
            db=db,
            admin_email=current_user.email,
            admin_user_id=current_user.id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_scope="GLOBAL_SUMMARY",
            details={
                "action": "get_global_summary",
                "total_organizations": global_summary["total_organizations"],
                "total_records": global_summary["total_records"]
            }
        )
        
        return global_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global data summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get global data summary"
        )


@router.post("/emergency/access", response_model=EmergencyAccessResponse)
async def request_emergency_access(
    emergency_request: EmergencyAccessRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Request emergency access with special logging (super admin only)"""
    try:
        # Generate emergency token (this would typically have special restrictions)
        from app.core.security import create_access_token
        from datetime import timedelta
        
        emergency_token = create_access_token(
            subject=current_user.email,
            organization_id=emergency_request.organization_id,
            expires_delta=timedelta(minutes=30)  # Short-lived token
        )
        
        restrictions = [
            "Limited to 30 minutes",
            "Read-only access recommended",
            "All actions heavily audited",
            "Requires justification for data modifications"
        ]
        
        # Log emergency access request
        AuditLogger.log_data_reset(
            db=db,
            admin_email=current_user.email,
            admin_user_id=current_user.id,
            organization_id=emergency_request.organization_id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_scope="EMERGENCY_ACCESS",
            details={
                "action": "emergency_access_request",
                "reason": emergency_request.reason,
                "restrictions": restrictions,
                "token_expires_minutes": 30
            }
        )
        
        logger.warning(f"EMERGENCY ACCESS GRANTED to {current_user.email}: {emergency_request.reason}")
        
        return EmergencyAccessResponse(
            message="Emergency access granted",
            emergency_token=emergency_token,
            valid_for_minutes=30,
            restrictions=restrictions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant emergency access"
        )


@router.get("/audit/logs")
async def get_reset_audit_logs(
    organization_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get audit logs for reset operations"""
    try:
        # Check permissions
        if organization_id:
            if not PermissionChecker.can_access_organization(current_user, organization_id):
                PermissionChecker.require_organization_access(current_user, organization_id, db, request)
        else:
            # Viewing all audit logs requires super admin
            PermissionChecker.require_permission(
                Permission.VIEW_ALL_AUDIT_LOGS,
                current_user,
                db,
                request
            )
        
        # Build query
        from app.models.base import AuditLog
        query = db.query(AuditLog)
        
        # Filter by organization if specified
        if organization_id:
            query = query.filter(AuditLog.organization_id == organization_id)
        
        # Filter by event type if specified
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        # Filter to reset-related events
        reset_event_types = ["PASSWORD_RESET", "DATA_RESET", "SECURITY"]
        query = query.filter(AuditLog.event_type.in_(reset_event_types))
        
        # Order by timestamp descending
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Apply pagination
        audit_logs = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        logs_response = []
        for log in audit_logs:
            logs_response.append({
                "id": log.id,
                "event_type": log.event_type,
                "action": log.action,
                "user_email": log.user_email,
                "organization_id": log.organization_id,
                "success": log.success,
                "details": log.details,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "user_agent": log.user_agent
            })
        
        # Log audit log access
        AuditLogger.log_data_reset(
            db=db,
            admin_email=current_user.email,
            admin_user_id=current_user.id,
            organization_id=organization_id,
            success=True,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            reset_scope="AUDIT_LOG_ACCESS",
            details={
                "action": "view_audit_logs",
                "filters": {
                    "organization_id": organization_id,
                    "event_type": event_type
                },
                "result_count": len(logs_response)
            }
        )
        
        return {
            "audit_logs": logs_response,
            "total_count": len(logs_response),
            "filters": {
                "organization_id": organization_id,
                "event_type": event_type
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs"
        )