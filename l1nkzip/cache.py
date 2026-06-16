"""
Redis caching module for URL redirects.

This module provides optional Redis caching for URL redirects to reduce database hits.
Caching is only enabled when the REDIS_SERVER environment variable is set.
"""

from typing import Optional

import redis.asyncio as redis

from l1nkzip import config
from l1nkzip.logging import get_logger


logger = get_logger(__name__)


class Cache:
    """Redis cache client for URL redirects."""

    def __init__(self):
        """Initialize Redis client if REDIS_SERVER is configured."""
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get or lazily initialize the Redis client.

        The client is created on first access so that ``config.settings`` is
        read at runtime rather than at import time, which keeps test patches
        effective and avoids connection side effects on module import.
        """
        if self._client is None and config.settings.redis_server:
            try:
                self._client = redis.from_url(config.settings.redis_server, decode_responses=True)
            except Exception as e:
                logger.error("Failed to connect to Redis", extra={"error": str(e)})
        return self._client

    @client.setter
    def client(self, value: Optional[redis.Redis]) -> None:
        self._client = value

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.client:
            return None

        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error("Redis get error", extra={"error": str(e), "key": key})
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            ttl_value = ttl or config.settings.redis_ttl
            await self.client.set(key, value, ex=ttl_value)
            return True
        except Exception as e:
            logger.error("Redis set error", extra={"error": str(e), "key": key})
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error", extra={"error": str(e), "key": key})
            return False

    def is_enabled(self) -> bool:
        """Check if caching is enabled.

        Returns:
            True if Redis is configured and connected, False otherwise
        """
        return self.client is not None


# Global cache instance
cache = Cache()
