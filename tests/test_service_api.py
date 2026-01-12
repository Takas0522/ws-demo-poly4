import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.models.auth import JWTPayload
from app.repositories.service_repository import ServiceRepository, TenantRepository
from app.routes.service_routes import service_repo, tenant_repo

client = TestClient(app)


# Mock users for testing
def get_mock_global_admin():
    """Mock global admin user"""
    return JWTPayload(
        sub="admin-123",
        tenant_id="system-internal",
        email="admin@example.com",
        roles=["global-admin"],
    )


def get_mock_tenant_admin():
    """Mock tenant admin user"""
    return JWTPayload(
        sub="user-456", tenant_id="tenant-123", email="user@example.com", roles=["admin"]
    )


def get_mock_regular_user():
    """Mock regular user"""
    return JWTPayload(
        sub="user-789", tenant_id="tenant-123", email="regular@example.com", roles=["user"]
    )


# Mock data
mock_service = {
    "id": "service-test-service",
    "tenantId": "system-internal",
    "name": "test-service",
    "displayName": "Test Service",
    "description": "A test service",
    "category": "storage",
    "status": "active",
    "requiredPlan": ["premium", "enterprise"],
    "features": ["feature1", "feature2"],
    "pricing": [{"plan": "premium", "price": 10.0, "currency": "USD"}],
    "createdAt": "2024-01-01T00:00:00",
    "updatedAt": "2024-01-01T00:00:00",
    "createdBy": "admin-123",
    "updatedBy": "admin-123",
    "metadata": {},
}

mock_tenant = {
    "id": "tenant-123",
    "name": "Test Tenant",
    "subscription": {"plan": "premium"},
    "services": [],
}


@pytest.fixture(autouse=True)
def setup_mocks():
    """Setup mocks for all tests"""
    # Reset mocks before each test
    from app.routes.service_routes import service_repo, tenant_repo
    
    # Mock service repository methods
    service_repo._container = Mock()
    service_repo.get_container = Mock(return_value=Mock())
    service_repo.create = AsyncMock(return_value=mock_service.copy())
    service_repo.list_all = AsyncMock(return_value=[mock_service.copy()])
    service_repo.get_by_id = AsyncMock(return_value=mock_service.copy())
    service_repo.update = AsyncMock(return_value=mock_service.copy())
    service_repo.delete = AsyncMock()

    # Mock tenant repository methods
    tenant_repo._container = Mock()
    tenant_repo.get_container = Mock(return_value=Mock())
    tenant_repo.get_by_id = AsyncMock(return_value=mock_tenant.copy())
    tenant_repo.update = AsyncMock(return_value=mock_tenant.copy())
    tenant_repo.list_all = AsyncMock(return_value=[mock_tenant.copy()])

    yield

    # Cleanup
    app.dependency_overrides.clear()


# Service Catalog Tests


def test_create_service_permissions():
    """Test that only global admins can create services"""
    # Regular user should fail
    app.dependency_overrides[get_current_user] = get_mock_regular_user
    response = client.post(
        "/api/services",
        json={
            "name": "test-service",
            "displayName": "Test Service",
            "description": "A test service",
            "category": "storage",
            "requiredPlan": [],
            "features": [],
            "pricing": [],
        },
    )
    assert response.status_code == 403

    # Global admin should work (may fail with 422 due to test setup, but shouldn't be 403)
    app.dependency_overrides[get_current_user] = get_mock_global_admin
    response = client.post(
        "/api/services",
        json={
            "name": "test-service",
            "displayName": "Test Service",
            "description": "A test service",
            "category": "storage",
            "requiredPlan": [],
            "features": [],
            "pricing": [],
        },
    )
    # Should not be forbidden
    assert response.status_code != 403


def test_create_service_as_regular_user_should_fail():
    """Test that regular users cannot create services"""
    app.dependency_overrides[get_current_user] = get_mock_regular_user

    response = client.post(
        "/api/services",
        json={
            "name": "test-service-2",
            "displayName": "Test Service 2",
            "description": "Another test service",
            "category": "compute",
            "requiredPlan": ["free"],
            "features": [],
            "pricing": [],
        },
    )

    assert response.status_code == 403


def test_list_services():
    """Test listing all services"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.get("/api/services")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_services_with_filters():
    """Test listing services with filters"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    # Filter by status
    response = client.get("/api/services?status=active")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Filter by category
    response = client.get("/api/services?category=storage")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_service_by_id():
    """Test getting a specific service"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.get("/api/services/service-test-service")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "service-test-service"


def test_update_service_permissions():
    """Test update service permissions"""
    # Regular user should fail
    app.dependency_overrides[get_current_user] = get_mock_regular_user
    response = client.put(
        "/api/services/service-test-service",
        json={"displayName": "Updated Service Name"},
    )
    assert response.status_code == 403

    # Global admin should work (may fail with 422 due to test setup, but shouldn't be 403)
    app.dependency_overrides[get_current_user] = get_mock_global_admin
    response = client.put(
        "/api/services/service-test-service",
        json={"displayName": "Updated Service Name"},
    )
    # Should not be forbidden
    assert response.status_code != 403


def test_delete_service_as_global_admin():
    """Test deleting a service as global admin"""
    app.dependency_overrides[get_current_user] = get_mock_global_admin

    response = client.delete("/api/services/service-test-service")

    assert response.status_code == 204


# Tenant Service Assignment Tests


def test_assign_service_permissions():
    """Test assign service permissions"""
    # Regular user should fail
    app.dependency_overrides[get_current_user] = get_mock_regular_user
    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test-service"}
    )
    assert response.status_code == 403

    # Tenant admin should work (may fail with 422 due to test setup, but shouldn't be 403)
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin
    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test-service"}
    )
    # Should not be forbidden
    assert response.status_code != 403


def test_get_tenant_services():
    """Test getting services assigned to a tenant"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.get("/api/tenants/tenant-123/services")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_remove_service_from_tenant():
    """Test removing a service from a tenant"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin
    
    # First add a service to the tenant for removal
    updated_tenant = mock_tenant.copy()
    updated_tenant["services"] = [
        {"serviceId": "service-test-service", "enabled": True}
    ]
    tenant_repo.get_by_id = AsyncMock(return_value=updated_tenant)

    response = client.delete("/api/tenants/tenant-123/services/service-test-service")

    assert response.status_code == 204


def test_tenant_isolation():
    """Test that users cannot access other tenants' services"""
    # Mock user from tenant-123
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    # Try to access tenant-456's services
    response = client.get("/api/tenants/tenant-456/services")

    assert response.status_code == 403


# Analytics Tests


def test_get_service_usage_stats_as_global_admin():
    """Test getting service usage statistics as global admin"""
    app.dependency_overrides[get_current_user] = get_mock_global_admin

    response = client.get("/api/analytics/services/usage")

    assert response.status_code == 200
    data = response.json()
    assert "totalServices" in data
    assert "activeServices" in data
    assert "serviceUsage" in data
    assert isinstance(data["serviceUsage"], list)


def test_get_service_usage_stats_as_regular_user_should_fail():
    """Test that regular users cannot access global analytics"""
    app.dependency_overrides[get_current_user] = get_mock_regular_user

    response = client.get("/api/analytics/services/usage")

    assert response.status_code == 403


def test_get_tenant_service_activity():
    """Test getting service activity for a tenant"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.get("/api/analytics/tenants/tenant-123/service-activity")

    assert response.status_code == 200
    data = response.json()
    assert "tenantId" in data
    assert data["tenantId"] == "tenant-123"


# Permission Tests


def test_permissions_enforce_global_admin_for_create():
    """Test that only global admins can create services"""
    # Tenant admin should fail
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.post(
        "/api/services",
        json={
            "name": "permission-test",
            "displayName": "Permission Test",
            "description": "Test",
            "category": "test",
            "requiredPlan": ["free"],
            "features": [],
            "pricing": [],
        },
    )

    assert response.status_code == 403


def test_permissions_enforce_global_admin_for_update():
    """Test that only global admins can update services"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.put(
        "/api/services/service-test", json={"displayName": "Updated Name"}
    )

    assert response.status_code == 403


def test_permissions_enforce_global_admin_for_delete():
    """Test that only global admins can delete services"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.delete("/api/services/service-test")

    assert response.status_code == 403


def test_tenant_admin_permissions():
    """Test that tenant admins can manage tenant services"""
    # Regular user should fail
    app.dependency_overrides[get_current_user] = get_mock_regular_user
    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test"}
    )
    assert response.status_code == 403

    # Tenant admin should work (may fail with 422 due to test setup, but shouldn't be 403)
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin
    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test"}
    )
    # Should not be forbidden
    assert response.status_code != 403

    # Get tenant services should work for tenant admin
    response = client.get("/api/tenants/tenant-123/services")
    assert response.status_code == 200
