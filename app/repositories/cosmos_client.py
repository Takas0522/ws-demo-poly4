import os
from typing import Optional
from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from app.core.config import settings
from app.core.logger import logger

# SSL証明書検証を無効化（開発環境のCosmosDBエミュレータ用）
os.environ['NODE_TLS_REJECT_UNAUTHORIZED'] = '0'


class CosmosDBClient:
    def __init__(self) -> None:
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self.container: Optional[ContainerProxy] = None
        self._initialized = False
        self._connection_attempted = False

    async def initialize(self) -> None:
        """Initialize CosmosDB database and container"""
        if self._initialized:
            return

        if not self._connection_attempted:
            self._connection_attempted = True
            try:
                logger.info(
                    f"Connecting to CosmosDB: {settings.COSMOS_ENDPOINT}")
                logger.info(f"Database: {settings.COSMOS_DATABASE}")

                # CosmosDBエミュレータの場合はSSL証明書の検証を無効化
                self.client = CosmosClient(
                    settings.COSMOS_ENDPOINT,
                    settings.COSMOS_KEY,
                    connection_verify=False  # SSL検証を無効化
                )
                logger.info("✓ Connection established")
            except Exception as e:
                logger.error(f"✗ Connection failed: {e}")
                logger.warning(
                    "Service will continue without CosmosDB connection")
                return

        if not self.client:
            return

        try:
            self.database = self.client.create_database_if_not_exists(
                id=settings.COSMOS_DATABASE)
            self.container = self.database.create_container_if_not_exists(
                id=settings.COSMOS_CONTAINER, partition_key={
                    "paths": ["/tenant_id"]}
            )
            logger.info("CosmosDB initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB: {e}")
            logger.warning("Service will continue without CosmosDB connection")

    def get_container(self) -> ContainerProxy:
        """Get CosmosDB container"""
        if not self.container:
            raise RuntimeError("CosmosDB container not initialized")
        return self.container


cosmos_client = CosmosDBClient()
