"""
Tests for Redis caching functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest

from l1nkzip.cache import Cache, cache
from l1nkzip.models import increment_visit_async


class TestCache:
    """Test the Cache class functionality."""

    def test_cache_disabled_when_no_redis_server(self):
        """Test that cache is disabled when REDIS_SERVER is not set."""
        with patch("l1nkzip.config.settings.redis_server", None):
            test_cache = Cache()
            assert test_cache.client is None
            assert not test_cache.is_enabled()

    def test_cache_enabled_when_redis_server_set(self):
        """Test that cache is enabled when REDIS_SERVER is set."""
        with patch("l1nkzip.config.settings.redis_server", "redis://localhost:6379/0"):
            with patch("redis.asyncio.from_url") as mock_from_url:
                mock_from_url.return_value = "mock_redis_client"
                test_cache = Cache()
                assert test_cache.client is not None
                assert test_cache.is_enabled()

    @pytest.mark.asyncio
    async def test_get_returns_none_when_cache_disabled(self):
        """Test that get returns None when cache is disabled."""
        with patch("l1nkzip.config.settings.redis_server", None):
            test_cache = Cache()
            result = await test_cache.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_cache_disabled(self):
        """Test that set returns False when cache is disabled."""
        with patch("l1nkzip.config.settings.redis_server", None):
            test_cache = Cache()
            result = await test_cache.set("test_key", "test_value")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_with_enabled_cache(self):
        """Test get operation with enabled cache."""
        with patch("l1nkzip.config.settings.redis_server", "redis://localhost:6379/0"):
            test_cache = Cache()
            test_cache.client = AsyncMock()
            test_cache.client.get.return_value = "cached_value"

            result = await test_cache.get("test_key")
            assert result == "cached_value"
            test_cache.client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_set_with_enabled_cache(self):
        """Test set operation with enabled cache."""
        with patch("l1nkzip.config.settings.redis_server", "redis://localhost:6379/0"):
            with patch("l1nkzip.config.settings.redis_ttl", 3600):
                test_cache = Cache()
                test_cache.client = AsyncMock()
                test_cache.client.set.return_value = True

                result = await test_cache.set("test_key", "test_value")
                assert result is True
                test_cache.client.set.assert_called_once_with(
                    "test_key", "test_value", ex=3600
                )

    @pytest.mark.asyncio
    async def test_get_handles_exceptions(self):
        """Test that get handles Redis exceptions gracefully."""
        with patch("l1nkzip.config.settings.redis_server", "redis://localhost:6379/0"):
            test_cache = Cache()
            test_cache.client = AsyncMock()
            test_cache.client.get.side_effect = Exception("Redis error")

            result = await test_cache.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_handles_exceptions(self):
        """Test that set handles Redis exceptions gracefully."""
        with patch("l1nkzip.config.settings.redis_server", "redis://localhost:6379/0"):
            test_cache = Cache()
            test_cache.client = AsyncMock()
            test_cache.client.set.side_effect = Exception("Redis error")

            result = await test_cache.set("test_key", "test_value")
            assert result is False


class TestAsyncVisitCounting:
    """Test async visit counting functionality."""

    @pytest.mark.asyncio
    async def test_increment_visit_async_calls_sync_function(self):
        """Test that increment_visit_async properly calls the sync function."""
        # We need to patch the sync function that's called inside the async function
        # Need to patch where the function is used, not where it's defined
        with patch("l1nkzip.models.increment_visit") as mock_increment:
            mock_increment.return_value = None

            # Call the async function
            await increment_visit_async("test_link")

            # Verify the sync function was called
            mock_increment.assert_called_once_with("test_link")

    @pytest.mark.asyncio
    async def test_increment_visit_async_handles_exceptions(self):
        """Test that increment_visit_async handles exceptions gracefully."""
        # We need to patch the sync function that's called inside the async function
        # Need to patch where the function is used, not where it's defined
        with patch("l1nkzip.models.increment_visit") as mock_increment:
            mock_increment.side_effect = Exception("Database error")

            # The async function will propagate the exception from the thread executor
            with pytest.raises(Exception, match="Database error"):
                await increment_visit_async("test_link")

            # Verify the sync function was still called
            mock_increment.assert_called_once_with("test_link")


class TestIntegrationWithFastAPI:
    """Integration tests for caching with FastAPI endpoints."""

    def test_cache_module_imports_correctly(self):
        """Test that cache module can be imported without errors."""
        assert hasattr(cache, "get")
        assert hasattr(cache, "set")
        assert hasattr(cache, "is_enabled")

    def test_models_async_function_imports_correctly(self):
        """Test that async visit counting function can be imported."""
        from l1nkzip.models import increment_visit_async

        assert callable(increment_visit_async)

    @pytest.mark.asyncio
    async def test_cache_operations_with_mock_redis(self):
        """Test cache operations with a mock Redis client."""
        # Create a mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "https://example.com"
        mock_redis.set.return_value = True

        # Create cache instance with mock client
        test_cache = Cache()
        test_cache.client = mock_redis

        # Test get operation
        result = await test_cache.get("redirect:test123")
        assert result == "https://example.com"
        mock_redis.get.assert_called_once_with("redirect:test123")

        # Test set operation
        result = await test_cache.set("redirect:test123", "https://example.com")
        assert result is True
        mock_redis.set.assert_called_once_with(
            "redirect:test123", "https://example.com", ex=86400
        )
