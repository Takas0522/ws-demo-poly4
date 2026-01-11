from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from app.core.config import settings
from app.core.logger import logger


class CosmosDBClient:
    def __init__(self) -> None:
        self.client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        self.database: DatabaseProxy | None = None
        self.container: ContainerProxy | None = None

    async def initialize(self) -> None:
        """Initialize CosmosDB database and container"""
        try:
            self.database = self.client.create_database_if_not_exists(id=settings.COSMOS_DATABASE)
            self.container = self.database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER, partition_key={"paths": ["/tenant_id"]}
            )
            logger.info("CosmosDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB: {e}")
            raise

    def get_container(self) -> ContainerProxy:
        """Get CosmosDB container"""
        if not self.container:
            raise RuntimeError("CosmosDB container not initialized")
        return self.container


cosmos_client = CosmosDBClient()
