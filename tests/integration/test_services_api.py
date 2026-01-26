"""Integration tests for services API endpoints."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture
def mock_current_user():
    """Mock the current user with admin role."""

    class MockCurrentUser:
        def __init__(self):
            self.user_id = "user-001"
            self.name = "Test User"
            self.roles = {
                "service-setting-service": ["全体管理者"],
            }

        def has_role(self, service_id, role_name):
            return role_name in self.roles.get(service_id, [])

        def is_global_admin(self):
            return self.has_role("service-setting-service", "全体管理者")

        def is_viewer(self):
            return self.is_global_admin() or self.has_role(
                "service-setting-service", "閲覧者"
            )

    return MockCurrentUser()


@pytest.fixture
def mock_viewer_user():
    """Mock a user with viewer role only."""

    class MockViewerUser:
        def __init__(self):
            self.user_id = "viewer-001"
            self.name = "Viewer User"
            self.roles = {
                "service-setting-service": ["閲覧者"],
            }

        def has_role(self, service_id, role_name):
            return role_name in self.roles.get(service_id, [])

        def is_global_admin(self):
            return False

        def is_viewer(self):
            return self.has_role("service-setting-service", "閲覧者")

    return MockViewerUser()


@pytest.fixture
def sample_service_data():
    """Sample service data."""
    return {
        "id": "file-management",
        "name": "ファイル管理サービス",
        "description": "File management service",
        "roleEndpoint": "http://mock-services/api/file-management/roles",
        "isCore": False,
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@pytest.fixture
def sample_tenant_service_data():
    """Sample tenant service data."""
    return {
        "serviceId": "file-management",
        "serviceName": "ファイル管理サービス",
        "assignedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "assignedBy": "user-001",
    }


@pytest.fixture
def test_client_with_auth(mock_current_user):
    """Create a test client with authentication mocked."""
    from app.main import app

    # Override dependencies
    app.dependency_overrides = {}

    def override_verify_token():
        return mock_current_user

    from app.core.auth import verify_token

    app.dependency_overrides[verify_token] = override_verify_token

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides = {}


def test_get_services_success(test_client_with_auth, sample_service_data):
    """Test GET /api/services endpoint returns services list."""
    from app.models.service import Service

    with patch(
        "app.services.service_service.ServiceService.get_all_services"
    ) as mock_get_all:
        mock_get_all.return_value = [Service(**sample_service_data)]

        response = test_client_with_auth.get(
            "/api/services", headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "file-management"


def test_get_services_unauthorized(test_client):
    """Test GET /api/services without authentication."""
    response = test_client.get("/api/services")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_tenant_services_success(test_client_with_auth, sample_tenant_service_data):
    """Test GET /api/tenants/{tenantId}/services endpoint."""
    with patch(
        "app.services.service_service.ServiceService.get_tenant_services"
    ) as mock_get_tenant:
        mock_get_tenant.return_value = [sample_tenant_service_data]

        response = test_client_with_auth.get(
            "/api/tenants/tenant-001/services",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["serviceId"] == "file-management"


def test_get_tenant_services_empty(test_client_with_auth):
    """Test GET /api/tenants/{tenantId}/services with no assignments."""
    with patch(
        "app.services.service_service.ServiceService.get_tenant_services"
    ) as mock_get_tenant:
        mock_get_tenant.return_value = []

        response = test_client_with_auth.get(
            "/api/tenants/tenant-001/services",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 0


def test_update_tenant_services_success(test_client_with_auth):
    """Test PUT /api/tenants/{tenantId}/services endpoint."""
    with patch(
        "app.services.service_service.ServiceService.update_tenant_services"
    ) as mock_update:
        mock_update.return_value = ["file-management", "messaging"]

        response = test_client_with_auth.put(
            "/api/tenants/tenant-001/services",
            headers={"Authorization": "Bearer test-token"},
            json={"serviceIds": ["file-management", "messaging"]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tenantId"] == "tenant-001"
        assert len(data["assignedServices"]) == 2
        assert "file-management" in data["assignedServices"]
        assert "messaging" in data["assignedServices"]


def test_update_tenant_services_invalid_service(test_client_with_auth):
    """Test PUT /api/tenants/{tenantId}/services with invalid service ID."""
    with patch(
        "app.services.service_service.ServiceService.update_tenant_services"
    ) as mock_update:
        mock_update.side_effect = ValueError("Service not found: non-existent")

        response = test_client_with_auth.put(
            "/api/tenants/tenant-001/services",
            headers={"Authorization": "Bearer test-token"},
            json={"serviceIds": ["non-existent"]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Service not found" in response.json()["detail"]


def test_update_tenant_services_viewer_forbidden(mock_viewer_user):
    """Test PUT /api/tenants/{tenantId}/services with viewer role (should fail)."""
    from app.main import app

    # Override with viewer user
    def override_verify_token():
        return mock_viewer_user

    from app.core.auth import verify_token

    app.dependency_overrides[verify_token] = override_verify_token

    client = TestClient(app)

    response = client.put(
        "/api/tenants/tenant-001/services",
        headers={"Authorization": "Bearer test-token"},
        json={"serviceIds": ["file-management"]},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Clean up
    app.dependency_overrides = {}


def test_update_tenant_services_empty_list(test_client_with_auth):
    """Test PUT /api/tenants/{tenantId}/services with empty service list."""
    with patch(
        "app.services.service_service.ServiceService.update_tenant_services"
    ) as mock_update:
        mock_update.return_value = []

        response = test_client_with_auth.put(
            "/api/tenants/tenant-001/services",
            headers={"Authorization": "Bearer test-token"},
            json={"serviceIds": []},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["assignedServices"]) == 0
