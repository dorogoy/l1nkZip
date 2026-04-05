---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
  - step-08-complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
workflowType: 'architecture'
project_name: 'l1nkZip'
user_name: 'Sergio'
date: '2026-04-05'
status: 'complete'
completedAt: '2026-04-05'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
38 FRs across 9 capability areas. The core architectural flow is a request pipeline: URL creation (encode → store → respond) and URL redirection (lookup → count visit → redirect). Supporting capabilities — caching, metrics, logging, phishing checks, rate limiting — are cross-cutting concerns that layer onto the core pipeline.

**Non-Functional Requirements:**
Performance NFRs are the primary architectural driver: redirect < 100ms p95 (cache miss), < 10ms (cache hit), creation < 200ms p95. Integration NFRs mandate graceful degradation for all optional components. Security NFRs require token-based auth, URL validation, and rate limiting as middleware.

**Scale & Complexity:**
- Primary domain: Backend API (REST)
- Complexity level: Low
- Estimated architectural components: 6-8 (app, models, generator, cache, metrics, logging, config, phishtank)

### Technical Constraints & Dependencies

- **Python 3.12+** with FastAPI as async framework
- **Pony ORM** for multi-database abstraction (SQLite, PostgreSQL, MySQL, Oracle, CockroachDB)
- **Single-process deployment** via Uvicorn ASGI server
- **SQLite + Litestream** for default database resilience (external to application)
- **Optional components** (Redis, Prometheus, PhishTank) must degrade gracefully when unavailable
- **100% environment-based configuration** via Pydantic Settings

## Starter Template Evaluation

### Primary Technology Domain

Backend API (REST) — Python/FastAPI. Already implemented and in production.

### Existing Technology Stack (Brownfield — No Starter Selection Needed)

**Language & Runtime:**
- Python 3.12+ with FastAPI 0.115.12
- Uvicorn 0.35.0 as ASGI server
- Async-first architecture

**ORM & Database:**
- Pony ORM 0.7.19 (multi-database abstraction)
- SQLite as default (with Litestream for replication)
- PostgreSQL, MySQL, Oracle, CockroachDB supported

**Configuration:**
- Pydantic Settings 2.4.0 (environment-based)
- 100% env var configuration

**Code Quality:**
- Ruff 0.12.7 (linting + formatting)
- ty (type checking, replaced mypy)
- pytest + pytest-asyncio (testing)

**Optional Dependencies:**
- Redis 5.0.1 (caching)
- Prometheus Client 0.21.0 (metrics)
- HTTpx 0.28.1 (PhishTank HTTP client)
- SlowAPI 0.1.9 (rate limiting)
- Jinja2 3.1.6 (error page templates)

**Build & Deploy:**
- Docker single-stage build
- uv for dependency management
- Makefile for development tasks

**CLI Companion:** [l1nkzip-cli](https://github.com/dorogoy/l1nkzip-cli) (separate repo)

## Core Architectural Decisions

### AD1: Single-Process Monolithic Architecture

**Decision:** l1nkZip runs as a single FastAPI process behind Uvicorn. No microservices, no message queues, no service mesh.

**Rationale:** The application has a single responsibility (URL shortening/redirection) with low complexity. A monolith minimizes operational overhead, deployment complexity, and hosting cost — aligned with the "simple and cheap" differentiator.

**Implications:**
- All components (models, cache, metrics, logging) are in-process Python modules
- Horizontal scaling not supported (by design for MVP)
- Single point of failure mitigated by Litestream data replication

### AD2: Pony ORM for Multi-Database Abstraction

**Decision:** Use Pony ORM as the data access layer with a provider-based configuration strategy.

**Rationale:** Enables the core differentiator of database portability — SQLite for cheap hosting, PostgreSQL/MySQL/Oracle/CockroachDB for enterprise deployments. Pony ORM's Pythonic query syntax keeps the codebase simple.

**Implications:**
- Database provider selected at startup via `DB_TYPE` environment variable
- Factory pattern in config.py constructs the appropriate connection
- All database operations encapsulated in repository-style model functions

### AD3: Custom Bit-Shuffling URL Encoding

**Decision:** Use a custom bit-shuffling algorithm for generating short URL identifiers, not sequential IDs.

**Rationale:** Non-sequential IDs prevent enumeration attacks and make short URLs unpredictable while remaining deterministic and reversible. Configurable encoding alphabet via `GENERATOR_STRING`.

**Implications:**
- IDs are encoded/decoded without external state
- No collision risk due to monotonically increasing internal counter
- Generator module is stateless and independently testable

### AD4: Optional Components with Graceful Degradation

**Decision:** Redis caching, Prometheus metrics, and PhishTank integration are optional features that must not break the application when unavailable.

**Rationale:** Aligns with the deployment flexibility goal — operators should be able to run l1nkZip with minimal dependencies. Each optional component is guarded by configuration flags and wrapped in try/catch with fallback behavior.

**Pattern:**
- **Redis cache:** On connection failure, skip cache and query database directly
- **Prometheus metrics:** On `METRICS_ENABLED=false`, skip all metric recording
- **PhishTank:** On `PHISHTANK=false`, skip URL validation entirely

### AD5: Middleware-Based Cross-Cutting Concerns

**Decision:** Rate limiting and metrics collection implemented as FastAPI middleware, applied globally to all requests.

**Rationale:** Cross-cutting concerns should not pollute business logic. Middleware ensures consistent application across all endpoints without individual handler changes.

**Implications:**
- SlowAPI middleware handles rate limiting before request processing
- Metrics middleware records request start/end times and route-level metrics
- Both are configurable via environment variables

### AD6: Environment-Only Configuration

**Decision:** All configuration via environment variables through Pydantic Settings. No config files, no CLI flags.

**Rationale:** Container-native approach. Environment variables are the standard configuration mechanism for Docker and Kubernetes. Pydantic Settings provides type validation, default values, and a clean settings object.

**Implications:**
- Single `Settings` class in `config.py` holds all configuration
- Settings object injected via FastAPI dependency injection
- No `.env` file required (but supported for local development)

### AD7: Structured Logging as Centralized Module

**Decision:** Centralized logging module (`logging.py`) with configurable format (JSON/text) and level.

**Rationale:** Replaces ad-hoc `print()` statements with proper structured logging. JSON format enables integration with log aggregation tools (ELK, Loki). Single configuration point via `LOG_LEVEL` and `LOG_FORMAT` environment variables.

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database Naming:**
- Tables: `snake_case` plural (e.g., `links`)
- Columns: `snake_case` (e.g., `created_at`, `visit_count`)
- Pony ORM entities: `PascalCase` (e.g., `Link`, `PhishEntry`)

**API Naming:**
- Endpoints: `snake_case` in paths, plural nouns (`/urls`, `/health`)
- Query parameters: `snake_case` (`rate_limit_create`)
- Environment variables: `UPPER_SNAKE_CASE` (`DB_TYPE`, `REDIS_SERVER`)

**Code Naming:**
- Files: `snake_case` (`cache.py`, `generator.py`)
- Classes: `PascalCase` (`Settings`, `Link`)
- Functions/methods: `snake_case` (`encode_url`, `set_visit`)
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_PORT`)
- Private functions: `_leading_underscore` (`_init_metrics`)

### Structure Patterns

**Project Organization:**
- `l1nkzip/` — Application source code (single package)
- `tests/` — All tests, organized by type (`tests/unit/`, `tests/api/`, `tests/integration/`)
- Configuration in `l1nkzip/config.py` — single source of truth
- Each module is self-contained: domain logic + related functions

**Module Responsibility:**
- `main.py` — FastAPI app, routes, middleware registration
- `models.py` — Database entities, CRUD operations
- `generator.py` — URL encoding/decoding (pure functions)
- `cache.py` — Redis caching layer
- `metrics.py` — Prometheus metrics definitions and recording
- `logging.py` — Centralized logging configuration
- `config.py` — Settings class and database provider factory
- `phishtank.py` — PhishTank integration

### Format Patterns

**API Response Formats:**
- Success responses: plain JSON with data directly (no wrapper)
- Error responses: JSON with `detail` field (FastAPI default)
- Redirect: HTTP 307 with `Location` header (no body)
- No pagination needed (admin list returns all)

**Data Formats:**
- JSON field names: `snake_case` (Python convention with FastAPI)
- Dates: ISO 8601 strings where needed
- Booleans: `true`/`false` in JSON

### Process Patterns

**Error Handling:**
- Use FastAPI `HTTPException` for API errors
- Log errors at appropriate level (ERROR for unexpected, WARNING for degraded service)
- Never expose internal details in error responses
- Optional component failures: log WARNING + continue with degraded behavior

**Logging Patterns:**
- Use structured logging via `l1nkzip/logging.py`
- Always include context: request path, URL ID, operation type
- Log levels: ERROR (failures affecting users), WARNING (degraded features), INFO (startup/config), DEBUG (development tracing)
- Never log sensitive data (tokens, credentials)

**Configuration Access:**
- Inject `Settings` via FastAPI dependency injection
- Never read environment variables directly outside `config.py`
- Never hardcode configuration values

### Enforcement Guidelines

**All implementations MUST:**
- Follow `snake_case` for all Python identifiers (PEP 8)
- Use type hints on all function signatures
- Handle optional component failures gracefully (try/except + fallback)
- Log meaningful context at appropriate levels
- Access configuration only through the injected `Settings` object
- Write tests for all new functionality in the appropriate test directory

## Project Structure & Boundaries

### Complete Project Tree

```
l1nkZip/
├── l1nkzip/                    # Application package
│   ├── __init__.py
│   ├── cache.py                # Redis caching layer (optional)
│   ├── config.py               # Pydantic Settings + DB provider factory
│   ├── generator.py            # URL encoding/decoding (bit-shuffling)
│   ├── logging.py              # Centralized structured logging
│   ├── main.py                 # FastAPI app, routes, middleware
│   ├── metrics.py              # Prometheus metrics definitions
│   ├── models.py               # Pony ORM entities + CRUD operations
│   ├── phishtank.py            # PhishTank integration (optional)
│   └── templates/              # Jinja2 error page templates
├── tests/                      # Test suite
│   ├── conftest.py             # Shared fixtures
│   ├── unit/                   # Unit tests (54 tests)
│   ├── api/                    # API endpoint tests (61 tests)
│   └── integration/            # Integration tests (36 tests)
├── docs/                       # Documentation
├── user-guide/                 # End user documentation
├── _bmad-output/               # BMad planning artifacts
│   └── planning-artifacts/
│       ├── prd.md
│       └── architecture.md
├── Dockerfile                  # Single-stage Docker build
├── Makefile                    # Development task automation
├── pyproject.toml              # Project config, dependencies, tool settings
├── uv.lock                     # Dependency lock file
├── README.md                   # Project overview
├── CHANGELOG.md                # Version history
├── LICENSE                     # MIT License
└── monitoring-blueprint.md     # Monitoring reference
```

### Component Boundaries & Communication

```
Request → Middleware Stack → Route Handler → Response
           ├── Rate Limiting (SlowAPI)
           └── Metrics Collection
           
Route Handler → config.py (Settings via DI)
              → models.py (Pony ORM → Database)
              → cache.py (Redis, optional)
              → generator.py (URL encoding)
              → phishtank.py (PhishTank, optional)
              → metrics.py (Prometheus, optional)
              → logging.py (Structured logging)
```

### FR-to-Module Mapping

| FR Category | Primary Module(s) | Supporting Module(s) |
|---|---|---|
| URL Management | `main.py`, `generator.py`, `models.py` | `cache.py`, `config.py` |
| Visit Tracking | `models.py`, `main.py` | `logging.py` |
| Administration | `main.py`, `models.py` | `config.py` (token auth) |
| Caching | `cache.py` | `config.py`, `logging.py` |
| Phishing Protection | `phishtank.py`, `main.py` | `config.py`, `logging.py` |
| Observability | `metrics.py`, `logging.py` | `main.py` (middleware) |
| Rate Limiting | `main.py` (middleware) | `config.py` |
| Database & Storage | `models.py`, `config.py` | — |
| Configuration & Deployment | `config.py`, `Dockerfile`, `Makefile` | — |
| CLI Integration | External: l1nkzip-cli | `main.py` (API endpoints) |

## Architecture Validation Result

### Coherence Validation

**Decision Compatibility:** All 7 architectural decisions are mutually compatible. The monolith + Pony ORM + env-only config + middleware cross-cutting concerns form a coherent, simple architecture. No contradictory decisions found.

**Pattern Consistency:** Naming conventions (`snake_case` everywhere), structure patterns (flat `l1nkzip/` package), and process patterns (graceful degradation) are all consistent with each other and with the technology stack.

**Structure Alignment:** The flat module structure directly supports the monolithic architecture. Each module maps to exactly one responsibility.

### Requirements Coverage

**FR Coverage:** All 38 FRs across 9 capability areas have architectural support via mapped modules.

**NFR Coverage:** All 19 NFRs addressed — performance (async + caching), security (token auth + rate limiting + validation), scalability (single-instance by design), integration (graceful degradation + standard formats).

### Implementation Readiness

- All 7 critical decisions documented with rationale and implications
- Technology stack fully specified with versions
- Naming conventions established
- Project structure mapped to requirements
- Error handling and logging patterns defined
- Optional component degradation patterns specified
- Configuration access patterns enforced

**Overall Status:** READY FOR IMPLEMENTATION
**Confidence Level:** High — brownfield project with existing working codebase.
