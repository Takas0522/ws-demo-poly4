from fastapi import APIRouter, Depends, Query, status, Path
from typing import List, Optional, Dict, Any
from app.models.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    AssignServiceRequest,
    TenantServiceResponse,
    ServiceAnalytics,
)
from app.models.auth import JWTPayload
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_permission
from app.middleware.tenant_isolation import verify_tenant_access
from app.services.service_management import ServiceManagementService
from app.repositories.service_repository import ServiceRepository, TenantRepository
from app.repositories.cache_service import cache_service

router = APIRouter(tags=["services"])

# Initialize repositories and service
service_repo = ServiceRepository()
tenant_repo = TenantRepository()
service_management = ServiceManagementService(service_repo, tenant_repo, cache_service)


# Service Catalog CRUD APIs


@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service: ServiceCreate,
    current_user: JWTPayload = Depends(require_permission("services.create", scope="global")),
) -> ServiceResponse:
    """
    Create a new service (Global admin only).

    All services are stored in the system-internal tenant.
    """
    return await service_management.create_service(service, current_user.sub)


@router.get("/services", response_model=List[ServiceResponse])
async def list_services(
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'active', 'inactive')"),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> List[ServiceResponse]:
    """
    List all services with optional filters.

    Uses Redis caching for improved performance (10 minutes TTL).
    """
    return await service_management.list_services(status=status, category=category)


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str = Path(..., description="Service ID"),
) -> ServiceResponse:
    """Get a specific service by ID."""
    return await service_management.get_service(service_id)


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    *,
    service_id: str = Path(..., description="Service ID"),
    updates: ServiceUpdate,
    current_user: JWTPayload = Depends(require_permission("services.update", scope="global")),
) -> ServiceResponse:
    """Update a service (Global admin only)."""
    return await service_management.update_service(service_id, updates, current_user.sub)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: str = Path(..., description="Service ID"),
    current_user: JWTPayload = Depends(require_permission("services.delete", scope="global")),
) -> None:
    """Delete a service (Global admin only)."""
    await service_management.delete_service(service_id)


# Tenant Service Assignment APIs


@router.post(
    "/tenants/{tenant_id}/services",
    response_model=TenantServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_service_to_tenant(
    *,
    tenant_id: str = Path(..., description="Tenant ID"),
    request: AssignServiceRequest,
    current_user: JWTPayload = Depends(require_permission("services.update")),
) -> TenantServiceResponse:
    """
    Assign a service to a tenant.

    Validates that the tenant's subscription plan meets the service requirements.
    """
    verify_tenant_access(current_user, tenant_id)
    result = await service_management.assign_service_to_tenant(tenant_id, request)
    return TenantServiceResponse(**result)


@router.get("/tenants/{tenant_id}/services", response_model=List[ServiceResponse])
async def get_tenant_services(
    tenant_id: str = Path(..., description="Tenant ID"),
    current_user: JWTPayload = Depends(require_permission("services.read")),
) -> List[ServiceResponse]:
    """
    Get all services assigned to a tenant.

    Uses Redis caching for improved performance (10 minutes TTL).
    """
    verify_tenant_access(current_user, tenant_id)
    return await service_management.get_tenant_services(tenant_id)


@router.delete(
    "/tenants/{tenant_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_service_from_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    service_id: str = Path(..., description="Service ID"),
    current_user: JWTPayload = Depends(require_permission("services.delete")),
) -> None:
    """
    Remove (disable) a service from a tenant.

    The service assignment is disabled rather than deleted for audit purposes.
    """
    verify_tenant_access(current_user, tenant_id)
    await service_management.remove_service_from_tenant(tenant_id, service_id)


# Analytics APIs


@router.get("/analytics/services/usage", response_model=ServiceAnalytics)
async def get_service_usage_stats(
    current_user: JWTPayload = Depends(require_permission("analytics.read", scope="global")),
) -> ServiceAnalytics:
    """
    Get service usage statistics across all tenants (Global admin only).

    Returns aggregated data for dashboard display.
    """
    return await service_management.get_service_usage_stats()


@router.get("/analytics/tenants/{tenant_id}/service-activity", response_model=Dict[str, Any])
async def get_tenant_service_activity(
    tenant_id: str = Path(..., description="Tenant ID"),
    current_user: JWTPayload = Depends(require_permission("analytics.read")),
) -> Dict[str, Any]:
    """
    Get service activity for a specific tenant.

    Returns summary of enabled/disabled services and activity history.
    """
    verify_tenant_access(current_user, tenant_id)
    return await service_management.get_tenant_service_activity(tenant_id)
