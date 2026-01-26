"""Service layer for managing services and tenant service assignments."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.database import CosmosDBClient
from app.models.service import Service
from app.models.tenant_service_assignment import TenantServiceAssignment

logger = logging.getLogger(__name__)


def format_datetime_utc(dt: datetime) -> str:
    """
    Format datetime as ISO 8601 string with UTC timezone.

    Args:
        dt: Datetime object to format

    Returns:
        ISO 8601 formatted string with 'Z' suffix for UTC
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ServiceService:
    """Service for managing services and service assignments."""

    def __init__(self, db_client: CosmosDBClient) -> None:
        """
        Initialize the service.

        Args:
            db_client: Cosmos DB client instance
        """
        self.db_client = db_client

    async def get_all_services(self) -> List[Service]:
        """
        Get all services.

        Returns:
            List of all services
        """
        try:
            container = self.db_client.services_container
            query = "SELECT * FROM c ORDER BY c.name"
            items = list(
                container.query_items(
                    query=query,
                    enable_cross_partition_query=True,
                )
            )

            services = [Service(**item) for item in items]
            logger.info(f"Retrieved {len(services)} services")
            return services

        except Exception as e:
            logger.error(f"Error retrieving services: {e}")
            raise

    async def get_service_by_id(self, service_id: str) -> Optional[Service]:
        """
        Get a service by ID.

        Args:
            service_id: Service ID

        Returns:
            Service if found, None otherwise
        """
        try:
            container = self.db_client.services_container
            item = container.read_item(item=service_id, partition_key=service_id)
            return Service(**item)

        except CosmosResourceNotFoundError:
            logger.warning(f"Service not found: {service_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving service {service_id}: {e}")
            raise

    async def get_tenant_services(self, tenant_id: str) -> List[dict]:
        """
        Get all services assigned to a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            List of services with assignment information
        """
        try:
            # Get assignments for the tenant
            assignments_container = self.db_client.service_assignments_container
            assignments_query = "SELECT * FROM c WHERE c.tenantId = @tenantId"
            assignment_items = list(
                assignments_container.query_items(
                    query=assignments_query,
                    parameters=[{"name": "@tenantId", "value": tenant_id}],
                    enable_cross_partition_query=True,
                )
            )

            if not assignment_items:
                logger.info(f"No services assigned to tenant {tenant_id}")
                return []

            # Get service details for each assignment
            services_container = self.db_client.services_container
            tenant_services = []

            for assignment in assignment_items:
                service_id = assignment["serviceId"]
                try:
                    service_item = services_container.read_item(
                        item=service_id, partition_key=service_id
                    )
                    tenant_services.append(
                        {
                            "serviceId": service_item["id"],
                            "serviceName": service_item["name"],
                            "assignedAt": assignment["assignedAt"],
                            "assignedBy": assignment["assignedBy"],
                        }
                    )
                except CosmosResourceNotFoundError:
                    logger.warning(
                        f"Service {service_id} not found for "
                        f"assignment {assignment['id']}"
                    )
                    continue

            logger.info(
                f"Retrieved {len(tenant_services)} services for " f"tenant {tenant_id}"
            )
            return tenant_services

        except Exception as e:
            logger.error(f"Error retrieving tenant services for {tenant_id}: {e}")
            raise

    async def update_tenant_services(
        self, tenant_id: str, service_ids: List[str], user_id: str
    ) -> List[str]:
        """
        Update service assignments for a tenant.

        This replaces all existing assignments with the new list.

        Args:
            tenant_id: Tenant ID
            service_ids: List of service IDs to assign
            user_id: User ID performing the assignment

        Returns:
            List of assigned service IDs

        Raises:
            ValueError: If any service ID is invalid
        """
        try:
            # Validate all service IDs exist
            services_container = self.db_client.services_container
            for service_id in service_ids:
                try:
                    services_container.read_item(
                        item=service_id, partition_key=service_id
                    )
                except CosmosResourceNotFoundError:
                    raise ValueError(f"Service not found: {service_id}")

            # Get existing assignments
            assignments_container = self.db_client.service_assignments_container
            existing_query = "SELECT * FROM c WHERE c.tenantId = @tenantId"
            existing_items = list(
                assignments_container.query_items(
                    query=existing_query,
                    parameters=[{"name": "@tenantId", "value": tenant_id}],
                    enable_cross_partition_query=True,
                )
            )

            existing_service_ids = {item["serviceId"] for item in existing_items}
            new_service_ids = set(service_ids)

            # Determine which to add and which to remove
            to_add = new_service_ids - existing_service_ids
            to_remove = existing_service_ids - new_service_ids

            # Remove old assignments
            for item in existing_items:
                if item["serviceId"] in to_remove:
                    assignments_container.delete_item(
                        item=item["id"], partition_key=item["id"]
                    )
                    logger.info(
                        f"Removed assignment {item['id']} for tenant {tenant_id}"
                    )

            # Add new assignments
            now = format_datetime_utc(datetime.now(timezone.utc))
            for service_id in to_add:
                assignment = TenantServiceAssignment(
                    id=str(uuid4()),
                    tenantId=tenant_id,
                    serviceId=service_id,
                    assignedAt=now,
                    assignedBy=user_id,
                )
                assignments_container.create_item(body=assignment.model_dump())
                logger.info(
                    f"Created assignment for service {service_id} "
                    f"to tenant {tenant_id}"
                )

            logger.info(
                f"Updated tenant {tenant_id} services: "
                f"added {len(to_add)}, removed {len(to_remove)}"
            )
            return service_ids

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating tenant services for {tenant_id}: {e}")
            raise
