from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from app.models.configuration import (
    Configuration,
    ConfigurationCreate,
    ConfigurationUpdate,
    ConfigurationQuery,
    BackupRequest,
    BackupResponse,
    RestoreResponse,
)
from app.models.auth import JWTPayload
from app.middleware.auth import get_current_user
from app.middleware.tenant_isolation import verify_tenant_access
from app.services.configuration_service import ConfigurationService
from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.cache_service import cache_service

router = APIRouter(prefix="/configurations", tags=["configurations"])

# Initialize service
repository = ConfigurationRepository()
config_service = ConfigurationService(repository, cache_service)


@router.post("/", response_model=Configuration, status_code=status.HTTP_201_CREATED)
async def create_configuration(
    dto: ConfigurationCreate, current_user: JWTPayload = Depends(get_current_user)
) -> Configuration:
    """Create a new configuration"""
    verify_tenant_access(current_user, dto.tenant_id)
    return await config_service.create(dto, current_user.sub)


@router.get("/", response_model=List[Configuration])
async def list_configurations(
    key: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    include_inherited: bool = Query(False),
    current_user: JWTPayload = Depends(get_current_user),
) -> List[Configuration]:
    """List all configurations for tenant"""
    tag_list = tags.split(",") if tags else None
    query = ConfigurationQuery(
        tenant_id=current_user.tenant_id, key=key, tags=tag_list, include_inherited=include_inherited
    )
    return await config_service.list(query)


@router.get("/key/{key}", response_model=Configuration)
async def get_configuration_by_key(
    key: str,
    include_inherited: bool = Query(False),
    current_user: JWTPayload = Depends(get_current_user),
) -> Configuration:
    """Get configuration by key"""
    return await config_service.get_by_key(key, current_user.tenant_id, include_inherited)


@router.get("/{config_id}", response_model=Configuration)
async def get_configuration(
    config_id: str,
    include_inherited: bool = Query(False),
    current_user: JWTPayload = Depends(get_current_user),
) -> Configuration:
    """Get configuration by ID"""
    return await config_service.get_by_id(config_id, current_user.tenant_id, include_inherited)


@router.put("/{config_id}", response_model=Configuration)
async def update_configuration(
    config_id: str,
    dto: ConfigurationUpdate,
    current_user: JWTPayload = Depends(get_current_user),
) -> Configuration:
    """Update configuration"""
    return await config_service.update(config_id, current_user.tenant_id, dto, current_user.sub)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_configuration(
    config_id: str, current_user: JWTPayload = Depends(get_current_user)
) -> None:
    """Delete configuration"""
    await config_service.delete(config_id, current_user.tenant_id)


@router.post("/backup", response_model=BackupResponse)
async def backup_configurations(
    request: BackupRequest, current_user: JWTPayload = Depends(get_current_user)
) -> BackupResponse:
    """Create backup of all configurations"""
    return await config_service.backup(
        current_user.tenant_id, current_user.sub, request.description
    )


@router.post("/restore/{backup_id}", response_model=RestoreResponse)
async def restore_configurations(
    backup_id: str, current_user: JWTPayload = Depends(get_current_user)
) -> RestoreResponse:
    """Restore configurations from backup"""
    await config_service.restore(backup_id, current_user.tenant_id, current_user.sub)
    return RestoreResponse(message="Backup restored successfully")
