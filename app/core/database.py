"""Cosmos DB database connection and management."""
import logging
from typing import Optional

from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """Cosmos DB client wrapper for managing database connections."""

    def __init__(self) -> None:
        """Initialize Cosmos DB client."""
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._services_container: Optional[ContainerProxy] = None
        self._service_assignments_container: Optional[ContainerProxy] = None

    def connect(self) -> None:
        """Establish connection to Cosmos DB."""
        try:
            logger.info(
                f"Connecting to Cosmos DB at {settings.cosmosdb_endpoint}"
            )
            self._client = CosmosClient(
                url=settings.cosmosdb_endpoint,
                credential=settings.cosmosdb_key,
            )
            self._database = self._client.get_database_client(
                settings.cosmosdb_database
            )
            logger.info(
                f"Connected to database: {settings.cosmosdb_database}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection to Cosmos DB."""
        if self._client:
            logger.info("Disconnecting from Cosmos DB")
            self._client.close()
            self._client = None
            self._database = None
            self._services_container = None
            self._service_assignments_container = None

    @property
    def services_container(self) -> ContainerProxy:
        """Get the services container."""
        if not self._services_container:
            if not self._database:
                raise RuntimeError(
                    "Database connection not established. Call connect() first."
                )
            self._services_container = self._database.get_container_client(
                settings.cosmosdb_services_container
            )
        return self._services_container

    @property
    def service_assignments_container(self) -> ContainerProxy:
        """Get the service assignments container."""
        if not self._service_assignments_container:
            if not self._database:
                raise RuntimeError(
                    "Database connection not established. Call connect() first."
                )
            self._service_assignments_container = (
                self._database.get_container_client(
                    settings.cosmosdb_service_assignments_container
                )
            )
        return self._service_assignments_container

    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            if not self._database:
                return False
            # Try to read database properties as a health check
            self._database.read()
            return True
        except CosmosResourceNotFoundError:
            logger.error("Database not found during health check")
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global database client instance
db_client = CosmosDBClient()


def get_db_client() -> CosmosDBClient:
    """Get the global database client instance."""
    return db_client
