from typing import List, Optional, Dict, Any
from datetime import datetime
from app.repositories.cosmos_client import cosmos_client
from app.core.logger import logger


class ServiceRepository:
    """Repository for service data access"""

    def __init__(self):
        self.container_name = "services"
        self._container = None

    async def initialize(self) -> None:
        """Initialize services container"""
        try:
            if cosmos_client.database:
                self._container = cosmos_client.database.create_container_if_not_exists(
                    id=self.container_name, partition_key={"paths": ["/tenantId"]}
                )
                logger.info(f"Services container initialized: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize services container: {e}")

    def get_container(self):
        """Get the container, initializing if necessary"""
        if not self._container and cosmos_client.database:
            try:
                self._container = cosmos_client.database.create_container_if_not_exists(
                    id=self.container_name, partition_key={"paths": ["/tenantId"]}
                )
            except Exception as e:
                logger.error(f"Failed to get services container: {e}")
                raise RuntimeError("Services container not available")
        return self._container

    async def create(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service"""
        container = self.get_container()
        service["tenantId"] = "system-internal"
        created = container.create_item(body=service)
        logger.info(f"Service created: {created['id']}")
        return created

    async def get_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service by ID"""
        try:
            container = self.get_container()
            item = container.read_item(item=service_id, partition_key="system-internal")
            return item
        except Exception as e:
            logger.debug(f"Service not found: {service_id} - {e}")
            return None

    async def list_all(
        self, status: Optional[str] = None, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all services with optional filters"""
        container = self.get_container()

        # Build query
        query = "SELECT * FROM c WHERE c.tenantId = 'system-internal'"
        parameters = []

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status})

        if category:
            query += " AND c.category = @category"
            parameters.append({"name": "@category", "value": category})

        # Execute query
        items = list(
            container.query_items(
                query=query, parameters=parameters, partition_key="system-internal"
            )
        )

        logger.debug(f"Listed {len(items)} services")
        return items

    async def update(self, service_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a service"""
        container = self.get_container()

        # Get existing service
        service = await self.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service not found: {service_id}")

        # Apply updates
        service.update(updates)
        service["updatedAt"] = datetime.utcnow().isoformat()

        # Save
        updated = container.upsert_item(body=service)
        logger.info(f"Service updated: {service_id}")
        return updated

    async def delete(self, service_id: str) -> None:
        """Delete a service"""
        container = self.get_container()
        container.delete_item(item=service_id, partition_key="system-internal")
        logger.info(f"Service deleted: {service_id}")


class TenantRepository:
    """Repository for tenant data access"""

    def __init__(self):
        self.container_name = "tenants"
        self._container = None

    async def initialize(self) -> None:
        """Initialize tenants container"""
        try:
            if cosmos_client.database:
                self._container = cosmos_client.database.create_container_if_not_exists(
                    id=self.container_name, partition_key={"paths": ["/id"]}
                )
                logger.info(f"Tenants container initialized: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize tenants container: {e}")

    def get_container(self):
        """Get the container, initializing if necessary"""
        if not self._container and cosmos_client.database:
            try:
                self._container = cosmos_client.database.create_container_if_not_exists(
                    id=self.container_name, partition_key={"paths": ["/id"]}
                )
            except Exception as e:
                logger.error(f"Failed to get tenants container: {e}")
                raise RuntimeError("Tenants container not available")
        return self._container

    async def get_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID"""
        try:
            container = self.get_container()
            item = container.read_item(item=tenant_id, partition_key=tenant_id)
            return item
        except Exception as e:
            logger.debug(f"Tenant not found: {tenant_id} - {e}")
            return None

    async def update(self, tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Update tenant"""
        container = self.get_container()
        tenant["updatedAt"] = datetime.utcnow().isoformat()
        updated = container.upsert_item(body=tenant)
        logger.info(f"Tenant updated: {tenant['id']}")
        return updated

    async def list_all(self) -> List[Dict[str, Any]]:
        """List all tenants"""
        container = self.get_container()
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        logger.debug(f"Listed {len(items)} tenants")
        return items
