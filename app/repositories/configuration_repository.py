from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from azure.cosmos import ContainerProxy
from app.models.configuration import Configuration, ConfigurationQuery
from app.repositories.cosmos_client import cosmos_client
from app.core.logger import logger


class ConfigurationRepository:
    def __init__(self) -> None:
        pass

    def _get_container(self) -> ContainerProxy:
        """Get container with lazy initialization check"""
        return cosmos_client.get_container()

    async def create(self, config: Configuration) -> Configuration:
        """Create a new configuration"""
        try:
            container = self._get_container()
            config_dict = config.model_dump(by_alias=True)
            # Convert datetime objects to ISO format strings
            config_dict["created_at"] = config.created_at.isoformat()
            config_dict["updated_at"] = config.updated_at.isoformat()

            result = container.create_item(body=config_dict)
            logger.info(f"Configuration created: {result['id']}")
            return Configuration(**result)
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            raise

    async def find_by_id(self, config_id: str, tenant_id: str) -> Optional[Configuration]:
        """Find configuration by ID"""
        try:
            container = self._get_container()
            result = container.read_item(
                item=config_id, partition_key=tenant_id)
            return Configuration(**result)
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code == 404:
                return None
            logger.error(f"Error finding configuration: {e}")
            raise

    async def find_by_key(self, key: str, tenant_id: str) -> Optional[Configuration]:
        """Find configuration by key"""
        try:
            container = self._get_container()
            query = "SELECT * FROM c WHERE c.key = @key AND c.tenant_id = @tenant_id"
            parameters = [{"name": "@key", "value": key},
                          {"name": "@tenant_id", "value": tenant_id}]

            results = list(
                container.query_items(
                    query=query, parameters=parameters, enable_cross_partition_query=False
                )
            )
            return Configuration(**results[0]) if results else None
        except Exception as e:
            logger.error(f"Error finding configuration by key: {e}")
            raise

    async def find_all(self, query: ConfigurationQuery) -> List[Configuration]:
        """Find all configurations matching query"""
        try:
            container = self._get_container()
            query_text = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
            parameters = [{"name": "@tenant_id", "value": query.tenant_id}]

            if query.key:
                query_text += " AND c.key = @key"
                parameters.append({"name": "@key", "value": query.key})

            if query.tags:
                query_text += " AND ARRAY_CONTAINS(c.tags, @tag)"
                parameters.append({"name": "@tag", "value": query.tags[0]})

            results = list(
                container.query_items(
                    query=query_text, parameters=parameters, enable_cross_partition_query=False
                )
            )
            return [Configuration(**r) for r in results]
        except Exception as e:
            logger.error(f"Error finding configurations: {e}")
            raise

    async def update(
        self, config_id: str, tenant_id: str, updates: dict
    ) -> Configuration:
        """Update configuration"""
        try:
            container = self._get_container()
            existing = await self.find_by_id(config_id, tenant_id)
            if not existing:
                raise ValueError("Configuration not found")

            updated_dict = existing.model_dump(by_alias=True)
            updated_dict.update(updates)
            updated_dict["version"] = existing.version + 1
            updated_dict["updated_at"] = datetime.utcnow().isoformat()

            result = container.replace_item(item=config_id, body=updated_dict)
            logger.info(f"Configuration updated: {config_id}")
            return Configuration(**result)
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            raise

    async def delete(self, config_id: str, tenant_id: str) -> None:
        """Delete configuration"""
        try:
            container = self._get_container()
            container.delete_item(item=config_id, partition_key=tenant_id)
            logger.info(f"Configuration deleted: {config_id}")
        except Exception as e:
            logger.error(f"Error deleting configuration: {e}")
            raise
