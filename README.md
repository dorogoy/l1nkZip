# l1nkZip

L1nkZip is a simple URL shortener API. It is written in Python and uses the [Fastapi](https://fastapi.tiangolo.com/) framework and [Pony ORM](https://ponyorm.org/). The main priority of this project is to be simple and low in resource usage. The first option in L1nkZip is always a combination of [sqlite](https://www.sqlite.org) for the database and [litestream](https://litestream.io) for its replication and resilience from cheap and volatile environments. Using Pony ORM allows to use any other database if sqlite is not of your taste. This app is mainly focused on running inside a container managed by Kubernetes or docker.

The working API is available at https://l1nk.zip/docs

The full documentation is available at https://dorogoy.github.io/l1nkZip.

## Features

* Simple to setup and use. It just works.
* Low resource usage and also low maintenance.
* If you choose the [litestream](https://litestream.io) way, it is very cheap to host. You will have a reliable database almost impossible to destroy, backed on any compatible S3 bucket.
* Do you want to use Postgresql? No problem. Just change the configuration and you are ready to go.
* Optional protection against phisphing with the [PhishTank](https://phishtank.org) database.
* Built-in rate limiting protection against abuse through mass URL creation or enumeration attacks using [slowapi](https://github.com/laurentS/slowapi).
* Optional Redis caching for improved performance on frequently accessed URLs (TTL-based with configurable expiration).
* **Comprehensive monitoring and observability** with Prometheus metrics, structured logging, and alerting support.
* **Comprehensive test suite** with more than 159 tests covering unit, API, and integration scenarios (75%+ coverage).

## Companion CLI Tool

L1nkZip has an official command-line interface client available at [l1nkzip-cli](https://github.com/dorogoy/l1nkzip-cli). The CLI provides a modern, rich-powered interface to interact with the API, featuring:

- URL shortening from the command line
- Link information retrieval
- Admin functionality (requires API token)
- Beautiful output formatting with the rich library
- Self-contained execution with uv

Check out the [CLI repository](https://github.com/dorogoy/l1nkzip-cli) for installation and usage instructions.

## Redis Caching

L1nkZip supports optional Redis caching to improve performance for frequently accessed URLs. When enabled, URL redirects are cached with a configurable TTL (Time To Live), reducing database hits and improving response times.

### Configuration

To enable Redis caching, set the following environment variables:

```bash
# Redis server URL (required for caching)
REDIS_SERVER=redis://localhost:6379/0

# Cache TTL in seconds (optional, defaults to 86400 = 24 hours)
REDIS_TTL=3600
```

### How It Works

1. **Cache Hit**: When a short URL is accessed, the system first checks Redis for a cached redirect
2. **Cache Miss**: If not found in cache, it queries the database and stores the result in Redis
3. **Visit Counting**: Visit counts are updated asynchronously even for cache hits to maintain accuracy
4. **TTL Expiration**: Cached entries automatically expire after the configured TTL

### Benefits

- **Performance**: Faster redirects for frequently accessed URLs
- **Scalability**: Reduced database load under high traffic
- **Optional**: Completely disabled when `REDIS_SERVER` is not set
- **Configurable**: TTL can be adjusted based on usage patterns

### Example

```bash
# Enable caching with default 24-hour TTL
export REDIS_SERVER=redis://localhost:6379/0

# Or with custom 1-hour TTL
export REDIS_SERVER=redis://localhost:6379/0
export REDIS_TTL=3600
```

When Redis is not configured, L1nkZip operates normally without any caching, ensuring backward compatibility.

## Monitoring and Observability

L1nkZip provides comprehensive monitoring and observability features to ensure reliable operation and performance tracking. The monitoring system is built around Prometheus metrics and structured logging, making it easy to integrate with modern observability stacks.

### Prometheus Metrics

L1nkZip exposes a standard Prometheus metrics endpoint at `/metrics` when monitoring is enabled. The metrics include:

#### HTTP Metrics
- **Request Count**: Total HTTP requests by method, endpoint, and status code
- **Request Latency**: Response time histograms with configurable buckets
- **Active Requests**: Gauge of currently processing requests

#### Business Metrics
- **URLs Created**: Counter of shortened URLs
- **Redirects**: Counter of URL redirections
- **Phishing Blocks**: Counter of blocked malicious URLs

#### Performance Metrics
- **Cache Performance**: Hit/miss rates for Redis operations
- **Database Queries**: Query duration histograms
- **Rate Limiting**: Violation counters by endpoint

### Configuration

Enable monitoring by setting the following environment variables:

```bash
# Enable Prometheus metrics endpoint
METRICS_ENABLED=true

# Optional: Configure logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARN, ERROR
LOG_FORMAT=text         # text or json for structured logging
```

### Structured Logging

When `LOG_FORMAT=json` is set, L1nkZip outputs structured JSON logs with comprehensive context including:
- Request tracing IDs and correlation IDs
- Response times and status codes
- Error details and stack traces
- Cache operation results
- User agent and client information

### Alerting and Dashboards

The monitoring system is designed to work with:
- **Prometheus** for metrics collection and alerting
- **Grafana** for visualization and dashboards
- **Alertmanager** for notification routing

Pre-configured alert rules are available for:
- High error rates (>5% for 5 minutes)
- Service availability issues
- Performance degradation
- Security events (phishing blocks)

### Example Usage

```bash
# Enable monitoring
export METRICS_ENABLED=true
export LOG_FORMAT=json

# Start the application
uv run uvicorn l1nkzip.main:app --host 0.0.0.0 --port 80

# Access metrics
curl http://localhost:80/metrics
```

### Kubernetes Integration

For Kubernetes deployments, the monitoring system integrates seamlessly with:
- **Prometheus Operator** for automated service discovery
- **Grafana** for dashboard visualization
- **Alertmanager** for notification management

See the [self-hosting documentation](user-guide/docs/selfhosting.md) for detailed Kubernetes configuration examples.

## Testing

L1nkZip includes a comprehensive test suite to ensure code quality and reliability:

### Quick Start
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test categories
make test-unit      # Unit tests only
make test-api       # API tests only
make test-integration  # Integration tests only
```

### Test Coverage
- **159 total tests** across unit, API, and integration scenarios
- **75%+ code coverage** with detailed reporting
- **Test isolation** using in-memory databases and mocked external services
- **Performance optimized** with parallel execution and fast fixtures

### Test Categories
- **Unit Tests**: Individual component testing (54 tests)
- **API Tests**: FastAPI endpoint validation (61 tests)
- **Integration Tests**: End-to-end workflow testing (24 tests)

For detailed information about the testing strategy, fixtures, and best practices, see the [Testing Documentation](user-guide/docs/testing.md).
