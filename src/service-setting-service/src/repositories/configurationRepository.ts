import { Container } from '@azure/cosmos';
import { v4 as uuidv4 } from 'uuid';
import { Configuration, ConfigurationQuery } from '../types';
import { cosmosDBClient } from './cosmosClient';
import logger from '../utils/logger';

export class ConfigurationRepository {
  private container: Container;

  constructor() {
    this.container = cosmosDBClient.getContainer();
  }

  async create(config: Omit<Configuration, 'id' | 'version' | 'createdAt' | 'updatedAt'>): Promise<Configuration> {
    try {
      const newConfig: Configuration = {
        ...config,
        id: uuidv4(),
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      const { resource } = await this.container.items.create(newConfig);
      logger.info(`Configuration created: ${resource?.id}`);
      return resource as Configuration;
    } catch (error) {
      logger.error('Error creating configuration:', error);
      throw error;
    }
  }

  async findById(id: string, tenantId: string): Promise<Configuration | null> {
    try {
      const { resource } = await this.container.item(id, tenantId).read<Configuration>();
      return resource || null;
    } catch (error: unknown) {
      if (typeof error === 'object' && error !== null && 'code' in error && error.code === 404) {
        return null;
      }
      logger.error('Error finding configuration:', error);
      throw error;
    }
  }

  async findByKey(key: string, tenantId: string): Promise<Configuration | null> {
    try {
      const querySpec = {
        query: 'SELECT * FROM c WHERE c.key = @key AND c.tenantId = @tenantId',
        parameters: [
          { name: '@key', value: key },
          { name: '@tenantId', value: tenantId },
        ],
      };

      const { resources } = await this.container.items.query<Configuration>(querySpec).fetchAll();
      return resources.length > 0 ? resources[0] : null;
    } catch (error) {
      logger.error('Error finding configuration by key:', error);
      throw error;
    }
  }

  async findAll(query: ConfigurationQuery): Promise<Configuration[]> {
    try {
      let queryText = 'SELECT * FROM c WHERE c.tenantId = @tenantId';
      const parameters: Array<{ name: string; value: unknown }> = [
        { name: '@tenantId', value: query.tenantId },
      ];

      if (query.key) {
        queryText += ' AND c.key = @key';
        parameters.push({ name: '@key', value: query.key });
      }

      if (query.tags && query.tags.length > 0) {
        queryText += ' AND ARRAY_CONTAINS(c.tags, @tag)';
        parameters.push({ name: '@tag', value: query.tags[0] });
      }

      const querySpec = { query: queryText, parameters };
      const { resources } = await this.container.items.query<Configuration>(querySpec).fetchAll();

      return resources;
    } catch (error) {
      logger.error('Error finding configurations:', error);
      throw error;
    }
  }

  async update(id: string, tenantId: string, updates: Partial<Configuration>): Promise<Configuration> {
    try {
      const existing = await this.findById(id, tenantId);
      if (!existing) {
        throw new Error('Configuration not found');
      }

      const updated: Configuration = {
        ...existing,
        ...updates,
        id: existing.id,
        tenantId: existing.tenantId,
        version: existing.version + 1,
        updatedAt: new Date(),
      };

      const { resource } = await this.container.item(id, tenantId).replace(updated);
      logger.info(`Configuration updated: ${id}`);
      return resource as Configuration;
    } catch (error) {
      logger.error('Error updating configuration:', error);
      throw error;
    }
  }

  async delete(id: string, tenantId: string): Promise<void> {
    try {
      await this.container.item(id, tenantId).delete();
      logger.info(`Configuration deleted: ${id}`);
    } catch (error) {
      logger.error('Error deleting configuration:', error);
      throw error;
    }
  }
}
