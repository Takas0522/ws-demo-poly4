"""ServiceService テスト"""
import pytest
from unittest.mock import AsyncMock, Mock

from app.services.service_service import ServiceService
from app.repositories.service_repository import ServiceRepository
from app.models.service import Service


@pytest.fixture
def mock_service_repository():
    """ServiceRepositoryモック"""
    return AsyncMock(spec=ServiceRepository)


@pytest.fixture
def service_service(mock_service_repository):
    """ServiceServiceフィクスチャ"""
    return ServiceService(mock_service_repository)


class Test正常系:
    """正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_get_service_detail(self, service_service, mock_service_repository, test_service_file):
        """ST_SS001: get_service: サービス詳細取得"""
        # Arrange
        service = Service(**test_service_file)
        mock_service_repository.get_service.return_value = service
        
        # Act
        result = await service_service.get_service("file-service")
        
        # Assert
        assert result is not None
        assert result.id == "file-service"
        assert result.name == "ファイル管理サービス"
        mock_service_repository.get_service.assert_called_once_with("file-service")
    
    @pytest.mark.asyncio
    async def test_should_return_none_when_service_not_found(self, service_service, mock_service_repository):
        """ST_SS002: get_service: 存在しないサービスでNone"""
        # Arrange
        mock_service_repository.get.return_value = None
        
        # Act
        result = await service_service.get_service("nonexistent-service")
        
        # Assert
        assert result is None
        mock_service_repository.get.assert_called_once_with("nonexistent-service")
    
    @pytest.mark.asyncio
    async def test_should_list_active_services(self, service_service, mock_service_repository, test_service_file):
        """ST_SS003: list_services: is_active=Trueでアクティブのみ"""
        # Arrange
        service = Service(**test_service_file)
        mock_service_repository.list_services.return_value = [service]
        
        # Act
        result = await service_service.list_services(is_active=True)
        
        # Assert
        assert len(result) == 1
        assert result[0].is_active is True
        mock_service_repository.list_services.assert_called_once_with(is_active=True)
    
    @pytest.mark.asyncio
    async def test_should_list_inactive_services(self, service_service, mock_service_repository, test_service_inactive):
        """ST_SS004: list_services: is_active=Falseで非アクティブのみ"""
        # Arrange
        service = Service(**test_service_inactive)
        mock_service_repository.list_services.return_value = [service]
        
        # Act
        result = await service_service.list_services(is_active=False)
        
        # Assert
        assert len(result) == 1
        assert result[0].is_active is False
        mock_service_repository.list_services.assert_called_once_with(is_active=False)
    
    @pytest.mark.asyncio
    async def test_should_create_service(self, service_service, mock_service_repository, test_service_file):
        """ST_SS005: create_service: サービス作成成功"""
        # Arrange
        service = Service(**test_service_file)
        mock_service_repository.get.return_value = None
        mock_service_repository.create.return_value = service
        
        # Act
        result = await service_service.create_service(service)
        
        # Assert
        assert result.id == "file-service"
        mock_service_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_count_active_services(self, service_service, mock_service_repository):
        """ST_SS007: count_active_services: アクティブ数取得"""
        # Arrange
        mock_service_repository.count_active_services.return_value = 5
        
        # Act
        result = await service_service.count_active_services()
        
        # Assert
        assert result == 5
        mock_service_repository.count_active_services.assert_called_once()


class Test異常系:
    """異常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_raise_value_error_when_creating_duplicate_service(self, service_service, mock_service_repository, test_service_file):
        """ST_SS006: create_service: 重複IDでValueError"""
        # Arrange
        service = Service(**test_service_file)
        mock_service_repository.get.return_value = service  # 既に存在する
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await service_service.create_service(service)
        assert "already exists" in str(exc_info.value)
