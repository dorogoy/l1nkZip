# Tech

## Technologies used
- **Python 3.12+**: Core programming language
- **FastAPI 0.115.12**: Web framework with async support and OpenAPI documentation
- **Pony ORM 0.7.19**: Object-relational mapper supporting multiple databases
- **Pydantic Settings 2.4.0**: Settings management with environment variables
- **SQLite**: Default database (file-based, in-memory options)
- **Litestream**: Database replication for SQLite to S3-compatible storage
- **Redis 5.0.1**: Optional caching layer for improved performance
- **Prometheus Client 0.21.0**: Metrics collection and exposure for monitoring
- **HTTpx 0.28.1**: Async HTTP client for PhishTank integration
- **Jinja2 3.1.6**: Templating engine for error pages
- **Ruff 0.12.7**: Fast Python linter and formatter
- **Mypy 1.10.0**: Static type checking
- **SlowAPI 0.1.9**: Rate limiting library for abuse protection
- **Uvicorn 0.35.0**: ASGI server for FastAPI
- **pytest-asyncio 0.25.1**: Async testing support for pytest
- **Rich**: CLI output formatting (used in l1nkzip-cli)
- **uv**: Python package manager (used in l1nkzip-cli and main project)
- **Ruff**: Linting and formatting (used in l1nkzip-cli and main project)

## Development setup
1. **Virtual environment**: Managed via Makefile with `make env_ok`
2. **Dependency management**: `uv` for core dependencies (replaced pip)
3. **Code quality**: Ruff for linting/formatting, Mypy for type checking
4. **Testing**: pytest framework with comprehensive test coverage including generator, rate limiting, and API integration tests
5. **Build system**: Makefile with targets for development, testing, and Docker builds (using uv)

## Technical constraints
- **Python 3.7+ compatibility**: Maintains backward compatibility
- **Database flexibility**: Supports multiple backends through Pony ORM
- **Minimal dependencies**: Keeps package footprint small for containerization
- **Async-first**: Leverages FastAPI's async capabilities where beneficial
- **Type hints**: Comprehensive type annotations throughout codebase

## Dependencies
Core runtime dependencies:
- fastapi
- httpx
- jinja2
- pony
- prometheus-client
- pydantic-settings
- redis
- slowapi
- uvicorn
- validators

## Companion CLI Technologies
The official L1nkZip CLI ([l1nkzip-cli](https://github.com/dorogoy/l1nkzip-cli)) uses:
- **Python 3.12+**: CLI-specific runtime
- **Rich**: Beautiful terminal output formatting
- **uv**: Modern Python package and project manager
- **Ruff**: Fast linting and code formatting
- **Click**: Command-line interface creation
- **httpx**: Async HTTP client for API communication

Optional database drivers:
- psycopg2-binary (PostgreSQL)
- MySQL-python (MySQL)
- cx_oracle (Oracle)

## Tool usage patterns
- **Makefile**: Primary development interface with targets:
  - `make env_ok`: Setup virtual environment
  - `make fmt`: Format code with Ruff
  - `make check`: Run static analysis and type checking
  - `make test`: Run unit tests
  - `make run_dev`: Start development server
  - `make build`: Build Docker image (now uses uv)

- **Version management**: [`update-version.sh`](update-version.sh:1) script for consistent version updates
- **uv.lock**: Lock file for deterministic dependency installation

- **Docker deployment**: Single-stage build with Python 3.12 and uv

- **Python execution**: All direct Python execution must use `uv` with the prefix command `uv run --`

## CLI tool usage
The official L1nkZip CLI provides:
- `shorten <url>`: Shorten URLs from command line
- `info <link>`: Get information about short links
- `list`: List all URLs (requires admin token)
- `update-phishtank`: Update PhishTank database (admin only)
- Configurable via `L1NKZIP_TOKEN` and `L1NKZIP_API_URL` environment variables

## Database support matrix
| Database | Support Level | Driver Required | Notes |
|----------|---------------|-----------------|-------|
| SQLite   | Primary       | Built-in        | Default choice with Litestream |
| PostgreSQL | Full        | psycopg2-binary | Production-ready |
| MySQL    | Full          | MySQL-python    | Requires additional driver |
| Oracle   | Full          | cx_oracle       | Requires additional driver |
| CockroachDB | Full       | psycopg2-binary | PostgreSQL-compatible |

## Environment configuration
Configuration is managed through environment variables with sensible defaults:
- `API_DOMAIN`: Domain for shortened URLs
- `DB_TYPE`: Database type (inmemory, sqlite, postgres, mysql, oracle, cockroachdb)
- `DB_NAME`: Database name or filename
- `TOKEN`: Admin authentication token
- `GENERATOR_STRING`: Custom URL encoding alphabet
- `PHISHTANK`: PhishTank integration (false, anonymous, or API key)
- `REDIS_SERVER`: Full Redis URL for caching (optional, e.g., redis://localhost:6379/0)
- `REDIS_TTL`: Cache TTL in seconds (optional, default: 86400 = 24 hours)
- `RATE_LIMIT_CREATE`: Rate limit for URL creation (default: "10/minute")
- `RATE_LIMIT_REDIRECT`: Rate limit for URL redirection (default: "120/minute")
- `METRICS_ENABLED`: Enable Prometheus metrics endpoint (default: false)
- `LOG_LEVEL`: Logging level (default: "INFO", options: "DEBUG", "INFO", "WARN", "ERROR")
- `LOG_FORMAT`: Log format (default: "text", options: "text", "json")
