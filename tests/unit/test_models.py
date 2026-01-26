"""Unit tests for data models."""

from datetime import datetime, timezone

import pytest

from app.models import Service, ServiceRole, TenantServiceAssignment


class TestServiceModel:
    """Tests for Service model."""

    def test_service_model_creation(self):
        """Test creating a Service model instance."""
        now = datetime.now(timezone.utc)
        service = Service(
            id="test-service",
            name="Test Service",
            description="Test description",
            roleEndpoint="/api/roles",
            isCore=False,
            isActive=True,
            createdAt=now,
            updatedAt=now,
        )

        assert service.id == "test-service"
        assert service.name == "Test Service"
        assert service.description == "Test description"
        assert service.roleEndpoint == "/api/roles"
        assert service.isCore is False
        assert service.isActive is True
        assert service.createdAt == now
        assert service.updatedAt == now

    def test_service_model_without_description(self):
        """Test creating a Service model without optional description."""
        now = datetime.now(timezone.utc)
        service = Service(
            id="test-service",
            name="Test Service",
            roleEndpoint="/api/roles",
            isCore=True,
            isActive=True,
            createdAt=now,
            updatedAt=now,
        )

        assert service.description is None

    def test_service_model_validation(self):
        """Test Service model validation for required fields."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Service()


class TestTenantServiceAssignmentModel:
    """Tests for TenantServiceAssignment model."""

    def test_tenant_service_assignment_creation(self):
        """Test creating a TenantServiceAssignment model instance."""
        now = datetime.now(timezone.utc)
        assignment = TenantServiceAssignment(
            id="tsa-001",
            tenantId="tenant-001",
            serviceId="service-001",
            assignedAt=now,
            assignedBy="user-001",
        )

        assert assignment.id == "tsa-001"
        assert assignment.tenantId == "tenant-001"
        assert assignment.serviceId == "service-001"
        assert assignment.assignedAt == now
        assert assignment.assignedBy == "user-001"

    def test_tenant_service_assignment_validation(self):
        """Test TenantServiceAssignment model validation for required fields."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TenantServiceAssignment()


class TestServiceRoleModel:
    """Tests for ServiceRole model."""

    def test_service_role_creation(self):
        """Test creating a ServiceRole model instance."""
        now = datetime.now(timezone.utc)
        role = ServiceRole(
            id="sr-001",
            serviceId="service-001",
            roleName="Admin",
            description="Administrator role",
            lastSyncedAt=now,
        )

        assert role.id == "sr-001"
        assert role.serviceId == "service-001"
        assert role.roleName == "Admin"
        assert role.description == "Administrator role"
        assert role.lastSyncedAt == now

    def test_service_role_without_optional_fields(self):
        """Test creating a ServiceRole model without optional fields."""
        role = ServiceRole(
            id="sr-001",
            serviceId="service-001",
            roleName="Admin",
        )

        assert role.description is None
        assert role.lastSyncedAt is None

    def test_service_role_validation(self):
        """Test ServiceRole model validation for required fields."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ServiceRole()
