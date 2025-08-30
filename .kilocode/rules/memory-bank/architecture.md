# Architecture

## System architecture
L1nkZip is a FastAPI-based URL shortener with a modular architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Pony ORM      │    │   URL Generator │
│   (main.py)     │◄──►│   (models.py)   │◄──►│   (generator.py)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTTP Clients  │    │   Database      │    │   Configuration │
│   (Web/API)     │    │   (SQLite/Other)│    │   (config.py)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Source Code paths
- **Main application**: [`l1nkzip/main.py`](l1nkzip/main.py:1) - FastAPI app with endpoints
- **Database models**: [`l1nkzip/models.py`](l1nkzip/models.py:1) - Pony ORM entities and database operations
- **Configuration**: [`l1nkzip/config.py`](l1nkzip/config.py:1) - Settings and database configuration
- **URL generation**: [`l1nkzip/generator.py`](l1nkzip/generator.py:1) - Short URL encoding/decoding
- **Phishing protection**: [`l1nkzip/phishtank.py`](l1nkzip/phishtank.py:1) - PhishTank integration
- **Version management**: [`l1nkzip/version.py`](l1nkzip/version.py:1) - Version tracking

## Key technical decisions
1. **FastAPI**: Chosen for its performance, async support, and automatic OpenAPI documentation
2. **Pony ORM**: Selected for its simplicity and multi-database support (SQLite, PostgreSQL, MySQL, Oracle, CockroachDB)
3. **SQLite + Litestream**: Default database choice for simplicity and cost-effectiveness with cloud replication
4. **Custom URL encoding**: Uses a bit-shuffling algorithm for predictable but non-sequential short URLs
5. **Environment-based configuration**: Uses Pydantic settings for flexible deployment

## Design patterns in use
- **Repository pattern**: Database operations encapsulated in model functions
- **Dependency Injection**: FastAPI's built-in DI for configuration and services
- **Factory pattern**: Database provider configuration in [`config.py`](l1nkzip/config.py:38)
- **Strategy pattern**: Multiple database backends with consistent interface

## Component relationships
- The main app depends on models for data access
- Models depend on generator for URL encoding
- Configuration is centralized and injected throughout
- PhishTank integration is optional and configurable

## Critical implementation paths
1. URL shortening: POST `/url` → [`insert_link()`](l1nkzip/models.py:63) → [`encode_url()`](l1nkzip/generator.py:132)
2. URL redirection: GET `/{link}` → [`set_visit()`](l1nkzip/models.py:74) → redirect
3. Phishing check: Integrated in both creation and redirection via [`get_phish()`](l1nkzip/phishtank.py:40)
4. Database health: GET `/health` → [`check_db_connection()`](l1nkzip/models.py:95)
