#!/usr/bin/env python3
"""Script to seed initial data for Service Setting Service."""

import logging
import os
import sys
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceExistsError

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Seed data: 4 mock services as specified in the issue
MOCK_SERVICES = [
    {
        "id": "file-management",
        "name": "ファイル管理",
        "description": "ファイルのアップロード、ダウンロード、管理機能を提供",
        "roleEndpoint": "/api/roles",
        "isCore": False,
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "messaging",
        "name": "メッセージング",
        "description": "メッセージの送受信機能を提供",
        "roleEndpoint": "/api/roles",
        "isCore": False,
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "api-usage",
        "name": "API利用",
        "description": "API利用状況の管理機能を提供",
        "roleEndpoint": "/api/roles",
        "isCore": False,
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "backup",
        "name": "バックアップ",
        "description": "データバックアップと復元機能を提供",
        "roleEndpoint": "/api/roles",
        "isCore": False,
        "isActive": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    },
]


def seed_services() -> None:
    """Seed mock services into the services container."""
    try:
        # Initialize Cosmos client
        logger.info(f"Connecting to Cosmos DB at {settings.cosmosdb_endpoint}")
        client = CosmosClient(
            url=settings.cosmosdb_endpoint, credential=settings.cosmosdb_key
        )

        # Get database and container
        database = client.get_database_client(settings.cosmosdb_database)
        services_container = database.get_container_client(
            settings.cosmosdb_services_container
        )

        # Insert mock services
        inserted_count = 0
        skipped_count = 0

        for service in MOCK_SERVICES:
            try:
                services_container.create_item(body=service)
                logger.info(f"✓ Inserted service: {service['id']} - {service['name']}")
                inserted_count += 1
            except CosmosResourceExistsError:
                logger.info(f"- Service already exists: {service['id']}")
                skipped_count += 1

        logger.info("\nSeed data completed:")
        logger.info(f"  Inserted: {inserted_count} services")
        logger.info(f"  Skipped: {skipped_count} services (already exist)")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise


if __name__ == "__main__":
    seed_services()
