import os
import pytest

# Set environment variables for testing before importing app
os.environ.setdefault(
    "COSMOS_ENDPOINT", "https://localhost:8081"
)
os.environ.setdefault(
    "COSMOS_KEY", "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)
os.environ.setdefault("COSMOS_DATABASE", "settingsdb")
os.environ.setdefault("COSMOS_CONTAINER", "configurations")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ISSUER", "auth-service")
os.environ.setdefault("LOG_LEVEL", "ERROR")


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests"""
    return "asyncio"
