"""
Tests for Prometheus metrics functionality.
"""

from unittest.mock import patch

from l1nkzip.metrics import (
    MetricsCollector,
    metrics,
    record_request_end,
    record_request_start,
)


class TestMetricsCollector:
    """Test the MetricsCollector class functionality."""

    def test_metrics_collector_initialization(self):
        """Test that MetricsCollector initializes properly."""
        collector = MetricsCollector()

        # Check that all metric attributes are created
        assert hasattr(collector, "http_requests_total")
        assert hasattr(collector, "http_request_duration_seconds")
        assert hasattr(collector, "http_requests_in_progress")
        assert hasattr(collector, "urls_created_total")
        assert hasattr(collector, "redirects_total")
        assert hasattr(collector, "phishing_blocks_total")
        assert hasattr(collector, "cache_hits_total")
        assert hasattr(collector, "cache_misses_total")
        assert hasattr(collector, "cache_operations_total")
        assert hasattr(collector, "db_connections_active")
        assert hasattr(collector, "db_query_duration_seconds")
        assert hasattr(collector, "rate_limit_exceeded_total")

    def test_record_http_request(self):
        """Test recording HTTP request metrics."""
        collector = MetricsCollector()

        # Record a request
        collector.record_http_request("GET", "/health", 200, "health_check", 0.1)

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_http_requests_total" in metrics_output
        assert b"l1nkzip_http_request_duration_seconds" in metrics_output

    def test_record_url_created(self):
        """Test recording URL creation metrics."""
        collector = MetricsCollector()

        # Record URL creation
        collector.record_url_created()

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_urls_created_total" in metrics_output

    def test_record_redirect(self):
        """Test recording redirect metrics."""
        collector = MetricsCollector()

        # Record redirect
        collector.record_redirect()

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_redirects_total" in metrics_output

    def test_record_phishing_block(self):
        """Test recording phishing block metrics."""
        collector = MetricsCollector()

        # Record phishing block
        collector.record_phishing_block()

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_phishing_blocks_total" in metrics_output

    def test_record_cache_operation(self):
        """Test recording cache operation metrics."""
        collector = MetricsCollector()

        # Record cache hit
        collector.record_cache_operation("get", hit=True, success=True)

        # Record cache miss
        collector.record_cache_operation("get", hit=False, success=True)

        # Record cache operation failure
        collector.record_cache_operation("set", success=False)

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_cache_hits_total" in metrics_output
        assert b"l1nkzip_cache_misses_total" in metrics_output
        assert b"l1nkzip_cache_operations_total" in metrics_output

    def test_record_db_operation(self):
        """Test recording database operation metrics."""
        collector = MetricsCollector()

        # Record database operation
        collector.record_db_operation("select", 0.05)

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_db_query_duration_seconds" in metrics_output

    def test_record_rate_limit_exceeded(self):
        """Test recording rate limit violation metrics."""
        collector = MetricsCollector()

        # Record rate limit violation
        collector.record_rate_limit_exceeded("/url")

        # Get metrics output
        metrics_output = collector.get_metrics()
        assert b"l1nkzip_rate_limit_exceeded_total" in metrics_output

    @patch("l1nkzip.config.settings.metrics_enabled", True)
    def test_record_request_start_end_enabled(self):
        """Test request start/end recording when metrics are enabled."""
        # Record request start
        start_time = record_request_start("GET", "/health")
        assert start_time is not None

        # Record request end
        record_request_end("GET", "/health", 200, "health_check", start_time)

        # Check that metrics were recorded
        metrics_output = metrics.get_metrics()
        assert b"l1nkzip_http_requests_total" in metrics_output

    @patch("l1nkzip.config.settings.metrics_enabled", False)
    def test_record_request_start_end_disabled(self):
        """Test request start/end recording when metrics are disabled."""
        # Record request start
        start_time = record_request_start("GET", "/health")
        assert start_time is None

        # Record request end (should not raise error)
        record_request_end("GET", "/health", 200, "health_check", start_time)

    def test_get_metrics_format(self):
        """Test that get_metrics returns proper Prometheus format."""
        collector = MetricsCollector()

        # Add some test data
        collector.record_http_request("GET", "/health", 200, "health_check", 0.1)

        metrics_output = collector.get_metrics()

        # Check that it's bytes
        assert isinstance(metrics_output, bytes)

        # Check that it contains expected Prometheus format elements
        output_str = metrics_output.decode("utf-8")
        assert "# HELP" in output_str
        assert "# TYPE" in output_str
        assert "l1nkzip_http_requests_total" in output_str

    def test_is_enabled(self):
        """Test the is_enabled method."""
        collector = MetricsCollector()

        with patch("l1nkzip.config.settings.metrics_enabled", True):
            assert collector.is_enabled() is True

        with patch("l1nkzip.config.settings.metrics_enabled", False):
            assert collector.is_enabled() is False


class TestMetricsIntegration:
    """Integration tests for metrics functionality."""

    def test_global_metrics_instance(self):
        """Test that the global metrics instance is properly initialized."""
        assert hasattr(metrics, "record_http_request")
        assert hasattr(metrics, "record_url_created")
        assert hasattr(metrics, "record_redirect")
        assert hasattr(metrics, "record_phishing_block")
        assert hasattr(metrics, "record_cache_operation")
        assert hasattr(metrics, "record_db_operation")
        assert hasattr(metrics, "record_rate_limit_exceeded")
        assert hasattr(metrics, "get_metrics")
        assert hasattr(metrics, "is_enabled")

    def test_metrics_with_labels(self):
        """Test metrics with different label combinations."""
        collector = MetricsCollector()

        # Test different HTTP methods and endpoints
        collector.record_http_request("GET", "/health", 200, "health_check", 0.1)
        collector.record_http_request("POST", "/url", 201, "create_url", 0.2)
        collector.record_http_request("GET", "/abc123", 301, "get_url", 0.05)

        # Test cache operations with different operations
        collector.record_cache_operation("get", hit=True)
        collector.record_cache_operation("set", hit=None, success=True)
        collector.record_cache_operation("delete", hit=None, success=False)

        # Get metrics and verify they contain the expected labels
        metrics_output = collector.get_metrics().decode("utf-8")

        # Check for method and endpoint labels
        assert 'method="GET"' in metrics_output
        assert 'method="POST"' in metrics_output
        assert 'endpoint="/health"' in metrics_output
        assert 'endpoint="/url"' in metrics_output

        # Check for cache operation labels
        assert 'operation="get"' in metrics_output
        assert 'operation="set"' in metrics_output
        assert 'operation="delete"' in metrics_output
        assert 'success="true"' in metrics_output
        assert 'success="false"' in metrics_output
