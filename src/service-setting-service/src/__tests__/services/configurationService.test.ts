import { ConfigurationService } from '../../services/configurationService';
import { ConfigurationRepository } from '../../repositories/configurationRepository';
import { CacheService } from '../../services/cacheService';
import { Configuration, CreateConfigurationDto } from '../../types';
import { AppError } from '../../middleware/errorHandler';

jest.mock('../../repositories/configurationRepository');
jest.mock('../../services/cacheService');

describe('ConfigurationService', () => {
  let service: ConfigurationService;
  let mockRepository: jest.Mocked<ConfigurationRepository>;
  let mockCache: jest.Mocked<CacheService>;

  beforeEach(() => {
    mockRepository = new ConfigurationRepository() as jest.Mocked<ConfigurationRepository>;
    mockCache = new CacheService() as jest.Mocked<CacheService>;
    service = new ConfigurationService(mockRepository, mockCache);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('create', () => {
    it('should create a new configuration', async () => {
      const dto: CreateConfigurationDto = {
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
        description: 'Test config',
      };

      const mockConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
        description: 'Test config',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      mockRepository.findByKey = jest.fn().mockResolvedValue(null);
      mockRepository.create = jest.fn().mockResolvedValue(mockConfig);
      mockCache.set = jest.fn().mockResolvedValue(undefined);

      const result = await service.create(dto, 'user-1');

      expect(result).toEqual(mockConfig);
      expect(mockRepository.findByKey).toHaveBeenCalledWith('test.key', 'tenant-1');
      expect(mockRepository.create).toHaveBeenCalled();
      expect(mockCache.set).toHaveBeenCalled();
    });

    it('should throw error if key already exists', async () => {
      const dto: CreateConfigurationDto = {
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
      };

      const existingConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'old-value',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      mockRepository.findByKey = jest.fn().mockResolvedValue(existingConfig);

      await expect(service.create(dto, 'user-1')).rejects.toThrow(AppError);
      await expect(service.create(dto, 'user-1')).rejects.toThrow(
        "Configuration with key 'test.key' already exists"
      );
    });
  });

  describe('getById', () => {
    it('should return cached configuration if available', async () => {
      const mockConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      mockCache.get = jest.fn().mockResolvedValue(mockConfig);

      const result = await service.getById('config-1', 'tenant-1');

      expect(result).toEqual(mockConfig);
      expect(mockCache.get).toHaveBeenCalled();
      expect(mockRepository.findById).not.toHaveBeenCalled();
    });

    it('should fetch from repository if not in cache', async () => {
      const mockConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      mockCache.get = jest.fn().mockResolvedValue(null);
      mockRepository.findById = jest.fn().mockResolvedValue(mockConfig);
      mockCache.set = jest.fn().mockResolvedValue(undefined);

      const result = await service.getById('config-1', 'tenant-1');

      expect(result).toEqual(mockConfig);
      expect(mockRepository.findById).toHaveBeenCalledWith('config-1', 'tenant-1');
      expect(mockCache.set).toHaveBeenCalled();
    });

    it('should throw error if configuration not found', async () => {
      mockCache.get = jest.fn().mockResolvedValue(null);
      mockRepository.findById = jest.fn().mockResolvedValue(null);

      await expect(service.getById('config-1', 'tenant-1')).rejects.toThrow(AppError);
      await expect(service.getById('config-1', 'tenant-1')).rejects.toThrow(
        'Configuration not found'
      );
    });
  });

  describe('update', () => {
    it('should update configuration and invalidate cache', async () => {
      const existingConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'old-value',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      const updatedConfig: Configuration = {
        ...existingConfig,
        value: 'new-value',
        version: 2,
      };

      mockRepository.findById = jest.fn().mockResolvedValue(existingConfig);
      mockRepository.update = jest.fn().mockResolvedValue(updatedConfig);
      mockCache.delete = jest.fn().mockResolvedValue(undefined);

      const result = await service.update(
        'config-1',
        'tenant-1',
        { value: 'new-value' },
        'user-1'
      );

      expect(result).toEqual(updatedConfig);
      expect(mockRepository.update).toHaveBeenCalled();
      expect(mockCache.delete).toHaveBeenCalled();
    });
  });

  describe('delete', () => {
    it('should delete configuration and invalidate cache', async () => {
      const existingConfig: Configuration = {
        id: 'config-1',
        tenantId: 'tenant-1',
        key: 'test.key',
        value: 'test-value',
        isEncrypted: false,
        version: 1,
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'user-1',
        updatedBy: 'user-1',
      };

      mockRepository.findById = jest.fn().mockResolvedValue(existingConfig);
      mockRepository.delete = jest.fn().mockResolvedValue(undefined);
      mockCache.delete = jest.fn().mockResolvedValue(undefined);

      await service.delete('config-1', 'tenant-1');

      expect(mockRepository.delete).toHaveBeenCalledWith('config-1', 'tenant-1');
      expect(mockCache.delete).toHaveBeenCalled();
    });
  });
});
