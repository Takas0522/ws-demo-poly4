import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import get_current_user
from app.models.auth import JWTPayload

client = TestClient(app)


# Mock user for testing
def get_mock_user():
    return JWTPayload(
        sub="user-123",
        tenant_id="tenant-123",
        email="test@example.com",
    )


app.dependency_overrides[get_current_user] = get_mock_user


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "service-setting-service"


def test_api_docs():
    """Test API documentation endpoints"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
