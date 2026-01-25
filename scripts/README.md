# Scripts for Service Setting Service

This directory contains utility scripts for managing the Service Setting Service database.

## Available Scripts

### create_containers.py

Creates the required Cosmos DB containers for the Service Setting Service.

**Containers created:**
- `services` - Container for service definitions (partition key: `/id`)
- `service-assignments` - Container for tenant service assignments (partition key: `/tenantId`)

**Usage:**
```bash
# Set up environment variables (or use .env file)
export COSMOSDB_ENDPOINT="https://your-account.documents.azure.com:443/"
export COSMOSDB_KEY="your-cosmos-db-key"
export COSMOSDB_DATABASE="management-app"

# Run the script
python scripts/create_containers.py
```

### seed_data.py

Seeds the database with initial mock service data.

**Mock services created:**
- `file-management` - ファイル管理
- `messaging` - メッセージング
- `api-usage` - API利用
- `backup` - バックアップ

**Usage:**
```bash
# Ensure containers are created first
python scripts/create_containers.py

# Run the seed script
python scripts/seed_data.py
```

## Prerequisites

1. Azure Cosmos DB account with the database created
2. Python 3.11+ with required dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Environment variables configured (see `.env.example`)

## Notes

- These scripts are idempotent - they can be run multiple times safely
- Existing containers and data will not be overwritten
- The scripts will skip items that already exist and report the counts
