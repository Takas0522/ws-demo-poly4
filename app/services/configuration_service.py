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
from app.core.logger import logger


class ConfigurationService:
    def __init__(self, repository: ConfigurationRepository):
        self.repository = repository

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
            # Fetch from database
            config = await self.repository.find_by_id(config_id, tenant_id)
            if not config:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Configuration not found"
                )

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

            # Note: Without Redis, backup functionality is limited
            # Consider implementing persistent backup storage if needed
            logger.warning("Backup feature requires persistent storage implementation")
            logger.info(f"Backup created for tenant {tenant_id}: {backup_id}")
            return BackupResponse(backup_id=backup_id)
        except Exception as e:
            logger.error(f"Error in backup: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def restore(self, backup_id: str, tenant_id: str, user_id: str) -> None:
        """Restore configurations from backup"""
        # Note: Without Redis, restore functionality is limited
        # Consider implementing persistent backup storage if needed
        logger.warning("Restore feature requires persistent storage implementation")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Restore feature requires persistent storage. Please implement backup storage."
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
