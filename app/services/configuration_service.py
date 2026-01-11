from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.models.configuration import (
    Configuration,
    ConfigurationCreate,
    ConfigurationUpdate,
    ConfigurationQuery,
    BackupResponse,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.cache_service import CacheService
from app.core.logger import logger


class ConfigurationService:
    def __init__(self, repository: ConfigurationRepository, cache: CacheService):
        self.repository = repository
        self.cache = cache

    def _get_cache_key(self, config_id: str, tenant_id: str) -> str:
        """Get cache key for configuration"""
        return f"config:{tenant_id}:{config_id}"

    def _get_tenant_cache_pattern(self, tenant_id: str) -> str:
        """Get cache pattern for tenant"""
        return f"config:{tenant_id}:*"

    async def create(self, dto: ConfigurationCreate, user_id: str) -> Configuration:
        """Create new configuration"""
        try:
            # Check if key already exists
            existing = await self.repository.find_by_key(dto.key, dto.tenant_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Configuration with key '{dto.key}' already exists",
                )

            config = Configuration(
                **dto.model_dump(by_alias=True), created_by=user_id, updated_by=user_id
            )
            result = await self.repository.create(config)

            # Cache the new configuration
            cache_key = self._get_cache_key(result.id, result.tenant_id)
            await self.cache.set(cache_key, result.model_dump(by_alias=True, mode="json"))

            logger.info(f"Configuration created: {result.id} by user {user_id}")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def get_by_id(
        self, config_id: str, tenant_id: str, include_inherited: bool = False
    ) -> Configuration:
        """Get configuration by ID"""
        try:
            # Try cache first
            cache_key = self._get_cache_key(config_id, tenant_id)
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Configuration {config_id} retrieved from cache")
                config = Configuration(**cached)
            else:
                # Fetch from database
                config = await self.repository.find_by_id(config_id, tenant_id)
                if not config:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
                    )

                # Cache the result
                await self.cache.set(cache_key, config.model_dump(by_alias=True, mode="json"))

            # Apply inheritance if needed
            if include_inherited and config.parent_config_id:
                config = await self._apply_inheritance(config)

            return config
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def get_by_key(
        self, key: str, tenant_id: str, include_inherited: bool = False
    ) -> Configuration:
        """Get configuration by key"""
        try:
            config = await self.repository.find_by_key(key, tenant_id)
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Configuration with key '{key}' not found",
                )

            if include_inherited and config.parent_config_id:
                config = await self._apply_inheritance(config)

            return config
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_by_key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def list(self, query: ConfigurationQuery) -> List[Configuration]:
        """List configurations"""
        try:
            configs = await self.repository.find_all(query)

            if query.include_inherited:
                processed_configs = []
                for config in configs:
                    if config.parent_config_id:
                        config = await self._apply_inheritance(config)
                    processed_configs.append(config)
                return processed_configs

            return configs
        except Exception as e:
            logger.error(f"Error in list: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def update(
        self, config_id: str, tenant_id: str, dto: ConfigurationUpdate, user_id: str
    ) -> Configuration:
        """Update configuration"""
        try:
            existing = await self.repository.find_by_id(config_id, tenant_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
                )

            updates = dto.model_dump(by_alias=True, exclude_unset=True)
            updates["updated_by"] = user_id

            updated = await self.repository.update(config_id, tenant_id, updates)

            # Invalidate cache
            cache_key = self._get_cache_key(config_id, tenant_id)
            await self.cache.delete(cache_key)

            logger.info(f"Configuration updated: {config_id} by user {user_id}")
            return updated
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def delete(self, config_id: str, tenant_id: str) -> None:
        """Delete configuration"""
        try:
            existing = await self.repository.find_by_id(config_id, tenant_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
                )

            await self.repository.delete(config_id, tenant_id)

            # Invalidate cache
            cache_key = self._get_cache_key(config_id, tenant_id)
            await self.cache.delete(cache_key)

            logger.info(f"Configuration deleted: {config_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in delete: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def backup(
        self, tenant_id: str, user_id: str, description: Optional[str] = None
    ) -> BackupResponse:
        """Create backup of configurations"""
        try:
            configs = await self.repository.find_all(ConfigurationQuery(tenant_id=tenant_id))

            backup_id = f"backup-{tenant_id}-{int(datetime.utcnow().timestamp())}"
            backup_data = {
                "id": backup_id,
                "tenant_id": tenant_id,
                "backup_date": datetime.utcnow().isoformat(),
                "configurations": [c.model_dump(by_alias=True, mode="json") for c in configs],
                "created_by": user_id,
                "description": description,
            }

            # Store backup in cache (7 days TTL)
            await self.cache.set(f"backup:{backup_id}", backup_data, ttl=86400 * 7)

            logger.info(f"Backup created for tenant {tenant_id}: {backup_id}")
            return BackupResponse(backup_id=backup_id)
        except Exception as e:
            logger.error(f"Error in backup: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def restore(self, backup_id: str, tenant_id: str, user_id: str) -> None:
        """Restore configurations from backup"""
        try:
            backup = await self.cache.get(f"backup:{backup_id}")
            if not backup:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found or expired"
                )

            if backup["tenant_id"] != tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot restore backup from different tenant",
                )

            # Restore configurations
            for config_data in backup["configurations"]:
                config_id = config_data["id"]
                existing = await self.repository.find_by_id(config_id, tenant_id)
                
                config_data["updated_by"] = user_id
                
                if existing:
                    await self.repository.update(config_id, tenant_id, config_data)
                else:
                    config = Configuration(**config_data)
                    await self.repository.create(config)

            # Invalidate all tenant cache
            await self.cache.delete_pattern(self._get_tenant_cache_pattern(tenant_id))

            logger.info(f"Backup restored for tenant {tenant_id}: {backup_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in restore: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def _apply_inheritance(self, config: Configuration) -> Configuration:
        """Apply configuration inheritance"""
        if not config.parent_config_id:
            return config

        try:
            parent = await self.repository.find_by_id(config.parent_config_id, config.tenant_id)
            if not parent:
                logger.warning(f"Parent configuration not found: {config.parent_config_id}")
                return config

            # Merge parent values with current config (current config takes precedence)
            inherited_dict = parent.model_dump(by_alias=True)
            config_dict = config.model_dump(by_alias=True)
            
            # Override with child values
            inherited_dict.update({k: v for k, v in config_dict.items() if v is not None})
            inherited_dict["id"] = config.id
            inherited_dict["key"] = config.key
            inherited_dict["value"] = config.value

            return Configuration(**inherited_dict)
        except Exception as e:
            logger.error(f"Error applying inheritance: {e}")
            return config
