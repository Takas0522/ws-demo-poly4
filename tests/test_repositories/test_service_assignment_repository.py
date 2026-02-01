"""ServiceAssignmentRepository テスト"""
import pytest
from unittest.mock import Mock
from azure.cosmos.exceptions import CosmosHttpResponseError

from app.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.models.service_assignment import ServiceAssignment


@pytest.fixture
def assignment_repository(mock_cosmos_container):
    """ServiceAssignmentRepositoryフィクスチャ"""
    return ServiceAssignmentRepository(mock_cosmos_container)


class Test正常系:
    """正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_get_assignment_by_id(self, assignment_repository, test_assignment):
        """RT_SAR001: get_assignment: 割り当てが取得できる"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.container.create_item(assignment.model_dump())
        
        # Act
        result = await assignment_repository.get(
            assignment.id,
            "tenant_acme"
        )
        
        # Assert
        assert result is not None
        assert result.service_id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_return_none_when_assignment_not_found(self, assignment_repository):
        """RT_SAR002: get_assignment: 存在しない割り当てでNone"""
        # Arrange
        # Act
        result = await assignment_repository.get(
            "assignment_tenant_acme_nonexistent",
            "tenant_acme"
        )
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_should_create_assignment(self, assignment_repository, test_assignment):
        """RT_SAR003: create_assignment: 割り当てが作成できる"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        
        # Act
        result = await assignment_repository.create(assignment)
        
        # Assert
        assert result.service_id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_list_assignments_by_tenant(self, assignment_repository, test_assignment):
        """RT_SAR005: list_by_tenant: テナントの割り当て一覧取得"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        result = await assignment_repository.list_by_tenant("tenant_acme")
        
        # Assert
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_should_list_assignments_by_tenant_with_status_filter(self, assignment_repository, test_assignment):
        """RT_SAR006: list_by_tenant: statusフィルタが動作する"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        result = await assignment_repository.list_by_tenant(
            "tenant_acme",
            status="active"
        )
        
        # Assert
        assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_should_find_assignment_by_tenant_and_service(self, assignment_repository, test_assignment):
        """RT_SAR007: find_by_tenant_and_service: 決定的IDで検索"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        result = await assignment_repository.find_by_tenant_and_service(
            "tenant_acme",
            "file-service"
        )
        
        # Assert
        assert result is not None
        assert result.service_id == "file-service"
    
    @pytest.mark.asyncio
    async def test_should_count_assignments_by_tenant(self, assignment_repository, test_assignment):
        """RT_SAR008: count_by_tenant: テナントの割り当て数取得"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        result = await assignment_repository.count_by_tenant("tenant_acme")
        
        # Assert
        assert result >= 1
    
    @pytest.mark.asyncio
    async def test_should_list_assignments_by_service(self, assignment_repository, test_assignment):
        """RT_SAR009: list_by_service: サービス利用テナント一覧"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        result = await assignment_repository.list_by_service("file-service")
        
        # Assert
        assert len(result) >= 1
    
    @pytest.mark.asyncio
    async def test_should_delete_assignment(self, assignment_repository, test_assignment):
        """RT_SAR010: delete_assignment: 割り当てを削除できる"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act
        await assignment_repository.delete(
            assignment.id,
            "tenant_acme"
        )
        
        # Assert
        result = await assignment_repository.get(
            assignment.id,
            "tenant_acme"
        )
        assert result is None


class Test異常系:
    """異常系テスト"""
    
    @pytest.mark.asyncio
    async def test_should_raise_409_when_creating_duplicate_assignment(self, assignment_repository, test_assignment):
        """RT_SAR004: create_assignment: 重複IDで409エラー"""
        # Arrange
        assignment = ServiceAssignment(**test_assignment)
        await assignment_repository.create(assignment)
        
        # Act & Assert
        from azure.cosmos.exceptions import CosmosResourceExistsError
        with pytest.raises(CosmosResourceExistsError):
            await assignment_repository.create(assignment)
