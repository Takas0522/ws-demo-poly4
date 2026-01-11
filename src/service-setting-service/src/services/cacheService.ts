import { createClient, RedisClientType } from 'redis';
import { config } from '../config';
import logger from '../utils/logger';

export class CacheService {
  private client: RedisClientType | null = null;
  private isConnected = false;

  async connect(): Promise<void> {
    try {
      this.client = createClient({
        socket: {
          host: config.redis.host,
          port: config.redis.port,
        },
        password: config.redis.password || undefined,
      });

      this.client.on('error', (err) => {
        logger.error('Redis Client Error:', err);
        this.isConnected = false;
      });

      this.client.on('connect', () => {
        logger.info('Redis Client Connected');
        this.isConnected = true;
      });

      await this.client.connect();
    } catch (error) {
      logger.error('Failed to connect to Redis:', error);
      this.isConnected = false;
    }
  }

  async get<T>(key: string): Promise<T | null> {
    if (!this.client || !this.isConnected) {
      logger.warn('Cache unavailable, skipping get');
      return null;
    }

    try {
      const value = await this.client.get(key);
      if (!value) return null;
      return JSON.parse(value) as T;
    } catch (error) {
      logger.error('Error getting from cache:', error);
      return null;
    }
  }

  async set(key: string, value: unknown, ttl?: number): Promise<void> {
    if (!this.client || !this.isConnected) {
      logger.warn('Cache unavailable, skipping set');
      return;
    }

    try {
      const serialized = JSON.stringify(value);
      const expiryTime = ttl || config.cache.ttl;
      await this.client.setEx(key, expiryTime, serialized);
    } catch (error) {
      logger.error('Error setting cache:', error);
    }
  }

  async delete(key: string): Promise<void> {
    if (!this.client || !this.isConnected) {
      logger.warn('Cache unavailable, skipping delete');
      return;
    }

    try {
      await this.client.del(key);
    } catch (error) {
      logger.error('Error deleting from cache:', error);
    }
  }

  async deletePattern(pattern: string): Promise<void> {
    if (!this.client || !this.isConnected) {
      logger.warn('Cache unavailable, skipping delete pattern');
      return;
    }

    try {
      const keys = await this.client.keys(pattern);
      if (keys.length > 0) {
        await this.client.del(keys);
      }
    } catch (error) {
      logger.error('Error deleting cache pattern:', error);
    }
  }

  async disconnect(): Promise<void> {
    if (this.client && this.isConnected) {
      await this.client.disconnect();
      this.isConnected = false;
      logger.info('Redis Client Disconnected');
    }
  }
}

export const cacheService = new CacheService();
