"""
Prometheus metrics module for L1nkZip.

This module provides comprehensive metrics collection for monitoring the URL shortener service.
"""

import time
from typing import Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from prometheus_client.core import CollectorRegistry

from l1nkzip.config import settings


class MetricsCollector:
    """Prometheus metrics collector for L1nkZip."""

    def __init__(self):
        """Initialize metrics collectors."""
        self.registry = CollectorRegistry()

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "l1nkzip_http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status_code", "handler"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "l1nkzip_http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "handler"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry,
        )

        self.http_requests_in_progress = Gauge(
            "l1nkzip_http_requests_in_progress",
            "Number of HTTP requests currently in progress",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # Business Metrics
        self.urls_created_total = Counter(
            "l1nkzip_urls_created_total",
            "Total number of URLs shortened",
            registry=self.registry,
        )

        self.redirects_total = Counter(
            "l1nkzip_redirects_total",
            "Total number of URL redirects",
            registry=self.registry,
        )

        self.phishing_blocks_total = Counter(
            "l1nkzip_phishing_blocks_total",
            "Total number of phishing URLs blocked",
            registry=self.registry,
        )

        # Cache Metrics
        self.cache_hits_total = Counter(
            "l1nkzip_cache_hits_total",
            "Total number of cache hits",
            ["operation"],
            registry=self.registry,
        )

        self.cache_misses_total = Counter(
            "l1nkzip_cache_misses_total",
            "Total number of cache misses",
            ["operation"],
            registry=self.registry,
        )

        self.cache_operations_total = Counter(
            "l1nkzip_cache_operations_total",
            "Total number of cache operations",
            ["operation", "success"],
            registry=self.registry,
        )

        # Database Metrics
        self.db_connections_active = Gauge(
            "l1nkzip_db_connections_active",
            "Number of active database connections",
            registry=self.registry,
        )

        self.db_query_duration_seconds = Histogram(
            "l1nkzip_db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry,
        )

        # Rate Limiting Metrics
        self.rate_limit_exceeded_total = Counter(
            "l1nkzip_rate_limit_exceeded_total",
            "Total number of rate limit violations",
            ["endpoint"],
            registry=self.registry,
        )

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        handler: str,
        duration: Optional[float] = None,
    ):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code, handler=handler
        ).inc()

        if duration is not None:
            self.http_request_duration_seconds.labels(
                method=method, endpoint=endpoint, handler=handler
            ).observe(duration)

    def record_url_created(self):
        """Record URL creation."""
        self.urls_created_total.inc()

    def record_redirect(self):
        """Record URL redirect."""
        self.redirects_total.inc()

    def record_phishing_block(self):
        """Record phishing URL block."""
        self.phishing_blocks_total.inc()

    def record_cache_operation(
        self, operation: str, hit: Optional[bool] = None, success: bool = True
    ):
        """Record cache operation metrics."""
        if hit is True:
            self.cache_hits_total.labels(operation=operation).inc()
        elif hit is False:
            self.cache_misses_total.labels(operation=operation).inc()

        self.cache_operations_total.labels(
            operation=operation, success=str(success).lower()
        ).inc()

    def record_db_operation(self, operation: str, duration: Optional[float] = None):
        """Record database operation metrics."""
        if duration is not None:
            self.db_query_duration_seconds.labels(operation=operation).observe(duration)

    def record_rate_limit_exceeded(self, endpoint: str):
        """Record rate limit violation."""
        self.rate_limit_exceeded_total.labels(endpoint=endpoint).inc()

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry)

    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return settings.metrics_enabled


# Global metrics instance
metrics = MetricsCollector()


def get_metrics_response():
    """Get metrics response for FastAPI endpoint."""
    return metrics.get_metrics()


def record_request_start(method: str, endpoint: str):
    """Record the start of an HTTP request."""
    if not metrics.is_enabled():
        return None

    metrics.http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    return time.time()


def record_request_end(
    method: str,
    endpoint: str,
    status_code: int,
    handler: str,
    start_time: Optional[float] = None,
):
    """Record the end of an HTTP request."""
    if not metrics.is_enabled():
        return

    duration = None
    if start_time is not None:
        duration = time.time() - start_time

    metrics.record_http_request(method, endpoint, status_code, handler, duration)
    metrics.http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
