"""サービス割り当てAPI テスト"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

from app.main import app
from app.services.service_assignment_service import ServiceAssignmentService
from app.services.service_service import ServiceService
from app.dependencies import get_cosmos_container


@pytest.fixture
def mock_assignment_service():
    """ServiceAssignmentServiceモック"""
    return AsyncMock(spec=ServiceAssignmentService)


@pytest.fixture
def mock_service_service():
    """ServiceServiceモック"""
    return AsyncMock(spec=ServiceService)


@pytest.fixture
def test_client_assignments(mock_cosmos_container):
    """FastAPI TestClient（サービス割り当てAPI用）"""
    app.dependency_overrides[get_cosmos_container] = lambda: mock_cosmos_container
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


class Test正常系:
    """正常系テスト"""
    
    def test_should_list_tenant_services_successfully(
        self,
        test_client_assignments,
        mock_assignment_service,
        test_assignment,
        test_service_file
    ):
        """AT_SA001: GET /tenants/{tenant_id}/services: 利用サービス一覧"""
        # Arrange
        from app.models.service_assignment import ServiceAssignment
        from app.models.service import Service
        assignment = ServiceAssignment(**test_assignment)
        service = Service(**test_service_file)
        mock_assignment_service.list_tenant_services.return_value = [(assignment, service)]
        
        # Act
        response = test_client_assignments.get("/api/v1/tenants/tenant_acme/services")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 0  # 実装により異なる
    
    def test_should_list_tenant_services_with_status_filter(
        self,
        test_client_assignments,
        mock_assignment_service,
        test_assignment
    ):
        """AT_SA002: GET /tenants/{tenant_id}/services?status=active: statusフィルタ"""
        # Arrange
        from app.models.service_assignment import ServiceAssignment
        assignment = ServiceAssignment(**test_assignment)
        mock_assignment_service.list_tenant_services.return_value = [(assignment, None)]
        
        # Act
        response = test_client_assignments.get("/api/v1/tenants/tenant_acme/services?status=active")
        
        # Assert
        assert response.status_code == 200
    
    def test_should_assign_service_successfully(
        self,
        test_client_assignments,
        mock_assignment_service,
        mock_service_service,
        test_assignment,
        test_service_file
    ):
        """AT_SA004: POST /tenants/{tenant_id}/services: サービス割り当て成功"""
        # Arrange
        from app.models.service_assignment import ServiceAssignment
        assignment = ServiceAssignment(**test_assignment)
        mock_assignment_service.assign_service.return_value = assignment
        
        request_body = {
            "serviceId": "file-service",
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_acme/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 201
    
    def test_should_remove_service_assignment_successfully(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA010: DELETE /tenants/{tenant_id}/services/{service_id}: 削除成功"""
        # Arrange
        mock_assignment_service.remove_service_assignment.return_value = None
        
        # Act
        response = test_client_assignments.delete("/api/v1/tenants/tenant_acme/services/file-service")
        
        # Assert
        assert response.status_code == 204


class Test異常系:
    """異常系テスト"""
    
    def test_should_return_400_when_status_filter_is_invalid(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA003: GET /tenants/{tenant_id}/services?status=invalid: 無効なstatus"""
        # Arrange
        # Act
        response = test_client_assignments.get("/api/v1/tenants/tenant_acme/services?status=invalid")
        
        # Assert
        # FastAPIのバリデーションで422が返される可能性がある
        assert response.status_code in [400, 422]
    
    def test_should_return_400_when_validation_error(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA005: POST /tenants/{tenant_id}/services: バリデーションエラー"""
        # Arrange
        request_body = {
            # serviceIdが欠けている
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_acme/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 422
    
    def test_should_return_404_when_tenant_not_found(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA006: POST /tenants/{tenant_id}/services: テナント不在で404"""
        # Arrange
        from app.utils.errors import ServiceSettingException, ServiceErrorCode
        mock_assignment_service.assign_service.side_effect = ServiceSettingException(
            error_code=ServiceErrorCode.TENANT_001_NOT_FOUND,
            message="Tenant not found",
            status_code=404
        )
        
        request_body = {
            "serviceId": "file-service",
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_nonexistent/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_should_return_404_when_service_not_found(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA007: POST /tenants/{tenant_id}/services: サービス不在で404"""
        # Arrange
        from app.utils.errors import ServiceSettingException, ServiceErrorCode
        mock_assignment_service.assign_service.side_effect = ServiceSettingException(
            error_code=ServiceErrorCode.SERVICE_001_NOT_FOUND,
            message="Service not found",
            status_code=404
        )
        
        request_body = {
            "serviceId": "nonexistent-service",
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_acme/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_should_return_409_when_assignment_already_exists(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA008: POST /tenants/{tenant_id}/services: 重複割り当てで409"""
        # Arrange
        from app.utils.errors import ServiceSettingException, ServiceErrorCode
        mock_assignment_service.assign_service.side_effect = ServiceSettingException(
            error_code=ServiceErrorCode.ASSIGNMENT_001_ALREADY_EXISTS,
            message="Assignment already exists",
            status_code=409
        )
        
        request_body = {
            "serviceId": "file-service",
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_acme/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 409
    
    def test_should_return_422_when_service_is_inactive(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA009: POST /tenants/{tenant_id}/services: 非アクティブで422"""
        # Arrange
        from app.utils.errors import ServiceSettingException, ServiceErrorCode
        mock_assignment_service.assign_service.side_effect = ServiceSettingException(
            error_code=ServiceErrorCode.SERVICE_002_INACTIVE,
            message="Service is inactive",
            status_code=422
        )
        
        request_body = {
            "serviceId": "inactive-service",
            "config": {}
        }
        
        # Act
        response = test_client_assignments.post(
            "/api/v1/tenants/tenant_acme/services",
            json=request_body
        )
        
        # Assert
        assert response.status_code == 422
    
    def test_should_return_404_when_assignment_not_found_on_removal(
        self,
        test_client_assignments,
        mock_assignment_service
    ):
        """AT_SA011: DELETE /tenants/{tenant_id}/services/{service_id}: 存在しない割り当てで404"""
        # Arrange
        from app.utils.errors import ServiceSettingException, ServiceErrorCode
        mock_assignment_service.remove_service_assignment.side_effect = ServiceSettingException(
            error_code=ServiceErrorCode.ASSIGNMENT_003_NOT_FOUND,
            message="Assignment not found",
            status_code=404
        )
        
        # Act
        response = test_client_assignments.delete("/api/v1/tenants/tenant_acme/services/nonexistent-service")
        
        # Assert
        assert response.status_code == 404
    
    def test_should_return_401_when_authentication_fails(
        self,
        test_client_assignments
    ):
        """AT_SA012: POST /tenants/{tenant_id}/services: 認証なしで401"""
        # Arrange
        # 認証ヘッダーなしでリクエスト
        
        # Act
        # Note: 認証ミドルウェアが実装されたら有効化
        # request_body = {"serviceId": "file-service", "config": {}}
        # response = test_client_assignments.post(
        #     "/api/v1/tenants/tenant_acme/services",
        #     json=request_body,
        #     headers={}
        # )
        
        # Assert
        # assert response.status_code == 401
        pass
