"""Test health check endpoint."""
import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_health_check_endpoint(test_client):
    """Test that health check endpoint returns expected structure."""
    response = test_client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "dependencies" in data
    
    # Check service information
    assert data["service"] == "Service Setting Service"
    assert data["version"] == "0.1.0"
    
    # Check dependencies structure
    assert "cosmosdb" in data["dependencies"]


@pytest.mark.asyncio
async def test_root_endpoint(test_client):
    """Test that root endpoint returns service information."""
    response = test_client.get("/")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"
