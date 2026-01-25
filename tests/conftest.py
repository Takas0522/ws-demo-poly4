"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app
    
    return TestClient(app)
