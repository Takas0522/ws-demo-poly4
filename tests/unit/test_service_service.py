"""Unit tests for ServiceService."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.models.service import Service
from app.services.service_service import ServiceService


@pytest.fixture
def mock_db_client():
    """Create a mock database client."""
    mock_client = MagicMock()
    mock_client.services_container = MagicMock()
    mock_client.service_assignments_container = MagicMock()
    return mock_client


@pytest.fixture
def service_service(mock_db_client):
    """Create a ServiceService instance with mock db client."""
    return ServiceService(mock_db_client)


@pytest.fixture
def sample_service():
    """Create a sample service."""
    return Service(
        id="file-management",
        name="ファイル管理サービス",
        description="File management service",
        roleEndpoint="http://mock-services/api/file-management/roles",
        isCore=False,
        isActive=True,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_assignment():
    """Create a sample tenant service assignment."""
    return {
        "id": str(uuid4()),
        "tenantId": "tenant-001",
        "serviceId": "file-management",
        "assignedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "assignedBy": "user-001",
    }


@pytest.mark.asyncio
async def test_get_all_services(service_service, mock_db_client, sample_service):
    """Test getting all services."""
    # Arrange
    mock_db_client.services_container.query_items.return_value = [
        sample_service.model_dump()
    ]

    # Act
    services = await service_service.get_all_services()

    # Assert
    assert len(services) == 1
    assert services[0].id == sample_service.id
    assert services[0].name == sample_service.name
    mock_db_client.services_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_service_by_id_found(service_service, mock_db_client, sample_service):
    """Test getting a service by ID when it exists."""
    # Arrange
    mock_db_client.services_container.read_item.return_value = (
        sample_service.model_dump()
    )

    # Act
    service = await service_service.get_service_by_id("file-management")

    # Assert
    assert service is not None
    assert service.id == sample_service.id
    assert service.name == sample_service.name
    mock_db_client.services_container.read_item.assert_called_once_with(
        item="file-management", partition_key="file-management"
    )


@pytest.mark.asyncio
async def test_get_service_by_id_not_found(service_service, mock_db_client):
    """Test getting a service by ID when it doesn't exist."""
    # Arrange
    mock_db_client.services_container.read_item.side_effect = (
        CosmosResourceNotFoundError()
    )

    # Act
    service = await service_service.get_service_by_id("non-existent")

    # Assert
    assert service is None


@pytest.mark.asyncio
async def test_get_tenant_services(
    service_service, mock_db_client, sample_service, sample_assignment
):
    """Test getting services assigned to a tenant."""
    # Arrange
    mock_db_client.service_assignments_container.query_items.return_value = [
        sample_assignment
    ]
    mock_db_client.services_container.read_item.return_value = (
        sample_service.model_dump()
    )

    # Act
    tenant_services = await service_service.get_tenant_services("tenant-001")

    # Assert
    assert len(tenant_services) == 1
    assert tenant_services[0]["serviceId"] == "file-management"
    assert tenant_services[0]["serviceName"] == sample_service.name
    assert tenant_services[0]["assignedBy"] == "user-001"


@pytest.mark.asyncio
async def test_get_tenant_services_no_assignments(service_service, mock_db_client):
    """Test getting services for a tenant with no assignments."""
    # Arrange
    mock_db_client.service_assignments_container.query_items.return_value = []

    # Act
    tenant_services = await service_service.get_tenant_services("tenant-001")

    # Assert
    assert len(tenant_services) == 0


@pytest.mark.asyncio
async def test_update_tenant_services_add_new(
    service_service, mock_db_client, sample_service
):
    """Test adding new service assignments to a tenant."""
    # Arrange
    mock_db_client.services_container.read_item.return_value = (
        sample_service.model_dump()
    )
    mock_db_client.service_assignments_container.query_items.return_value = []
    mock_db_client.service_assignments_container.create_item = MagicMock()

    # Act
    result = await service_service.update_tenant_services(
        tenant_id="tenant-001",
        service_ids=["file-management"],
        user_id="user-001",
    )

    # Assert
    assert result == ["file-management"]
    mock_db_client.service_assignments_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_tenant_services_remove_existing(
    service_service, mock_db_client, sample_assignment
):
    """Test removing existing service assignments from a tenant."""
    # Arrange
    mock_db_client.service_assignments_container.query_items.return_value = [
        sample_assignment
    ]
    mock_db_client.service_assignments_container.delete_item = MagicMock()

    # Act
    result = await service_service.update_tenant_services(
        tenant_id="tenant-001",
        service_ids=[],
        user_id="user-001",
    )

    # Assert
    assert result == []
    mock_db_client.service_assignments_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_tenant_services_invalid_service_id(
    service_service, mock_db_client
):
    """Test updating tenant services with invalid service ID."""
    # Arrange
    mock_db_client.services_container.read_item.side_effect = (
        CosmosResourceNotFoundError()
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Service not found"):
        await service_service.update_tenant_services(
            tenant_id="tenant-001",
            service_ids=["non-existent"],
            user_id="user-001",
        )


@pytest.mark.asyncio
async def test_update_tenant_services_replace(
    service_service, mock_db_client, sample_service, sample_assignment
):
    """Test replacing existing service assignments."""
    # Arrange
    new_service = Service(
        id="messaging",
        name="メッセージングサービス",
        description="Messaging service",
        roleEndpoint="http://mock-services/api/messaging/roles",
        isCore=False,
        isActive=True,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )

    def read_item_side_effect(item, partition_key):
        if item == "file-management":
            return sample_service.model_dump()
        elif item == "messaging":
            return new_service.model_dump()
        raise CosmosResourceNotFoundError()

    mock_db_client.services_container.read_item.side_effect = read_item_side_effect
    mock_db_client.service_assignments_container.query_items.return_value = [
        sample_assignment
    ]
    mock_db_client.service_assignments_container.delete_item = MagicMock()
    mock_db_client.service_assignments_container.create_item = MagicMock()

    # Act
    result = await service_service.update_tenant_services(
        tenant_id="tenant-001",
        service_ids=["messaging"],
        user_id="user-001",
    )

    # Assert
    assert result == ["messaging"]
    mock_db_client.service_assignments_container.delete_item.assert_called_once()
    mock_db_client.service_assignments_container.create_item.assert_called_once()
