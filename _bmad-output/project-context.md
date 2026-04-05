---
project_name: 'l1nkZip'
user_name: 'Sergio'
date: '2026-04-05'
sections_completed:
  [
    'technology_stack',
    'language_rules',
    'framework_rules',
    'testing_rules',
    'quality_rules',
    'workflow_rules',
    'anti_patterns',
  ]
status: 'complete'
rule_count: 35
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns that AI agents must follow when implementing code. Focus on unobvious details agents might miss._

---

## Technology Stack & Versions

**Core:**
- Python 3.12+ / FastAPI 0.135.3 / Uvicorn 0.41.0
- Pony ORM 0.7.19 (multi-DB abstraction)
- Pydantic Settings 2.4.0 (env-only configuration)
- validators 0.34.0 (URL validation)

**Optional Dependencies (graceful degradation required):**
- Redis 5.0.1 (caching)
- Prometheus Client 0.24.1 (metrics)
- httpx 0.28.1 (PhishTank HTTP client)

**Middleware:**
- SlowAPI 0.1.9 (rate limiting)
- Jinja2 3.1.6 (error page templates)

**Tooling:**
- Ruff 0.12.7 (lint + format, rules: F, E, W, I, N, B, line-length: 120)
- ty (type checking)
- pytest 9.0.2 + pytest-asyncio 1.3.0 + pytest-cov 7.0.0
- uv (package manager)

---

## Critical Implementation Rules

### Pony ORM Rules

- **`@db_session` decorator is mandatory** on every function that touches the database — no exceptions
- **`flush()` before accessing auto-generated fields**: call `entity.flush()` to get the auto-increment `id` before using it (see `insert_link` in `models.py`)
- **Pony ORM is synchronous**: use `asyncio.get_event_loop().run_in_executor(None, sync_func, args)` when calling DB operations from async handlers
- **DB provider selection happens at startup** via `ponyorm_settings` dict in `config.py` keyed by `settings.db_type`
- **Never call Pony ORM operations without a `db_session`** — even reads require it

### Settings & Configuration

- **Use the global `settings` singleton** from `l1nkzip.config` — NOT FastAPI dependency injection
- **All configuration via `Settings` class** (Pydantic Settings) — never read env vars directly outside `config.py`
- **Never hardcode configuration values** — add new settings to the `Settings` class
- The `settings` object is created at module import time as a module-level singleton

### Optional Components Guard Pattern

Every optional component MUST follow this pattern:

```python
# Redis cache: check is_enabled(), wrap in try/except
if cache.is_enabled():
    try:
        result = await cache.get(key)
    except Exception as e:
        logger.error("Cache error", extra={"error": str(e)})
        # Continue without cache — graceful degradation

# Prometheus metrics: check settings.metrics_enabled
if settings.metrics_enabled:
    metrics.record_redirect()

# PhishTank: check settings.phishtank
if settings.phishtank:
    phish = await retry_phishtank_check(url)
```

### Logging

- **Module-level logger**: `logger = get_logger(__name__)` at the top of each module
- **Structured context via `extra={}`**: always include relevant context keys
- **Log levels**: ERROR (user-facing failures), WARNING (degraded features), INFO (startup/config), DEBUG (tracing)
- **Never log tokens, credentials, or sensitive data**

### Validation Helpers

- Validation functions are **standalone functions** in `main.py`, not Pydantic validators
- They return the cleaned value or raise `HTTPException` directly
- Pattern: `validate_url(url) -> str`, `validate_admin_token(token) -> str`, `validate_short_link(link) -> str`

### Rate Limiting

- **`@limiter.limit()` decorator requires `request: Request` as first parameter** to the endpoint function
- Rate limits configured via `settings.rate_limit_create` and `settings.rate_limit_redirect`
- SlowAPIMiddleware is added globally — the decorator controls per-endpoint limits

### Async Patterns

- **Fire-and-forget visit counting**: `asyncio.create_task(increment_visit_async(link))`
- **PhishTank retry with exponential backoff**: `await asyncio.sleep(2**attempt)` in `retry_phishtank_check()`
- **Sync DB in async context**: always use `run_in_executor` — never call Pony ORM directly from async handlers

---

## Testing Rules

- **Module clearing for isolation**: `conftest.py` clears `sys.modules` entries for `l1nkzip.config`, `l1nkzip.models`, `l1nkzip.main` before each test to ensure clean state
- **`inmemory` db type** for all tests (`:sharedmemory:` SQLite)
- **Rate limits set high** in test settings (`1000/minute`, `2000/minute`)
- **`metrics_collector` fixture** resets the Prometheus `CollectorRegistry` per test — use it in any test that touches metrics
- **Test organization**: `tests/unit/`, `tests/api/`, `tests/integration/`
- **Run tests**: `make test` (runs check + all test suites), `make test-unit`, `make test-api`, `make test-integration`
- **Coverage**: `make test-cov` (HTML report) or `make test-cov-xml` (CI XML report)

---

## Code Quality & Style Rules

- **Line length**: 120 characters
- **Ruff rules**: F, E, W, I, N, B (pyflakes, pycodestyle, isort, pep8-naming, bugbear)
- **Lint command**: `make check` (runs `ruff check`, `ruff format --check`, `ty check`)
- **Format command**: `make fmt` (runs `ruff format` + `ruff check --fix`)
- **No comments** in code unless explicitly requested
- **Type hints on all function signatures**
- **Import sorting**: `known-first-party = ["l1nkzip", "tests"]`, `force-sort-within-sections = true`
- **Naming**: files `snake_case`, classes `PascalCase`, functions `snake_case`, constants `UPPER_SNAKE_CASE`

---

## Development Workflow Rules

- **Commit messages**: Conventional Commits format (`feat:`, `fix:`, `refactor:`, etc.)
- **Build**: `make build` (runs tests then Docker build)
- **Dev server**: `make run_dev` (uvicorn with `--reload`)
- **Package manager**: `uv` — always use `uv run` to execute commands

---

## Critical Don't-Miss Rules

### Anti-Patterns to Avoid

- **Do NOT use FastAPI dependency injection for settings** — use the global `settings` singleton from `l1nkzip.config`
- **Do NOT forget `@db_session`** on any function that accesses Pony ORM entities
- **Do NOT call Pony ORM directly from async handlers** — use `run_in_executor`
- **Do NOT add comments** in code unless explicitly asked
- **Do NOT hardcode configuration values** — add to `Settings` class
- **Do NOT import `asyncio` inside functions** — import at module level (unlike existing `main.py:get_url` which has a local import — this is a legacy pattern to avoid)

### Edge Cases

- **Duplicate URL creation**: `insert_link` handles race conditions with `flush()` + `rollback()` + retry pattern — preserve this
- **SQLite Litestream PRAGMA**: the `sqlite_litestream` callback sets `busy_timeout`, `synchronous`, and `wal_autocheckpoint` — do not modify
- **URL normalization**: Pydantic `HttpUrl` may add trailing slashes — tests account for this with `url in [url, url + "/"]`
- **Short link format**: validated as `^[a-zA-Z0-9_-]{4,20}$`

### Security Rules

- **Never expose internal error details** in API responses — use generic messages
- **Token validation** checks length >= 16 and character whitelist before comparison
- **URL validation** rejects non-HTTP/HTTPS schemes, dangerous schemes, and URLs > 2048 chars
- **Never log tokens or credentials** — sanitize the `extra` dict

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- Run `make check` after making changes
- Run `make test` to verify nothing is broken

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules

Last Updated: 2026-04-05
