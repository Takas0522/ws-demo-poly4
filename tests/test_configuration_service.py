import pytest
from app.models.configuration import Configuration, ConfigurationCreate
from app.services.configuration_service import ConfigurationService
from app.repositories.configuration_repository import ConfigurationRepository
from app.repositories.cache_service import CacheService
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException


@pytest.fixture
def mock_repository():
    return AsyncMock(spec=ConfigurationRepository)


@pytest.fixture
def mock_cache():
    cache = AsyncMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.delete_pattern = AsyncMock()
    return cache


@pytest.fixture
def service(mock_repository, mock_cache):
    return ConfigurationService(mock_repository, mock_cache)


@pytest.mark.asyncio
async def test_create_configuration(service, mock_repository, mock_cache):
    """Test creating a new configuration"""
    dto = ConfigurationCreate(
        tenant_id="tenant-1",
        key="test.key",
        value="test-value",
        description="Test config",
    )

    mock_config = Configuration(
        id="config-1",
        tenant_id="tenant-1",
        key="test.key",
        value="test-value",
        description="Test config",
        is_encrypted=False,
        version=1,
        created_by="user-1",
        updated_by="user-1",
    )

    mock_repository.find_by_key = AsyncMock(return_value=None)
    mock_repository.create = AsyncMock(return_value=mock_config)

    result = await service.create(dto, "user-1")

    assert result.id == "config-1"
    assert result.key == "test.key"
    mock_repository.find_by_key.assert_called_once_with("test.key", "tenant-1")
    mock_repository.create.assert_called_once()
    mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_create_configuration_duplicate_key(service, mock_repository):
    """Test creating configuration with duplicate key"""
    dto = ConfigurationCreate(
        tenant_id="tenant-1",
        key="test.key",
        value="test-value",
    )

    existing_config = Configuration(
        id="config-1",
        tenant_id="tenant-1",
        key="test.key",
        value="old-value",
        is_encrypted=False,
        version=1,
        created_by="user-1",
        updated_by="user-1",
    )

    mock_repository.find_by_key = AsyncMock(return_value=existing_config)

    with pytest.raises(HTTPException) as exc_info:
        await service.create(dto, "user-1")

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_by_id_from_cache(service, mock_repository, mock_cache):
    """Test getting configuration from cache"""
    mock_config_dict = {
        "id": "config-1",
        "tenant_id": "tenant-1",
        "key": "test.key",
        "value": "test-value",
        "is_encrypted": False,
        "version": 1,
        "created_by": "user-1",
        "updated_by": "user-1",
    }

    mock_cache.get = AsyncMock(return_value=mock_config_dict)

    result = await service.get_by_id("config-1", "tenant-1")

    assert result.id == "config-1"
    mock_cache.get.assert_called_once()
    mock_repository.find_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_by_id_from_database(service, mock_repository, mock_cache):
    """Test getting configuration from database when not in cache"""
    mock_config = Configuration(
        id="config-1",
        tenant_id="tenant-1",
        key="test.key",
        value="test-value",
        is_encrypted=False,
        version=1,
        created_by="user-1",
        updated_by="user-1",
    )

    mock_cache.get = AsyncMock(return_value=None)
    mock_repository.find_by_id = AsyncMock(return_value=mock_config)

    result = await service.get_by_id("config-1", "tenant-1")

    assert result.id == "config-1"
    mock_repository.find_by_id.assert_called_once_with("config-1", "tenant-1")
    mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_repository, mock_cache):
    """Test getting non-existent configuration"""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repository.find_by_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await service.get_by_id("config-1", "tenant-1")

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_configuration(service, mock_repository, mock_cache):
    """Test deleting configuration"""
    mock_config = Configuration(
        id="config-1",
        tenant_id="tenant-1",
        key="test.key",
        value="test-value",
        is_encrypted=False,
        version=1,
        created_by="user-1",
        updated_by="user-1",
    )

    mock_repository.find_by_id = AsyncMock(return_value=mock_config)
    mock_repository.delete = AsyncMock()

    await service.delete("config-1", "tenant-1")

    mock_repository.delete.assert_called_once_with("config-1", "tenant-1")
    mock_cache.delete.assert_called_once()
