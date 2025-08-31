"""
Pytest configuration and shared fixtures for L1nkZip tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client import Counter, Gauge, Histogram
from prometheus_client.core import CollectorRegistry

from l1nkzip.config import Settings


@pytest.fixture
def test_settings():
    """Test settings with in-memory database and disabled external services."""
    settings = Settings()
    settings.db_type = "inmemory"
    settings.redis_server = None
    settings.metrics_enabled = True
    settings.phishtank = None
    settings.rate_limit_create = "1000/minute"
    settings.rate_limit_redirect = "2000/minute"
    settings.token = "test-admin-token-12345"  # Match the admin_token fixture
    return settings


@pytest.fixture
def test_client(test_settings):
    """Test client with in-memory database and test settings."""
    # Clear modules first to ensure clean import
    import sys

    modules_to_clear = ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    # Patch settings before importing
    with patch("l1nkzip.config.settings", test_settings):
        # Import fresh modules
        from l1nkzip.main import app

        return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_client = MagicMock()
    # Configure async methods to return awaitable objects
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def metrics_collector():
    """Patch the global metrics collector for each test."""
    from l1nkzip.metrics import metrics

    # Store original registry
    original_registry = metrics.registry

    # Create a new registry for this test
    metrics.registry = CollectorRegistry()

    # Re-initialize metrics with new registry
    metrics.http_requests_total = Counter(
        "l1nkzip_http_requests_total",
        "Total number of HTTP requests",
        ["method", "endpoint", "status_code", "handler"],
        registry=metrics.registry,
    )
    metrics.http_request_duration_seconds = Histogram(
        "l1nkzip_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint", "handler"],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
        registry=metrics.registry,
    )
    metrics.http_requests_in_progress = Gauge(
        "l1nkzip_http_requests_in_progress",
        "Number of HTTP requests currently in progress",
        ["method", "endpoint"],
        registry=metrics.registry,
    )
    metrics.urls_created_total = Counter(
        "l1nkzip_urls_created_total",
        "Total number of URLs shortened",
        registry=metrics.registry,
    )
    metrics.redirects_total = Counter(
        "l1nkzip_redirects_total",
        "Total number of URL redirects",
        registry=metrics.registry,
    )
    metrics.phishing_blocks_total = Counter(
        "l1nkzip_phishing_blocks_total",
        "Total number of phishing URLs blocked",
        registry=metrics.registry,
    )
    metrics.cache_hits_total = Counter(
        "l1nkzip_cache_hits_total",
        "Total number of cache hits",
        ["operation"],
        registry=metrics.registry,
    )
    metrics.cache_misses_total = Counter(
        "l1nkzip_cache_misses_total",
        "Total number of cache misses",
        ["operation"],
        registry=metrics.registry,
    )
    metrics.cache_operations_total = Counter(
        "l1nkzip_cache_operations_total",
        "Total number of cache operations",
        ["operation", "success"],
        registry=metrics.registry,
    )
    metrics.db_connections_active = Gauge(
        "l1nkzip_db_connections_active",
        "Number of active database connections",
        registry=metrics.registry,
    )
    metrics.db_query_duration_seconds = Histogram(
        "l1nkzip_db_query_duration_seconds",
        "Database query duration in seconds",
        ["operation"],
        buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
        registry=metrics.registry,
    )
    metrics.rate_limit_exceeded_total = Counter(
        "l1nkzip_rate_limit_exceeded_total",
        "Total number of rate limit violations",
        ["endpoint"],
        registry=metrics.registry,
    )

    yield metrics

    # Restore original registry
    metrics.registry = original_registry


@pytest.fixture
def mock_phishtank():
    """Mock PhishTank API response."""
    with patch("l1nkzip.phishtank.get_phish") as mock:
        mock.return_value = False  # Default: not phishing
        yield mock


@pytest.fixture
async def async_test_client(test_settings):
    """Async test client for async tests."""
    with patch("l1nkzip.config.settings", test_settings):
        # Clear modules to ensure settings are reloaded
        import sys

        modules_to_clear = ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # Import fresh modules
        from fastapi.testclient import TestClient

        from l1nkzip.main import app

        return TestClient(app)


# Test data fixtures
@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return [
        "https://example.com",
        "https://google.com",
        "https://github.com/dorogoy/l1nkZip",
        "https://docs.fastapi.tiangolo.com/",
    ]


@pytest.fixture
def invalid_urls():
    """Invalid URLs for testing."""
    return [
        "not-a-url",
        "ftp://example.com",
        "javascript:alert(1)",
        "",
        "https://" + "a" * 3000,  # Very long URL
    ]


@pytest.fixture
def admin_token():
    """Valid admin token for testing."""
    # Use a token that meets the validation requirements:
    # - At least 16 characters long
    # - Contains only allowed characters: a-zA-Z0-9!@#$%^&*()_+-=
    return "test-admin-token-12345"


@pytest.fixture
def invalid_tokens():
    """Invalid admin tokens for testing."""
    return [
        "short",
        "invalid!@#$%token",
        " ",
        "",
    ]
