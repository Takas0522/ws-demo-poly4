import { CacheService } from '../../services/cacheService';

describe('CacheService', () => {
  let cacheService: CacheService;

  beforeEach(() => {
    cacheService = new CacheService();
  });

  afterEach(async () => {
    await cacheService.disconnect();
  });

  describe('get', () => {
    it('should return null when cache is not connected', async () => {
      const result = await cacheService.get('test-key');
      expect(result).toBeNull();
    });
  });

  describe('set', () => {
    it('should not throw when cache is not connected', async () => {
      await expect(
        cacheService.set('test-key', { value: 'test' })
      ).resolves.not.toThrow();
    });
  });

  describe('delete', () => {
    it('should not throw when cache is not connected', async () => {
      await expect(cacheService.delete('test-key')).resolves.not.toThrow();
    });
  });

  describe('deletePattern', () => {
    it('should not throw when cache is not connected', async () => {
      await expect(
        cacheService.deletePattern('test-*')
      ).resolves.not.toThrow();
    });
  });
});
