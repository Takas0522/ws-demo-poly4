import os
import asyncio
from typing import Optional
from azure.cosmos import CosmosClient, ContainerProxy, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError
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
        """Initialize CosmosDB database and container with retry logic"""
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

        # Retry logic for container creation
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Create database if not exists
                self.database = self.client.create_database_if_not_exists(
                    id=settings.COSMOS_DATABASE)

                # Wait a bit before creating container (for emulator stability)
                await asyncio.sleep(0.5)

                # Create container if not exists
                self.container = self.database.create_container_if_not_exists(
                    id=settings.COSMOS_CONTAINER,
                    partition_key={"paths": ["/tenant_id"]}
                )

                logger.info("CosmosDB initialized successfully")
                self._initialized = True
                return

            except CosmosHttpResponseError as e:
                if e.status_code == 409:  # Conflict - Resource already exists
                    # Container already exists, try to get it
                    try:
                        self.container = self.database.get_container_client(
                            settings.COSMOS_CONTAINER)
                        logger.info("CosmosDB container already exists, using existing container")
                        self._initialized = True
                        return
                    except Exception as get_error:
                        logger.error(f"Failed to get existing container: {get_error}")
                        logger.warning(
                            "Service will continue without CosmosDB connection")
                        return
                elif e.status_code == 503:  # Service Unavailable
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"CosmosDB service unavailable (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {retry_delay}s..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(
                            f"Failed to initialize CosmosDB after {max_retries} attempts: {e}")
                        logger.warning(
                            "Service will continue without CosmosDB connection")
                else:
                    logger.error(f"Failed to initialize CosmosDB: {e}")
                    logger.warning(
                        "Service will continue without CosmosDB connection")
                    return
            except Exception as e:
                logger.error(f"Failed to initialize CosmosDB: {e}")
                logger.warning(
                    "Service will continue without CosmosDB connection")
                return

    def get_container(self) -> ContainerProxy:
        """Get CosmosDB container"""
        if not self.container:
            raise RuntimeError("CosmosDB container not initialized")
        return self.container


cosmos_client = CosmosDBClient()
