"""
Redis caching module for URL redirects.

This module provides optional Redis caching for URL redirects to reduce database hits.
Caching is only enabled when the REDIS_SERVER environment variable is set.
"""

from typing import Optional

import redis.asyncio as redis

from l1nkzip.config import settings


class Cache:
    """Redis cache client for URL redirects."""

    def __init__(self):
        """Initialize Redis client if REDIS_SERVER is configured."""
        self.client: Optional[redis.Redis] = None
        if settings.redis_server:
            try:
                self.client = redis.from_url(settings.redis_server)
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                self.client = None

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
            print(f"Redis get error: {e}")
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
            ttl_value = ttl or settings.redis_ttl
            await self.client.set(key, value, ex=ttl_value)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
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
            print(f"Redis delete error: {e}")
            return False

    def is_enabled(self) -> bool:
        """Check if caching is enabled.

        Returns:
            True if Redis is configured and connected, False otherwise
        """
        return self.client is not None


# Global cache instance
cache = Cache()
