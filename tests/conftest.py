"""Pytest configuration and fixtures."""

import os

# Set up test environment variables BEFORE any other imports
os.environ.setdefault("COSMOSDB_ENDPOINT", "https://test.documents.azure.com:443/")
os.environ.setdefault("COSMOSDB_KEY", "test-key")
os.environ.setdefault("COSMOSDB_DATABASE", "management-app")
os.environ.setdefault("AUTH_SERVICE_URL", "http://localhost:8003")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Already set at import time, but ensure they remain
    pass


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app

    return TestClient(app)
