"""ServiceRepository テスト"""
import pytest
from unittest.mock import Mock
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.repositories.service_repository import ServiceRepository
from app.models.service import Service


@pytest.fixture
def service_repository(mock_cosmos_container):
    """ServiceRepositoryフィクスチャ"""
    return ServiceRepository(mock_cosmos_container)


class Test正常系:
    """正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_get_service_by_id(self, service_repository, test_service_file):
        """RT_SR001: get_service: サービスが取得できる"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.container.create_item(service.model_dump())
        
        # Act
        result = await service_repository.get("file-service")
        
        # Assert
        assert result is not None
        assert result.id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_return_none_when_service_not_found(self, service_repository):
        """RT_SR002: get_service: 存在しないサービスでNone"""
        # Arrange
        # Act
        result = await service_repository.get("nonexistent-service")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_should_create_service(self, service_repository, test_service_file):
        """RT_SR003: create_service: サービスが作成できる"""
        # Arrange
        service = Service(**test_service_file)
        
        # Act
        result = await service_repository.create(service)
        
        # Assert
        assert result.id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_list_active_services_only(self, service_repository, test_service_file, test_service_inactive):
        """RT_SR005: list_all: is_active=Trueでアクティブのみ取得"""
        # Arrange
        active_service = Service(**test_service_file)
        inactive_service = Service(**test_service_inactive)
        await service_repository.create(active_service)
        await service_repository.create(inactive_service)
        
        # Act
        result = await service_repository.list_services(is_active=True)
        
        # Assert
        assert len(result) >= 1
        assert all(s.is_active for s in result)
    
    @pytest.mark.asyncio
    async def test_should_list_all_services_when_is_active_is_none(self, service_repository, test_service_file, test_service_inactive):
        """RT_SR006: list_all: is_active=Noneで全サービス取得"""
        # Arrange
        active_service = Service(**test_service_file)
        inactive_service = Service(**test_service_inactive)
        await service_repository.create(active_service)
        await service_repository.create(inactive_service)
        
        # Act
        result = await service_repository.list_services(is_active=None)
        
        # Assert
        assert len(result) >= 2
    
    @pytest.mark.asyncio
    async def test_should_find_service_by_name(self, service_repository, test_service_file):
        """RT_SR007: find_by_name: サービス名で検索できる"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.create(service)
        
        # Act
        result = await service_repository.find_by_name("ファイル管理サービス")
        
        # Assert
        assert result is not None
        assert result.name == "ファイル管理サービス"
    
    @pytest.mark.asyncio
    async def test_should_count_active_services(self, service_repository, test_service_file):
        """RT_SR008: count_active_services: アクティブ数を取得"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.create(service)
        
        # Act
        result = await service_repository.count_active_services()
        
        # Assert
        assert result >= 1
    
    @pytest.mark.asyncio
    async def test_should_update_service(self, service_repository, test_service_file):
        """RT_SR009: update_service: サービスを更新できる"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.create(service)
        service.name = "Updated Service"
        
        # Act
        result = await service_repository.update(service)
        
        # Assert
        assert result.name == "Updated Service"
    
    @pytest.mark.asyncio
    async def test_should_delete_service(self, service_repository, test_service_file):
        """RT_SR010: delete_service: サービスを削除できる"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.create(service)
        
        # Act
        await service_repository.delete("file-service", "_system")
        
        # Assert
        result = await service_repository.get("file-service")
        assert result is None


class Test異常系:
    """異常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_raise_409_when_creating_duplicate_service(self, service_repository, test_service_file):
        """RT_SR004: create_service: 重複IDで409エラー"""
        # Arrange
        service = Service(**test_service_file)
        await service_repository.create(service)
        
        # Act & Assert
        from azure.cosmos.exceptions import CosmosResourceExistsError
        with pytest.raises(CosmosResourceExistsError):
            await service_repository.create(service)
