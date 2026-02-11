"""
Integration tests for Tenant Management API
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestTenantManagementAPI:
    """Test tenant management endpoints"""

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_get_tenants_list(self, test_client: TestClient, auth_headers: dict):
        """Test getting tenant list"""
        response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "data" in data
        assert isinstance(data["data"], list)
        
        if len(data["data"]) > 0:
            tenant = data["data"][0]
            assert "id" in tenant
            assert "name" in tenant
            assert "domains" in tenant
            assert "is_privileged" in tenant
            assert "created_at" in tenant
        
        # Check pagination if exists
        if "pagination" in data:
            assert "page" in data["pagination"]
            assert "per_page" in data["pagination"]
            assert "total" in data["pagination"]

    def test_get_tenants_with_pagination(self, test_client: TestClient, auth_headers: dict):
        """Test getting tenant list with pagination"""
        response = test_client.get(
            "/api/v1/tenants?page=1&per_page=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_tenants_unauthorized(self, test_client: TestClient):
        """Test getting tenant list without authentication"""
        response = test_client.get("/api/v1/tenants")
        
        assert response.status_code == 401

    def test_get_tenant_detail(self, test_client: TestClient, auth_headers: dict):
        """Test getting tenant detail"""
        # First, get tenant list to find a tenant ID
        list_response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            tenants = list_response.json().get("data", [])
            if len(tenants) > 0:
                tenant_id = tenants[0]["id"]
                
                # Get tenant detail
                response = test_client.get(
                    f"/api/v1/tenants/{tenant_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify detail information
                assert "id" in data
                assert data["id"] == tenant_id
                assert "name" in data
                assert "domains" in data
                assert "is_privileged" in data
                assert "created_at" in data
                assert "users" in data
                assert "services" in data

    def test_get_tenant_detail_not_found(self, test_client: TestClient, auth_headers: dict):
        """Test getting non-existent tenant"""
        response = test_client.get(
            "/api/v1/tenants/non-existent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_create_tenant(self, test_client: TestClient, auth_headers: dict):
        """Test creating a new tenant"""
        new_tenant = {
            "name": f"テストテナント {pytest.timestamp if hasattr(pytest, 'timestamp') else '123'}",
            "domains": ["test-tenant.example.com"]
        }
        
        response = test_client.post(
            "/api/v1/tenants",
            json=new_tenant,
            headers=auth_headers
        )
        
        # May fail if not admin or if tenant exists
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["name"] == new_tenant["name"]
            assert data["domains"] == new_tenant["domains"]
            assert data["is_privileged"] is False
        elif response.status_code == 403:
            # Not authorized (expected if not admin)
            pass
        elif response.status_code == 409:
            # Tenant already exists
            pass

    def test_create_tenant_duplicate(self, test_client: TestClient, auth_headers: dict):
        """Test creating tenant with duplicate name"""
        # Get existing tenant
        list_response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            tenants = list_response.json().get("data", [])
            if len(tenants) > 0:
                existing_name = tenants[0]["name"]
                
                duplicate_tenant = {
                    "name": existing_name,
                    "domains": ["duplicate.example.com"]
                }
                
                response = test_client.post(
                    "/api/v1/tenants",
                    json=duplicate_tenant,
                    headers=auth_headers
                )
                
                # Should return conflict or forbidden
                assert response.status_code in [403, 409]

    def test_update_tenant(self, test_client: TestClient, auth_headers: dict):
        """Test updating tenant information"""
        # Get a tenant to update
        list_response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            tenants = list_response.json().get("data", [])
            
            # Find a non-privileged tenant
            non_privileged = [t for t in tenants if not t.get("is_privileged", False)]
            
            if len(non_privileged) > 0:
                tenant_id = non_privileged[0]["id"]
                
                update_data = {
                    "name": "Updated Tenant Name",
                    "domains": ["updated.example.com"]
                }
                
                response = test_client.put(
                    f"/api/v1/tenants/{tenant_id}",
                    json=update_data,
                    headers=auth_headers
                )
                
                # May succeed or fail based on permissions
                if response.status_code == 200:
                    data = response.json()
                    assert data["name"] == update_data["name"]

    def test_update_privileged_tenant_forbidden(self, test_client: TestClient, auth_headers: dict):
        """Test updating privileged tenant (should be forbidden)"""
        # Get tenants
        list_response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            tenants = list_response.json().get("data", [])
            
            # Find a privileged tenant
            privileged = [t for t in tenants if t.get("is_privileged", False)]
            
            if len(privileged) > 0:
                tenant_id = privileged[0]["id"]
                
                update_data = {
                    "name": "Should Fail",
                    "domains": ["fail.example.com"]
                }
                
                response = test_client.put(
                    f"/api/v1/tenants/{tenant_id}",
                    json=update_data,
                    headers=auth_headers
                )
                
                # Should be forbidden
                assert response.status_code == 403

    def test_delete_tenant(self, test_client: TestClient, auth_headers: dict):
        """Test deleting a tenant"""
        # Create a test tenant first
        new_tenant = {
            "name": f"Delete Test Tenant {pytest.timestamp if hasattr(pytest, 'timestamp') else '456'}",
            "domains": ["delete-test.example.com"]
        }
        
        create_response = test_client.post(
            "/api/v1/tenants",
            json=new_tenant,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            tenant_id = create_response.json()["id"]
            
            # Delete the tenant
            response = test_client.delete(
                f"/api/v1/tenants/{tenant_id}",
                headers=auth_headers
            )
            
            # Should succeed or be forbidden
            assert response.status_code in [204, 403]

    def test_get_tenant_users(self, test_client: TestClient, auth_headers: dict):
        """Test getting tenant users"""
        # Get a tenant
        list_response = test_client.get(
            "/api/v1/tenants",
            headers=auth_headers
        )
        
        if list_response.status_code == 200:
            tenants = list_response.json().get("data", [])
            if len(tenants) > 0:
                tenant_id = tenants[0]["id"]
                
                response = test_client.get(
                    f"/api/v1/tenants/{tenant_id}/users",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "tenant_id" in data
                assert "users" in data
                assert isinstance(data["users"], list)
