---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-generate-epics-and-stories
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# l1nkZip - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for l1nkZip, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

> [!NOTE]
> This is a brownfield project (v0.4.4). Epics 1, 2, 3, and 4 represent the existing production system and are marked as **[Baseline - Already Implemented]**. No active development is required for them.
> Epic 5 represents the new feature scope for this iteration and is marked as **[Active Development]**.

## Requirements Inventory

### Functional Requirements

FR1: API consumers can submit a long URL and receive a unique short link
FR2: API consumers can configure a custom encoding alphabet for short link generation
FR3: API consumers can retrieve the original URL from a short link identifier
FR4: The system can generate short, unique identifiers using a bit-shuffling algorithm
FR5: Visitors can be redirected from a short link to the original URL via HTTP redirect
FR6: The system can count visits to each shortened URL
FR7: The system can increment visit counts asynchronously to avoid blocking redirects
FR8: Admins can view visit counts for individual URLs
FR9: Admins can list all shortened URLs in the system via a token-protected endpoint
FR10: Admins can verify system health including database connectivity
FR11: Admins can authenticate using a token passed via environment configuration
FR12: The system can cache URL mappings in an optional external cache layer
FR13: The system can serve redirects from cache without querying the database
FR14: The system can gracefully degrade when the cache layer is unavailable
FR15: The system can populate the cache with URL mappings on first access
FR16: The system can check submitted URLs against the PhishTank database
FR17: The system can block creation of short links for known phishing URLs
FR18: The system can block redirection to known phishing URLs
FR19: Admins can update the PhishTank database via CLI or API
FR20: The system can expose Prometheus-compatible metrics at a dedicated endpoint
FR21: The system can track and report request counts, latencies, and error rates
FR22: The system can produce structured logs in JSON or text format
FR23: The system can log with configurable severity levels (DEBUG, INFO, WARN, ERROR)
FR24: The system can enforce configurable rate limits on URL creation requests
FR25: The system can enforce configurable rate limits on URL redirection requests
FR26: The system can reject requests exceeding rate limits with appropriate HTTP responses
FR27: The system can store URL mappings in SQLite (default)
FR28: The system can store URL mappings in PostgreSQL, MySQL, Oracle, or CockroachDB
FR29: The system can replicate SQLite data to S3-compatible storage via Litestream
FR30: The system can recover SQLite data from S3 backup after data loss
FR31: Operators can configure all settings via environment variables
FR32: Operators can deploy the system as a single Docker container
FR33: Operators can deploy the system in Kubernetes with health checks
FR34: The system can expose auto-generated OpenAPI documentation
FR35: CLI users can shorten URLs from the command line
FR36: CLI users can retrieve information about existing short links
FR37: CLI users can list all shortened URLs (admin)
FR38: CLI users can update the PhishTank database (admin)
FR39: The system can expose a Model Context Protocol (MCP) server over Server-Sent Events (SSE) transport
FR40: The system can expose URL management capabilities as MCP tools (e.g., creating and retrieving short links)
FR41: The system can protect administrative MCP tools (e.g., listing all URLs) using the standard token authentication mechanism

### NonFunctional Requirements

NFR1: URL redirection must complete in under 100ms at p95 (cache miss) and under 10ms (cache hit)
NFR2: URL creation must complete in under 200ms at p95 including encoding and database write
NFR3: The system must handle at least 100 concurrent requests without degradation
NFR4: Cache lookup must add no more than 5ms latency to the redirect path
NFR5: Database operations must not block the async event loop
NFR6: Admin endpoints must reject requests without a valid token with HTTP 401/403
NFR7: All URLs must be validated before storage to prevent injection attacks
NFR8: Rate limiting must be enforced before request processing to prevent abuse
NFR9: PhishTank checks must complete within a configurable timeout to avoid blocking
NFR10: No sensitive data (tokens, database credentials) must appear in logs
NFR11: The system must operate as a single-instance service (horizontal scaling not required for MVP)
NFR12: Redis caching must reduce database load proportionally to cache hit rate
NFR13: The system must handle SQLite databases up to 10GB without performance degradation
NFR14: Litestream replication must not impact request latency during backup operations
NFR15: The system must support Redis as optional cache with graceful degradation on failure
NFR16: Prometheus metrics must be exposed in standard exposition format compatible with any scraper
NFR17: PhishTank integration must support both anonymous and API key modes
NFR18: Database backend must be swappable via environment configuration without code changes
NFR19: Structured logs must be consumable by standard log aggregation tools (ELK, Loki, etc.)

### Additional Requirements

ARCH-1: Single-process monolithic architecture deployed behind Uvicorn.
ARCH-2: Environment-based configuration singleton (`Settings`) from `config.py` using Pydantic Settings, injected via FastAPI dependency injection (no direct env access outside `config.py`).
ARCH-3: Database provider factory supporting SQLite, PostgreSQL, MySQL, Oracle, CockroachDB based on `DB_TYPE` environment variable.
ARCH-4: Custom stateless and independently testable URL generator (`generator.py`) using a deterministic bit-shuffling algorithm and configurable encoding alphabet via `GENERATOR_STRING`.
ARCH-5: Optional component graceful degradation pattern: Redis, Prometheus, and PhishTank failures must only log warnings and degrade gracefully without crashing the application.
ARCH-6: Global rate limiting and request metrics collection implemented as FastAPI middleware.
ARCH-7: Centralized structured logging module (`logging.py`) supporting both JSON and text formats based on `LOG_FORMAT` and `LOG_LEVEL` env vars.
ARCH-8: Embedded MCP server in FastAPI monolith using Server-Sent Events (SSE) exposing GET `/mcp/sse` and POST `/mcp/messages` routes.
ARCH-9: Unified token-based authentication mechanism validating tokens of length >= 16 and whitelisted characters for administrative endpoints and administrative MCP tools.

### UX Design Requirements

*No UX design requirements (API-first backend backend service without user interface)*

### FR Coverage Map

FR1: Epic 1 - API consumer submits a long URL and receives a unique short link.
FR2: Epic 1 - Custom encoding alphabet configuration for short link generation.
FR3: Epic 1 - Retrievability of the original URL from a short link identifier.
FR4: Epic 1 - Short, unique identifier generation using a bit-shuffling algorithm.
FR5: Epic 1 - Redirection of visitors from a short link to the original URL.
FR6: Epic 1 - Visit counting for each shortened URL.
FR7: Epic 1 - Asynchronous increment of visit counts to prevent blocking redirects.
FR8: Epic 1 - Retrieve and view visit counts for individual URLs.
FR9: Epic 3 - List all shortened URLs in the system via a token-protected endpoint.
FR10: Epic 3 - Verify system health including database connectivity.
FR11: Epic 3 - Token-based authentication passed via environment configuration.
FR12: Epic 4 - Cache URL mappings in an optional external cache layer (Redis).
FR13: Epic 1 - Serve redirects from cache without querying the database (In-memory fallback).
FR14: Epic 4 - Graceful degradation when the external cache layer (Redis) is unavailable.
FR15: Epic 1 - Populate the cache with URL mappings on first access (In-memory fallback).
FR16: Epic 2 - Check submitted URLs against the PhishTank database.
FR17: Epic 2 - Block creation of short links for known phishing URLs.
FR18: Epic 2 - Block redirection to known phishing URLs.
FR19: Epic 3 - Admins can update the PhishTank database via CLI or API.
FR20: Epic 3 - Expose Prometheus-compatible metrics at a dedicated endpoint.
FR21: Epic 3 - Track and report request counts, latencies, and error rates via middleware.
FR22: Epic 3 - Structured logging in JSON or text formats.
FR23: Epic 3 - Configurable log severity levels (DEBUG, INFO, WARN, ERROR).
FR24: Epic 2 - Enforce rate limits on URL creation requests via SlowAPI.
FR25: Epic 2 - Enforce rate limits on URL redirection requests via SlowAPI.
FR26: Epic 2 - Rate limit enforcement rejection responses.
FR27: Epic 1 - Store URL mappings in SQLite (default database).
FR28: Epic 4 - Support PostgreSQL, MySQL, Oracle, CockroachDB as alternative database providers.
FR29: Epic 4 - S3 replication of SQLite database using Litestream.
FR30: Epic 4 - Litestream S3 recovery validation.
FR31: Epic 1 - Configure all system settings via environment variables (Pydantic Settings).
FR32: Epic 1 - Package and deploy the application as a single Docker container.
FR33: Epic 3 - Kubernetes deployment configuration and health probes.
FR34: Epic 1 - Expose auto-generated OpenAPI documentation.
FR35: Epic 3 - Command-line interface tool to shorten URLs.
FR36: Epic 3 - CLI retrieval of information for existing short links.
FR37: Epic 3 - CLI administrative list command.
FR38: Epic 3 - CLI administrative command to update PhishTank database.
FR39: Epic 5 - MCP server over Server-Sent Events (SSE) transport protocol.
FR40: Epic 5 - URL management capabilities exposed as standard MCP tools.
FR41: Epic 5 - Standard token authentication mechanism protecting administrative MCP tools.

## Epic List

### Epic 1: [Baseline - Already Implemented] Core URL Shortening, Redirection & In-Memory Cache
This epic establishes the foundational high-performance pipeline. API consumers can submit long URLs to get shortened, deterministic, non-sequential codes using a bit-shuffling algorithm. Visitors are transparently redirected to original URLs, using an in-memory cache to serve hot redirects (sub-10ms) and asynchronous visit counting to prevent SQLite write-concurrency database locking. The system runs as a single-process container configured through environment variables (Pydantic Settings) using SQLite for storage.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR13, FR15, FR27, FR31, FR32, FR34

### Epic 2: [Baseline - Already Implemented] Security, Rate Limiting & Phishing Protection
This epic introduces active defense mechanisms to safeguard the application and its visitors. It integrates SlowAPI middleware to enforce configurable rate limits on creation and redirection endpoints, and incorporates an optional PhishTank client with local caching and non-blocking timeouts to actively scan and intercept submissions/redirections to known malicious URLs.
**FRs covered:** FR16, FR17, FR18, FR24, FR25, FR26

### Epic 3: [Baseline - Already Implemented] Administration, Observability & CLI
This epic delivers full manageability and developer-focused tooling. It implements unified token-based authentication to guard administrative operations, structured logging (JSON/text) with configurable severity, a Prometheus-compatible metrics endpoint fed by middleware, and Kubernetes deployment charts with health checks. It also introduces a CLI companion supporting command-line CRUD operations and administrative actions (like triggering PhishTank updates).
**FRs covered:** FR9, FR10, FR11, FR19, FR20, FR21, FR22, FR23, FR33, FR35, FR36, FR37, FR38

### Epic 4: [Baseline - Already Implemented] High Availability, Litestream & Data Portability
This epic readies the application for production-grade resilience and database flexibility. It adds support for Redis as an optional, high-performance external cache with graceful fallback behavior, refactors database connectivity using a Pony ORM provider factory to swap backends (SQLite, PostgreSQL, MySQL, Oracle, CockroachDB) via the environment, and configures S3 replication/recovery via Litestream.
**FRs covered:** FR12, FR14, FR28, FR29, FR30

### Epic 5: [Active Development] Model Context Protocol (MCP) Integration
This epic opens l1nkZip directly to AI agent workflows. It embeds an MCP server directly within the FastAPI monolith using the SSE transport protocol. This exposes core shortening, retrieval, and administrative capabilities as discoverable MCP tools, securing administrative operations using the unified token-based auth mechanism.
**FRs covered:** FR39, FR40, FR41

---

## Epic 1: [Baseline - Already Implemented] Core URL Shortening, Redirection & In-Memory Cache

*This epic represents existing working functionality in production.*

### Story 1.1: Configuración de Entorno y Módulo de Logs Estructurados
*(Completed)*

### Story 1.2: Generador de Identificadores determinista con Alfabeto Personalizable
*(Completed)*

### Story 1.3: Definición del Modelo de Datos e Inicialización de Pony ORM
*(Completed)*

### Story 1.4: Endpoint de Creación de Enlaces Cortos (POST /url) con OpenAPI
*(Completed)*

### Story 1.5: Endpoint de Redirección (GET /{link}) con Caché Local en Memoria
*(Completed)*

### Story 1.6: Registro Asíncrono y No Bloqueante de Visitas
*(Completed)*

---

## Epic 2: [Baseline - Already Implemented] Security, Rate Limiting & Phishing Protection

*This epic represents existing working functionality in production.*

### Story 2.1: Middleware de Rate Limiting con Fallback en Memoria (SlowAPI)
*(Completed)*

### Story 2.2: Cliente de Validación PhishTank Asíncrono con Timeout y API Key
*(Completed)*

### Story 2.3: Intercepción de Phishing y Renderizado de Página de Advertencia (Jinja2)
*(Completed)*

---

## Epic 3: [Baseline - Already Implemented] Administration, Observability & CLI

*This epic represents existing working functionality in production.*

### Story 3.1: Autenticación por Token Unificada para Operaciones Administrativas
*(Completed)*

### Story 3.2: Endpoints de Administración de Enlaces (/urls) e Inspección de Salud (/health)
*(Completed)*

### Story 3.3: Middleware de Monitoreo y Exposición de Métricas Prometheus (/metrics)
*(Completed)*

### Story 3.4: Manifiestos de Kubernetes y Configuración de Probes de Salud
*(Completed)*

### Story 3.5: CLI Companion (l1nkzip-cli) para Operaciones Rápidas desde Terminal
*(Completed)*

---

## Epic 4: [Baseline - Already Implemented] High Availability, Litestream & Data Portability

*This epic represents existing working functionality in production.*

### Story 4.1: Caché Externa Opcional en Redis y Degradación Elegante Automática
*(Completed)*

### Story 4.2: Factoría Dinámica Multibase de Datos mediante Pony ORM
*(Completed)*

### Story 4.3: Replicación en S3 con Litestream y Validación de Recuperación (Disaster Recovery)
*(Completed)*

---

## Epic 5: [Active Development] Model Context Protocol (MCP) Integration

This epic opens l1nkZip directly to AI agent workflows. It embeds an MCP server directly within the FastAPI monolith using the SSE transport protocol. This exposes core shortening, retrieval, and administrative capabilities as discoverable MCP tools, securing administrative operations using the unified token-based auth mechanism.

### Story 5.1: Servidor MCP SSE y Rutas de Conexión en FastAPI (GET/POST)

As an AI agent,
I want to initiate a Model Context Protocol session using SSE (Server-Sent Events) transport,
So that I can discover and call l1nkZip tools remotely.

**Acceptance Criteria:**

**Given** the FastAPI application is running.
**When** a GET request is made to `/mcp/sse`.
**Then** the server returns an SSE event stream with the endpoint URL to send messages to.
**When** a client sends a message via POST to `/mcp/messages?sessionId=<id>`.
**Then** the message is successfully routed to the embedded MCP server, and responses are streamed back to the client.
**And** standard FastAPI lifespan handlers close all connections gracefully on server shutdown.

### Story 5.2: Exposición de Herramientas Públicas de Gestión (shorten y get_url)

As an AI agent,
I want to discover and invoke core URL management tools (like shortening and retrieving destination URLs) directly via MCP,
So that I can integrate link shortening into my agentic flows.

**Acceptance Criteria:**

**Given** an active MCP SSE session.
**When** the client queries for available tools.
**Then** the server exposes `shorten_url` and `get_original_url` in the tools list with correct schemas.
**When** the client calls the `shorten_url` tool with a valid long URL.
**Then** the tool executes the business logic, registers the link in the database, and returns the short URL.

### Story 5.3: Herramientas MCP Administrativas y Seguridad por Token

As an authorized AI agent,
I want administrative capabilities (like listing all shortened URLs) exposed as secure MCP tools protected by the standard token authentication,
So that I can manage the link index.

**Acceptance Criteria:**

**Given** a secure admin token is set.
**When** an MCP tool call is made to `list_urls` without a valid token.
**Then** the MCP tool call returns an error response stating that the request is unauthorized.
**When** the call includes the correct token.
**Then** the tool succeeds and returns the complete list of shortened URLs and their stats.
