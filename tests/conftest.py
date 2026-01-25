"""Pytest configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient


# Set up test environment variables before any imports
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ.setdefault("COSMOSDB_ENDPOINT", "https://test.documents.azure.com:443/")
    os.environ.setdefault("COSMOSDB_KEY", "test-key")
    os.environ.setdefault("COSMOSDB_DATABASE", "management-app")


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app

    return TestClient(app)
