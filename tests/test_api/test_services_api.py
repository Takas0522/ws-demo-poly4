"""サービスカタログAPI テスト"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

from app.main import app
from app.services.service_service import ServiceService
from app.dependencies import get_cosmos_container


@pytest.fixture
def mock_service_service():
    """ServiceServiceモック"""
    return AsyncMock(spec=ServiceService)


@pytest.fixture
def test_client_services(mock_cosmos_container):
    """FastAPI TestClient（サービスカタログAPI用）"""
    app.dependency_overrides[get_cosmos_container] = lambda: mock_cosmos_container
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


class Test正常系:
    """正常系テスト"""
    
    def test_should_list_services_successfully(self, test_client_services, mock_service_service, test_service_file):
        """AT_SC001: GET /services: サービス一覧取得成功"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        mock_service_service.list_services.return_value = [service]
        
        # Act
        response = test_client_services.get("/api/v1/services")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "file-service"
    
    def test_should_list_inactive_services_when_is_active_false(self, test_client_services, mock_service_service, test_service_inactive):
        """AT_SC002: GET /services: is_active=falseで非アクティブのみ"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_inactive)
        mock_service_service.list_services.return_value = [service]
        
        # Act
        response = test_client_services.get("/api/v1/services?is_active=false")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["isActive"] is False
    
    def test_should_get_service_detail_successfully(self, test_client_services, mock_service_service, test_service_file):
        """AT_SC003: GET /services/{service_id}: サービス詳細取得"""
        # Arrange
        from app.models.service import Service
        service = Service(**test_service_file)
        mock_service_service.get_service.return_value = service
        
        # Act
        response = test_client_services.get("/api/v1/services/file-service")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "file-service"
        assert data["name"] == "ファイル管理サービス"


class Test異常系:
    """異常系テスト"""
    
    def test_should_return_404_when_service_not_found(self, test_client_services, mock_service_service):
        """AT_SC004: GET /services/{service_id}: 存在しないサービスで404"""
        # Arrange
        mock_service_service.get_service.return_value = None
        
        # Act
        response = test_client_services.get("/api/v1/services/nonexistent-service")
        
        # Assert
        assert response.status_code == 404
    
    def test_should_return_401_when_authentication_fails(self, test_client_services):
        """AT_SC005: GET /services: 認証なしで401エラー"""
        # Arrange
        # 認証ヘッダーなしでリクエスト
        
        # Act
        # Note: 認証ミドルウェアが実装されたら有効化
        # response = test_client_services.get("/api/v1/services", headers={})
        
        # Assert
        # assert response.status_code == 401
        pass
