#!/usr/bin/env python3
"""Script to create Cosmos DB containers for Service Setting Service."""

import logging
import os
import sys

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_containers() -> None:
    """Create Cosmos DB containers for Service Setting Service."""
    try:
        # Initialize Cosmos client
        logger.info(f"Connecting to Cosmos DB at {settings.cosmosdb_endpoint}")
        client = CosmosClient(
            url=settings.cosmosdb_endpoint, credential=settings.cosmosdb_key
        )

        # Get or create database
        database = client.get_database_client(settings.cosmosdb_database)
        logger.info(f"Using database: {settings.cosmosdb_database}")

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

    except Exception as e:
        logger.error(f"Error creating containers: {e}")
        raise


if __name__ == "__main__":
    create_containers()
