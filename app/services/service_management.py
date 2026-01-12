from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from app.repositories.service_repository import ServiceRepository, TenantRepository
from app.repositories.cache_service import CacheService
from app.models.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    AssignServiceRequest,
    TenantService,
    ServiceUsageStats,
    ServiceAnalytics,
)
from app.core.logger import logger
import json


class ServiceManagementService:
    """Service for managing services and tenant assignments"""

    def __init__(
        self, service_repo: ServiceRepository, tenant_repo: TenantRepository, cache: CacheService
    ):
        self.service_repo = service_repo
        self.tenant_repo = tenant_repo
        self.cache = cache

    async def create_service(self, service: ServiceCreate, created_by: str) -> ServiceResponse:
        """Create a new service"""
        # Generate service ID
        service_id = f"service-{service.name}"

        # Check if service already exists
        existing = await self.service_repo.get_by_id(service_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service with name '{service.name}' already exists",
            )

        # Create service document
        service_doc = {
            "id": service_id,
            "tenantId": "system-internal",
            "name": service.name,
            "displayName": service.displayName,
            "description": service.description,
            "category": service.category,
            "status": "active",
            "requiredPlan": service.requiredPlan,
            "features": service.features,
            "pricing": [p.model_dump() for p in service.pricing],
            "metadata": service.metadata or {},
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
            "createdBy": created_by,
            "updatedBy": created_by,
        }

        # Save to database
        created = await self.service_repo.create(service_doc)

        # Invalidate cache
        await self.cache.delete("services:all")

        logger.info(f"Service created: {service_id} by {created_by}")
        return ServiceResponse(**created)

    async def list_services(
        self, status: Optional[str] = None, category: Optional[str] = None
    ) -> List[ServiceResponse]:
        """List all services with optional filters and caching"""
        cache_key = "services:all"

        # Try to get from cache
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug("Services loaded from cache")
            services = cached
        else:
            # Load from database
            services = await self.service_repo.list_all()

            # Cache for 10 minutes (600 seconds)
            await self.cache.set(cache_key, services, ttl=600)
            logger.debug(f"Services loaded from database and cached: {len(services)}")

        # Apply filters
        if status:
            services = [s for s in services if s.get("status") == status]
        if category:
            services = [s for s in services if s.get("category") == category]

        return [ServiceResponse(**s) for s in services]

    async def get_service(self, service_id: str) -> ServiceResponse:
        """Get a service by ID"""
        service = await self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )
        return ServiceResponse(**service)

    async def update_service(
        self, service_id: str, updates: ServiceUpdate, updated_by: str
    ) -> ServiceResponse:
        """Update a service"""
        # Get existing service
        service = await self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )

        # Build update dict
        update_dict = {}
        if updates.displayName is not None:
            update_dict["displayName"] = updates.displayName
        if updates.description is not None:
            update_dict["description"] = updates.description
        if updates.category is not None:
            update_dict["category"] = updates.category
        if updates.status is not None:
            update_dict["status"] = updates.status
        if updates.requiredPlan is not None:
            update_dict["requiredPlan"] = updates.requiredPlan
        if updates.features is not None:
            update_dict["features"] = updates.features
        if updates.pricing is not None:
            update_dict["pricing"] = [p.model_dump() for p in updates.pricing]
        if updates.metadata is not None:
            update_dict["metadata"] = updates.metadata

        update_dict["updatedBy"] = updated_by

        # Update in database
        updated = await self.service_repo.update(service_id, update_dict)

        # Invalidate cache
        await self.cache.delete("services:all")

        logger.info(f"Service updated: {service_id} by {updated_by}")
        return ServiceResponse(**updated)

    async def delete_service(self, service_id: str) -> None:
        """Delete a service"""
        # Check if service exists
        service = await self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )

        # Delete from database
        await self.service_repo.delete(service_id)

        # Invalidate cache
        await self.cache.delete("services:all")

        logger.info(f"Service deleted: {service_id}")

    async def assign_service_to_tenant(
        self, tenant_id: str, request: AssignServiceRequest
    ) -> Dict[str, Any]:
        """Assign a service to a tenant"""
        # Check if service exists
        service = await self.service_repo.get_by_id(request.serviceId)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )

        # Get tenant
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        # Check plan requirement
        tenant_plan = tenant.get("subscription", {}).get("plan", "free")
        required_plans = service.get("requiredPlan", [])
        if required_plans and tenant_plan not in required_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This service requires one of the following plans: {', '.join(required_plans)}",
            )

        # Initialize services array if not exists
        if "services" not in tenant:
            tenant["services"] = []

        # Check for duplicates
        if any(s.get("serviceId") == request.serviceId for s in tenant["services"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service is already assigned to this tenant",
            )

        # Add service assignment
        tenant["services"].append(
            {
                "serviceId": request.serviceId,
                "enabled": True,
                "enabledAt": datetime.utcnow().isoformat(),
                "disabledAt": None,
            }
        )

        # Update tenant
        updated_tenant = await self.tenant_repo.update(tenant)

        # Invalidate cache
        await self.cache.delete(f"tenant:services:{tenant_id}")

        logger.info(f"Service {request.serviceId} assigned to tenant {tenant_id}")
        return {"success": True, "tenant": updated_tenant}

    async def get_tenant_services(self, tenant_id: str) -> List[ServiceResponse]:
        """Get all services assigned to a tenant with caching"""
        cache_key = f"tenant:services:{tenant_id}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Tenant services loaded from cache: {tenant_id}")
            return [ServiceResponse(**s) for s in cached]

        # Get tenant
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        # Get enabled service IDs
        service_ids = [
            s["serviceId"] for s in tenant.get("services", []) if s.get("enabled", False)
        ]

        # Load service details
        services = []
        for service_id in service_ids:
            service = await self.service_repo.get_by_id(service_id)
            if service:
                services.append(service)

        # Cache for 10 minutes
        await self.cache.set(cache_key, services, ttl=600)

        logger.debug(f"Tenant services loaded from database: {tenant_id}, count: {len(services)}")
        return [ServiceResponse(**s) for s in services]

    async def remove_service_from_tenant(self, tenant_id: str, service_id: str) -> None:
        """Remove (disable) a service from a tenant"""
        # Get tenant
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        # Find and disable service
        found = False
        for svc in tenant.get("services", []):
            if svc.get("serviceId") == service_id:
                svc["enabled"] = False
                svc["disabledAt"] = datetime.utcnow().isoformat()
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not assigned to this tenant",
            )

        # Update tenant
        await self.tenant_repo.update(tenant)

        # Invalidate cache
        await self.cache.delete(f"tenant:services:{tenant_id}")

        logger.info(f"Service {service_id} removed from tenant {tenant_id}")

    async def get_service_usage_stats(self) -> ServiceAnalytics:
        """Get service usage statistics across all tenants"""
        # Get all services
        all_services = await self.service_repo.list_all()
        total_services = len(all_services)
        active_services = len([s for s in all_services if s.get("status") == "active"])

        # Get all tenants
        all_tenants = await self.tenant_repo.list_all()

        # Count service usage
        service_usage_map: Dict[str, int] = {}
        for tenant in all_tenants:
            for svc in tenant.get("services", []):
                if svc.get("enabled", False):
                    service_id = svc.get("serviceId")
                    service_usage_map[service_id] = service_usage_map.get(service_id, 0) + 1

        # Build usage stats
        service_usage = [
            ServiceUsageStats(serviceId=service_id, tenantCount=count, userCount=0)
            for service_id, count in service_usage_map.items()
        ]

        logger.info(f"Service usage stats calculated: {len(service_usage)} services in use")
        return ServiceAnalytics(
            totalServices=total_services,
            activeServices=active_services,
            serviceUsage=service_usage,
        )

    async def get_tenant_service_activity(self, tenant_id: str) -> Dict[str, Any]:
        """Get service activity for a specific tenant"""
        # Get tenant
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )

        # Get tenant's services
        services = tenant.get("services", [])

        # Build activity summary
        activity = {
            "tenantId": tenant_id,
            "totalServices": len(services),
            "enabledServices": len([s for s in services if s.get("enabled", False)]),
            "disabledServices": len([s for s in services if not s.get("enabled", True)]),
            "services": services,
        }

        logger.debug(f"Tenant service activity retrieved: {tenant_id}")
        return activity
