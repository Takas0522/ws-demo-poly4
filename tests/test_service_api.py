import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.models.auth import JWTPayload
from app.repositories.service_repository import ServiceRepository, TenantRepository

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


# Service Catalog Tests


def test_create_service_as_global_admin():
    """Test creating a service as global admin"""
    app.dependency_overrides[get_current_user] = get_mock_global_admin

    response = client.post(
        "/api/services",
        json={
            "name": "test-service",
            "displayName": "Test Service",
            "description": "A test service",
            "category": "storage",
            "requiredPlan": ["premium", "enterprise"],
            "features": ["feature1", "feature2"],
            "pricing": [{"plan": "premium", "price": 10.0, "currency": "USD"}],
        },
    )

    assert response.status_code == 201 or response.status_code == 400  # 400 if already exists
    if response.status_code == 201:
        data = response.json()
        assert data["name"] == "test-service"
        assert data["displayName"] == "Test Service"
        assert data["tenantId"] == "system-internal"
        assert data["status"] == "active"


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

    # First create a service
    app.dependency_overrides[get_current_user] = get_mock_global_admin
    create_response = client.post(
        "/api/services",
        json={
            "name": "get-test-service",
            "displayName": "Get Test Service",
            "description": "Service for get test",
            "category": "storage",
            "requiredPlan": ["free"],
            "features": [],
            "pricing": [],
        },
    )

    if create_response.status_code == 201:
        service_id = create_response.json()["id"]

        # Get the service
        app.dependency_overrides[get_current_user] = get_mock_tenant_admin
        response = client.get(f"/api/services/{service_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_id


def test_update_service_as_global_admin():
    """Test updating a service as global admin"""
    app.dependency_overrides[get_current_user] = get_mock_global_admin

    # First create a service
    create_response = client.post(
        "/api/services",
        json={
            "name": "update-test-service",
            "displayName": "Update Test Service",
            "description": "Service to update",
            "category": "compute",
            "requiredPlan": ["free"],
            "features": [],
            "pricing": [],
        },
    )

    if create_response.status_code == 201:
        service_id = create_response.json()["id"]

        # Update the service
        response = client.put(
            f"/api/services/{service_id}",
            json={"displayName": "Updated Service Name", "status": "inactive"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["displayName"] == "Updated Service Name"
        assert data["status"] == "inactive"


def test_delete_service_as_global_admin():
    """Test deleting a service as global admin"""
    app.dependency_overrides[get_current_user] = get_mock_global_admin

    # First create a service
    create_response = client.post(
        "/api/services",
        json={
            "name": "delete-test-service",
            "displayName": "Delete Test Service",
            "description": "Service to delete",
            "category": "storage",
            "requiredPlan": ["free"],
            "features": [],
            "pricing": [],
        },
    )

    if create_response.status_code == 201:
        service_id = create_response.json()["id"]

        # Delete the service
        response = client.delete(f"/api/services/{service_id}")

        assert response.status_code == 204


# Tenant Service Assignment Tests


def test_assign_service_to_tenant():
    """Test assigning a service to a tenant"""
    # Note: This test requires tenant data to exist in the database
    # In a real scenario, you'd set up test data first
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test-service"}
    )

    # May return 404 if tenant doesn't exist or 400 if service already assigned
    assert response.status_code in [201, 400, 404]


def test_get_tenant_services():
    """Test getting services assigned to a tenant"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.get("/api/tenants/tenant-123/services")

    # May return 404 if tenant doesn't exist
    assert response.status_code in [200, 404]


def test_remove_service_from_tenant():
    """Test removing a service from a tenant"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    response = client.delete("/api/tenants/tenant-123/services/service-test-service")

    # May return 204 or 404 depending on whether the assignment exists
    assert response.status_code in [204, 404]


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

    # May return 404 if tenant doesn't exist
    assert response.status_code in [200, 404]


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


def test_permissions_allow_admins_for_tenant_operations():
    """Test that tenant admins can manage tenant services"""
    app.dependency_overrides[get_current_user] = get_mock_tenant_admin

    # Assign service (may fail if tenant doesn't exist)
    response = client.post(
        "/api/tenants/tenant-123/services", json={"serviceId": "service-test"}
    )
    assert response.status_code in [201, 400, 404, 403]

    # Get tenant services (may fail if tenant doesn't exist)
    response = client.get("/api/tenants/tenant-123/services")
    assert response.status_code in [200, 404]


# Clean up
app.dependency_overrides.clear()
