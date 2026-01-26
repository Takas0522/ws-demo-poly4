"""Services API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import CurrentUser, require_global_admin, require_viewer
from app.core.database import get_db_client
from app.schemas.service import (
    ServiceListResponse,
    ServiceResponse,
    TenantServiceListResponse,
    TenantServiceResponse,
    UpdateTenantServicesRequest,
    UpdateTenantServicesResponse,
)
from app.services.service_service import ServiceService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service_service() -> ServiceService:
    """Dependency to get ServiceService instance."""
    db_client = get_db_client()
    return ServiceService(db_client)


@router.get(
    "/services",
    response_model=ServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all services",
    description=(
        "Retrieve a list of all available services. "
        "Requires viewer role or higher."
    ),
)
async def get_services(
    current_user: CurrentUser = Depends(require_viewer),
    service: ServiceService = Depends(get_service_service),
) -> ServiceListResponse:
    """
    Get all services.

    Args:
        current_user: Authenticated user with viewer role or higher
        service: Service service instance

    Returns:
        ServiceListResponse: List of all services
    """
    try:
        services = await service.get_all_services()
        service_responses = [
            ServiceResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                roleEndpoint=s.roleEndpoint,
                isCore=s.isCore,
                isActive=s.isActive,
                createdAt=s.createdAt,
                updatedAt=s.updatedAt,
            )
            for s in services
        ]

        logger.info(f"User {current_user.user_id} retrieved {len(services)} services")
        return ServiceListResponse(data=service_responses)

    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve services",
        )


@router.get(
    "/tenants/{tenant_id}/services",
    response_model=TenantServiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant assigned services",
    description=(
        "Retrieve all services assigned to a specific tenant. "
        "Requires viewer role or higher."
    ),
)
async def get_tenant_services(
    tenant_id: str,
    current_user: CurrentUser = Depends(require_viewer),
    service: ServiceService = Depends(get_service_service),
) -> TenantServiceListResponse:
    """
    Get services assigned to a tenant.

    Args:
        tenant_id: Tenant ID
        current_user: Authenticated user with viewer role or higher
        service: Service service instance

    Returns:
        TenantServiceListResponse: List of services assigned to the tenant
    """
    try:
        tenant_services = await service.get_tenant_services(tenant_id)
        service_responses = [
            TenantServiceResponse(
                serviceId=ts["serviceId"],
                serviceName=ts["serviceName"],
                assignedAt=ts["assignedAt"],
                assignedBy=ts["assignedBy"],
            )
            for ts in tenant_services
        ]

        logger.info(
            f"User {current_user.user_id} retrieved "
            f"{len(tenant_services)} services for tenant {tenant_id}"
        )
        return TenantServiceListResponse(data=service_responses)

    except Exception as e:
        logger.error(f"Error getting tenant services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve services for tenant {tenant_id}",
        )


@router.put(
    "/tenants/{tenant_id}/services",
    response_model=UpdateTenantServicesResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tenant service assignments",
    description=(
        "Update the list of services assigned to a tenant. "
        "Requires global admin role."
    ),
)
async def update_tenant_services(
    tenant_id: str,
    request: UpdateTenantServicesRequest,
    current_user: CurrentUser = Depends(require_global_admin),
    service: ServiceService = Depends(get_service_service),
) -> UpdateTenantServicesResponse:
    """
    Update services assigned to a tenant.

    This replaces all existing service assignments with the new list.

    Args:
        tenant_id: Tenant ID
        request: Request containing list of service IDs to assign
        current_user: Authenticated user with global admin role
        service: Service service instance

    Returns:
        UpdateTenantServicesResponse: Updated service assignment information

    Raises:
        HTTPException: If any service ID is invalid
    """
    try:
        assigned_services = await service.update_tenant_services(
            tenant_id=tenant_id,
            service_ids=request.serviceIds,
            user_id=current_user.user_id,
        )

        logger.info(
            f"User {current_user.user_id} updated services for "
            f"tenant {tenant_id}: {assigned_services}"
        )

        return UpdateTenantServicesResponse(
            tenantId=tenant_id,
            assignedServices=assigned_services,
            message="Service assignments updated successfully",
        )

    except ValueError as e:
        logger.warning(f"Invalid service ID in request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating tenant services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update services for tenant {tenant_id}",
        )
