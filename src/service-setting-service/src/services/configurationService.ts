import { ConfigurationRepository } from '../repositories/configurationRepository';
import { CacheService } from './cacheService';
import {
  Configuration,
  CreateConfigurationDto,
  UpdateConfigurationDto,
  ConfigurationQuery,
} from '../types';
import logger from '../utils/logger';
import { AppError } from '../middleware/errorHandler';

export class ConfigurationService {
  private repository: ConfigurationRepository;
  private cache: CacheService;

  constructor(repository: ConfigurationRepository, cache: CacheService) {
    this.repository = repository;
    this.cache = cache;
  }

  private getCacheKey(id: string, tenantId: string): string {
    return `config:${tenantId}:${id}`;
  }

  private getTenantCachePattern(tenantId: string): string {
    return `config:${tenantId}:*`;
  }

  async create(dto: CreateConfigurationDto, userId: string): Promise<Configuration> {
    try {
      // Check if key already exists
      const existing = await this.repository.findByKey(dto.key, dto.tenantId);
      if (existing) {
        throw new AppError(409, `Configuration with key '${dto.key}' already exists`);
      }

      const config = await this.repository.create({
        ...dto,
        isEncrypted: dto.isEncrypted || false,
        createdBy: userId,
        updatedBy: userId,
      });

      // Cache the new configuration
      await this.cache.set(this.getCacheKey(config.id, config.tenantId), config);

      logger.info(`Configuration created: ${config.id} by user ${userId}`);
      return config;
    } catch (error) {
      logger.error('Error in create configuration:', error);
      throw error;
    }
  }

  async getById(id: string, tenantId: string, includeInherited = false): Promise<Configuration> {
    try {
      // Try cache first
      const cacheKey = this.getCacheKey(id, tenantId);
      const cached = await this.cache.get<Configuration>(cacheKey);
      if (cached) {
        logger.debug(`Configuration ${id} retrieved from cache`);
        return cached;
      }

      // Fetch from database
      const config = await this.repository.findById(id, tenantId);
      if (!config) {
        throw new AppError(404, 'Configuration not found');
      }

      // Apply inheritance if needed
      let finalConfig = config;
      if (includeInherited && config.parentConfigId) {
        finalConfig = await this.applyInheritance(config);
      }

      // Cache the result
      await this.cache.set(cacheKey, finalConfig);

      return finalConfig;
    } catch (error) {
      logger.error('Error in getById:', error);
      throw error;
    }
  }

  async getByKey(key: string, tenantId: string, includeInherited = false): Promise<Configuration> {
    try {
      const config = await this.repository.findByKey(key, tenantId);
      if (!config) {
        throw new AppError(404, `Configuration with key '${key}' not found`);
      }

      let finalConfig = config;
      if (includeInherited && config.parentConfigId) {
        finalConfig = await this.applyInheritance(config);
      }

      return finalConfig;
    } catch (error) {
      logger.error('Error in getByKey:', error);
      throw error;
    }
  }

  async list(query: ConfigurationQuery): Promise<Configuration[]> {
    try {
      const configs = await this.repository.findAll(query);

      if (query.includeInherited) {
        const processedConfigs = await Promise.all(
          configs.map((config) =>
            config.parentConfigId ? this.applyInheritance(config) : config
          )
        );
        return processedConfigs;
      }

      return configs;
    } catch (error) {
      logger.error('Error in list:', error);
      throw error;
    }
  }

  async update(
    id: string,
    tenantId: string,
    dto: UpdateConfigurationDto,
    userId: string
  ): Promise<Configuration> {
    try {
      const existing = await this.repository.findById(id, tenantId);
      if (!existing) {
        throw new AppError(404, 'Configuration not found');
      }

      const updated = await this.repository.update(id, tenantId, {
        ...dto,
        updatedBy: userId,
      });

      // Invalidate cache
      await this.cache.delete(this.getCacheKey(id, tenantId));

      logger.info(`Configuration updated: ${id} by user ${userId}`);
      return updated;
    } catch (error) {
      logger.error('Error in update:', error);
      throw error;
    }
  }

  async delete(id: string, tenantId: string): Promise<void> {
    try {
      const existing = await this.repository.findById(id, tenantId);
      if (!existing) {
        throw new AppError(404, 'Configuration not found');
      }

      await this.repository.delete(id, tenantId);

      // Invalidate cache
      await this.cache.delete(this.getCacheKey(id, tenantId));

      logger.info(`Configuration deleted: ${id}`);
    } catch (error) {
      logger.error('Error in delete:', error);
      throw error;
    }
  }

  async backup(tenantId: string, userId: string, description?: string): Promise<{ backupId: string }> {
    try {
      const configs = await this.repository.findAll({ tenantId });

      const backupId = `backup-${tenantId}-${Date.now()}`;
      const backup = {
        id: backupId,
        tenantId,
        backupDate: new Date(),
        configurations: configs,
        createdBy: userId,
        description,
      };

      // Store backup in cache (could also store in a separate container)
      await this.cache.set(`backup:${backupId}`, backup, 86400 * 7); // 7 days TTL

      logger.info(`Backup created for tenant ${tenantId}: ${backupId}`);
      return { backupId };
    } catch (error) {
      logger.error('Error in backup:', error);
      throw error;
    }
  }

  async restore(backupId: string, tenantId: string, userId: string): Promise<void> {
    try {
      const backup = await this.cache.get<{
        configurations: Configuration[];
        tenantId: string;
      }>(`backup:${backupId}`);

      if (!backup) {
        throw new AppError(404, 'Backup not found or expired');
      }

      if (backup.tenantId !== tenantId) {
        throw new AppError(403, 'Cannot restore backup from different tenant');
      }

      // Restore configurations
      for (const config of backup.configurations) {
        const existing = await this.repository.findById(config.id, tenantId);
        if (existing) {
          await this.repository.update(config.id, tenantId, {
            ...config,
            updatedBy: userId,
          });
        } else {
          await this.repository.create({
            ...config,
            createdBy: userId,
            updatedBy: userId,
          });
        }
      }

      // Invalidate all tenant cache
      await this.cache.deletePattern(this.getTenantCachePattern(tenantId));

      logger.info(`Backup restored for tenant ${tenantId}: ${backupId}`);
    } catch (error) {
      logger.error('Error in restore:', error);
      throw error;
    }
  }

  private async applyInheritance(config: Configuration): Promise<Configuration> {
    if (!config.parentConfigId) {
      return config;
    }

    try {
      const parent = await this.repository.findById(config.parentConfigId, config.tenantId);
      if (!parent) {
        logger.warn(`Parent configuration not found: ${config.parentConfigId}`);
        return config;
      }

      // Merge parent values with current config (current config takes precedence)
      const inherited: Configuration = {
        ...parent,
        ...config,
        id: config.id,
        key: config.key,
        value: config.value !== undefined ? config.value : parent.value,
      };

      return inherited;
    } catch (error) {
      logger.error('Error applying inheritance:', error);
      return config;
    }
  }
}
