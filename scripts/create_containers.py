#!/usr/bin/env python3
"""Script to create Cosmos DB containers for Service Setting Service."""

import logging
import os
import sys
import time

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import (
    CosmosResourceExistsError,
    CosmosHttpResponseError,
    CosmosResourceNotFoundError,
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_containers_with_retry(max_retries: int = 30, retry_delay: int = 20) -> None:
    """Create Cosmos DB containers with retry logic for startup delays.
    
    Note: Initial startup of Cosmos DB Emulator can take 5-10 minutes.
    We use 30 retries with 20 second delays to allow up to 10 minutes.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Connecting to Cosmos DB at {settings.cosmosdb_endpoint}")
            client = CosmosClient(
                url=settings.cosmosdb_endpoint, credential=settings.cosmosdb_key
            )

            # Create or get database
            try:
                database = client.create_database(id=settings.cosmosdb_database)
                logger.info(f"Created database: {settings.cosmosdb_database}")
            except CosmosResourceExistsError:
                database = client.get_database_client(settings.cosmosdb_database)
                logger.info(f"Database already exists: {settings.cosmosdb_database}")
            except CosmosResourceNotFoundError:
                # If database doesn't exist, create it
                database = client.create_database(id=settings.cosmosdb_database)
                logger.info(f"Created database: {settings.cosmosdb_database}")

            # Create services container with partition key /id
            try:
                database.create_container(
                    id=settings.cosmosdb_services_container,
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400,
                )
                logger.info(
                    f"Created container: {settings.cosmosdb_services_container} "
                    "with partition key /id"
                )
            except CosmosResourceExistsError:
                logger.info(
                    f"Container {settings.cosmosdb_services_container} already exists"
                )

            # Create service-assignments container with partition key /tenantId
            try:
                database.create_container(
                    id=settings.cosmosdb_service_assignments_container,
                    partition_key=PartitionKey(path="/tenantId"),
                    offer_throughput=400,
                )
                logger.info(
                    f"Created container: {settings.cosmosdb_service_assignments_container} "
                    "with partition key /tenantId"
                )
            except CosmosResourceExistsError:
                logger.info(
                    f"Container {settings.cosmosdb_service_assignments_container} "
                    f"already exists"
                )

            logger.info("Container creation completed successfully")
            return

        except CosmosHttpResponseError as e:
            if "still starting" in str(e) or e.status_code == 503:
                if attempt < max_retries - 1:
                    logger.warning(f"Cosmos DB is still starting. Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed after {max_retries} attempts. Cosmos DB may not be fully started.")
                    raise
            else:
                logger.error(f"Error creating containers: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error creating containers: {e}")
            raise


if __name__ == "__main__":
    create_containers_with_retry()
