import redis.asyncio as redis
from typing import Optional, Any
import json
from app.core.config import settings
from app.core.logger import logger


class CacheService:
    def __init__(self) -> None:
        self.redis: Optional[redis.Redis] = None
        self.is_connected = False

    async def connect(self) -> None:
        """Connect to Redis"""
        # Skip Redis connection if host is not configured
        if not settings.REDIS_HOST:
            logger.info("Redis host not configured, skipping Redis connection")
            self.is_connected = False
            return

        try:
            self.redis = await redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            await self.redis.ping()
            self.is_connected = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis and self.is_connected:
            await self.redis.close()
            self.is_connected = False
            logger.info("Redis disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis or not self.is_connected:
            logger.warning("Cache unavailable, skipping get")
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        if not self.redis or not self.is_connected:
            logger.warning("Cache unavailable, skipping set")
            return

        try:
            serialized = json.dumps(value, default=str)
            expiry = ttl or settings.CACHE_TTL
            await self.redis.setex(key, expiry, serialized)
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        if not self.redis or not self.is_connected:
            logger.warning("Cache unavailable, skipping delete")
            return

        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern"""
        if not self.redis or not self.is_connected:
            logger.warning("Cache unavailable, skipping delete pattern")
            return

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting cache pattern: {e}")


cache_service = CacheService()
