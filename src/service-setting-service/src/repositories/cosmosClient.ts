import { CosmosClient, Container, Database } from '@azure/cosmos';
import { config } from '../config';
import logger from '../utils/logger';

export class CosmosDBClient {
  private client: CosmosClient;
  private database: Database | null = null;
  private container: Container | null = null;

  constructor() {
    this.client = new CosmosClient({
      endpoint: config.cosmos.endpoint,
      key: config.cosmos.key,
    });
  }

  async initialize(): Promise<void> {
    try {
      const { database } = await this.client.databases.createIfNotExists({
        id: config.cosmos.database,
      });
      this.database = database;

      const { container } = await database.containers.createIfNotExists({
        id: config.cosmos.container,
        partitionKey: { paths: ['/tenantId'] },
      });
      this.container = container;

      logger.info('CosmosDB initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize CosmosDB:', error);
      throw error;
    }
  }

  getContainer(): Container {
    if (!this.container) {
      throw new Error('CosmosDB container not initialized');
    }
    return this.container;
  }

  getDatabase(): Database {
    if (!this.database) {
      throw new Error('CosmosDB database not initialized');
    }
    return this.database;
  }
}

export const cosmosDBClient = new CosmosDBClient();
