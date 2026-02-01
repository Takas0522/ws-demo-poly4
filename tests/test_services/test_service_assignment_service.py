"""ServiceAssignmentService テスト"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from app.services.service_assignment_service import ServiceAssignmentService
from app.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.repositories.service_repository import ServiceRepository
from app.services.tenant_client import TenantClient
from app.models.service_assignment import ServiceAssignment
from app.models.service import Service
from app.utils.errors import ServiceSettingException, ServiceErrorCode


@pytest.fixture
def mock_assignment_repository():
    """ServiceAssignmentRepositoryモック"""
    return AsyncMock(spec=ServiceAssignmentRepository)


@pytest.fixture
def mock_service_repository():
    """ServiceRepositoryモック"""
    return AsyncMock(spec=ServiceRepository)


@pytest.fixture
def assignment_service(mock_assignment_repository, mock_service_repository, mock_tenant_client):
    """ServiceAssignmentServiceフィクスチャ"""
    return ServiceAssignmentService(
        mock_assignment_repository,
        mock_service_repository,
        mock_tenant_client
    )


class Test正常系:
    """正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_assign_service_successfully(
        self, 
        assignment_service, 
        mock_assignment_repository,
        mock_service_repository,
        mock_tenant_client,
        test_service_file
    ):
        """ST_SAS001: assign_service: サービス割り当て成功"""
        # Arrange
        service = Service(**test_service_file)
        mock_tenant_client.verify_tenant_exists.return_value = True
        mock_service_repository.get_service.return_value = service
        mock_assignment_repository.find_by_tenant_and_service.return_value = None
        mock_assignment_repository.create_assignment.return_value = ServiceAssignment(
            id="assignment_tenant_acme_file-service",
            tenant_id="tenant_acme",
            service_id="file-service",
            status="active",
            config={},
            assigned_at=datetime.utcnow(),
            assigned_by="user_admin_001"
        )
        
        # Act
        result = await assignment_service.assign_service(
            tenant_id="tenant_acme",
            service_id="file-service",
            config={},
            assigned_by="user_admin_001",
            jwt_token="test_token"
        )
        
        # Assert
        assert result.service_id == "file-service"
        assert result.tenant_id == "tenant_acme"
        mock_tenant_client.verify_tenant_exists.assert_called_once()
        mock_service_repository.get_service.assert_called_once_with("file-service")
        mock_assignment_repository.create_assignment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_remove_service_assignment_successfully(
        self,
        assignment_service,
        mock_assignment_repository,
        test_assignment
    ):
        """ST_SAS008: remove_service_assignment: 割り当て解除成功"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        mock_assignment_repository.get_assignment.return_value = assignment
        mock_assignment_repository.delete_assignment.return_value = None
        
        # Act
        await assignment_service.remove_service_assignment(
            tenant_id="tenant_acme",
            service_id="file-service",
            deleted_by="user_admin_001"
        )
        
        # Assert
        mock_assignment_repository.get_assignment.assert_called_once()
        mock_assignment_repository.delete_assignment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_should_list_tenant_services(
        self,
        assignment_service,
        mock_assignment_repository,
        mock_service_repository,
        test_assignment,
        test_service_file
    ):
        """ST_SAS010: list_tenant_services: テナント利用サービス一覧取得"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        service = Service(**test_service_file)
        mock_assignment_repository.list_by_tenant.return_value = [assignment]
        mock_service_repository.get_service.return_value = service
        
        # Act
        result = await assignment_service.list_tenant_services(
            tenant_id="tenant_acme",
            status=None
        )
        
        # Assert
        assert len(result) == 1
        assert result[0][0].service_id == "file-service"
        assert result[0][1].id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_continue_when_service_fetch_fails(
        self,
        assignment_service,
        mock_assignment_repository,
        mock_service_repository,
        test_assignment
    ):
        """ST_SAS011: list_tenant_services: Service取得失敗時も継続"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        mock_assignment_repository.list_by_tenant.return_value = [assignment]
        mock_service_repository.get_service.side_effect = Exception("Database error")
        
        # Act
        result = await assignment_service.list_tenant_services(
            tenant_id="tenant_acme",
            status=None
        )
        
        # Assert
        assert len(result) == 1
        assert result[0][0].service_id == "file-service"
        assert result[0][1] is None  # Service取得失敗でNone
    
    @pytest.mark.asyncio
    async def test_should_continue_when_service_fetch_timeout(
        self,
        assignment_service,
        mock_assignment_repository,
        mock_service_repository,
        test_assignment
    ):
        """ST_SAS012: list_tenant_services: Service取得タイムアウトでも継続"""
        # Arrange
        import asyncio
        assignment = ServiceAssignment(**test_assignment)
        mock_assignment_repository.list_by_tenant.return_value = [assignment]
        mock_service_repository.get_service.side_effect = asyncio.TimeoutError()
        
        # Act
        result = await assignment_service.list_tenant_services(
            tenant_id="tenant_acme",
            status=None
        )
        
        # Assert
        assert len(result) == 1
        assert result[0][0].service_id == "file-service"
        assert result[0][1] is None  # タイムアウトでNone


class Test異常系:
    """異常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_tenant_not_found(
        self,
        assignment_service,
        mock_tenant_client
    ):
        """ST_SAS002: assign_service: テナント不在でエラー"""
        # Arrange
        mock_tenant_client.verify_tenant_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id="tenant_nonexistent",
                service_id="file-service",
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_service_not_found(
        self,
        assignment_service,
        mock_service_repository,
        mock_tenant_client
    ):
        """ST_SAS003: assign_service: サービス不在でエラー"""
        # Arrange
        mock_tenant_client.verify_tenant_exists.return_value = True
        mock_service_repository.get_service.return_value = None
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id="tenant_acme",
                service_id="nonexistent-service",
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_service_is_inactive(
        self,
        assignment_service,
        mock_service_repository,
        mock_tenant_client,
        test_service_inactive
    ):
        """ST_SAS004: assign_service: 非アクティブサービスでエラー"""
        # Arrange
        service = Service(**test_service_inactive)
        mock_tenant_client.verify_tenant_exists.return_value = True
        mock_service_repository.get_service.return_value = service
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id="tenant_acme",
                service_id="inactive-service",
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 422
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_assignment_already_exists(
        self,
        assignment_service,
        mock_assignment_repository,
        mock_service_repository,
        mock_tenant_client,
        test_assignment,
        test_service_file
    ):
        """ST_SAS005: assign_service: 重複割り当てでエラー"""
        # Arrange
        service = Service(**test_service_file)
        assignment = ServiceAssignment(**test_assignment)
        mock_tenant_client.verify_tenant_exists.return_value = True
        mock_service_repository.get_service.return_value = service
        mock_assignment_repository.find_by_tenant_and_service.return_value = assignment
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id="tenant_acme",
                service_id="file-service",
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 409
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_id_length_exceeds_limit(
        self,
        assignment_service
    ):
        """ST_SAS006: assign_service: ID長制限超過でエラー"""
        # Arrange
        long_tenant_id = "tenant_" + "a" * 200
        long_service_id = "service_" + "a" * 200
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id=long_tenant_id,
                service_id=long_service_id,
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_tenant_service_timeout(
        self,
        assignment_service,
        mock_tenant_client
    ):
        """ST_SAS007: assign_service: テナントサービスタイムアウト"""
        # Arrange
        import asyncio
        mock_tenant_client.verify_tenant_exists.side_effect = asyncio.TimeoutError()
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.assign_service(
                tenant_id="tenant_acme",
                service_id="file-service",
                config={},
                assigned_by="user_admin_001",
                jwt_token="test_token"
            )
        assert exc_info.value.status_code == 504
    
    @pytest.mark.asyncio
    async def test_should_raise_error_when_assignment_not_found_on_removal(
        self,
        assignment_service,
        mock_assignment_repository
    ):
        """ST_SAS009: remove_service_assignment: 存在しない割り当てでエラー"""
        # Arrange
        mock_assignment_repository.get_assignment.return_value = None
        
        # Act & Assert
        with pytest.raises(ServiceSettingException) as exc_info:
            await assignment_service.remove_service_assignment(
                tenant_id="tenant_acme",
                service_id="file-service",
                deleted_by="user_admin_001"
            )
        assert exc_info.value.status_code == 404
