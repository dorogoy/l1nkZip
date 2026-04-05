---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
inputDocuments:
  - .kilocode/rules/memory-bank/brief.md
  - .kilocode/rules/memory-bank/product.md
  - .kilocode/rules/memory-bank/architecture.md
  - .kilocode/rules/memory-bank/tech.md
  - .kilocode/rules/memory-bank/context.md
classification:
  projectType: api_backend
  domain: general
  complexity: low
  projectContext: brownfield
workflowType: 'prd'
---

# Product Requirements Document - l1nkZip

**Author:** Sergio
**Date:** 2026-04-05

## Executive Summary

l1nkZip is a self-hosted URL shortener API built for developers and operators who need a reliable, low-cost link management service without the overhead of complex infrastructure. It provides a REST API for creating short URLs, redirecting visitors, and optionally protecting against phishing — all deployable as a single container. The core use case: shortening a URL via POST and redirecting via GET, with no user registration required.

### What Makes This Special

- **Near-zero hosting cost**: SQLite + Litestream replicates the database to any S3-compatible bucket, providing production-grade durability for pennies per month — no managed database required.
- **Database portability**: Pony ORM abstracts the data layer, supporting SQLite, PostgreSQL, MySQL, Oracle, and CockroachDB with a configuration change.
- **Developer-friendly**: Official CLI client, automatic OpenAPI docs, token-based admin endpoints, and optional Prometheus metrics out of the box.
- **Privacy by design**: No user accounts, no tracking beyond visit counters, no analytics harvesting.
- **Optional phishing protection**: PhishTank integration blocks malicious URLs — a feature absent from most self-hosted shorteners.

## Project Classification

| Attribute | Value |
|---|---|
| **Project Type** | API Backend (REST) |
| **Domain** | General |
| **Complexity** | Low |
| **Project Context** | Brownfield — existing production system (v0.4.4) |

## Success Criteria

### User Success

- A developer shortens a URL via a single API call (`POST /url`) or CLI command (`l1nkzip shorten <url>`) and receives a working short link in under 500ms — no registration, no configuration beyond the API URL.
- An operator deploys l1nkZip as a single Docker container with SQLite + Litestream and has a production-ready URL shortener running in under 5 minutes.
- A visitor clicks a short link and is redirected to the original URL transparently, with optional phishing protection keeping them safe.
- An admin lists, manages, and monitors all shortened URLs via token-protected endpoints or the CLI.

### Business Success

- Maintain a stable, reliable public API at l1nk.zip with minimal operational overhead.
- Hosting cost remains under $5/month using SQLite + Litestream on cheap infrastructure.
- Community adoption measured by GitHub stars, CLI downloads, and external contributions.
- The project serves as a reference for simple, well-documented self-hosted API design.

### Technical Success

- API response time < 100ms for redirects (p95), < 200ms for URL creation (p95).
- Zero data loss with Litestream replication — database recoverable from S3 backup at any time.
- Full test suite passing: 54 unit tests, 61 API tests, 36 integration tests as baseline.
- Optional Redis caching delivers measurable latency reduction on high-traffic URLs.
- Prometheus metrics provide actionable observability for production monitoring.

### Measurable Outcomes

| Metric | Target |
|---|---|
| Redirect latency (p95) | < 100ms |
| Creation latency (p95) | < 200ms |
| Deployment time (new instance) | < 5 minutes |
| Hosting cost | < $5/month |
| Test coverage | All existing tests passing + new features covered |

## User Journeys

### Journey 1: Elena — Developer shortening URLs via API

Elena is a backend developer at a startup. Her team sends weekly newsletters with dozens of links and needs to track click counts. She doesn't want to pay for Bitly or set up a complex database.

She runs `docker run` with the l1nkZip image, configures her domain and Litestream in 3 minutes. Her first `POST /url` with a long URL returns a short link at `https://l1nk.zip/abc123`. She integrates it into her newsletter pipeline with a single HTTP request. A week later, she checks visit counters for each link via the admin endpoint. No accounts, no billing, no complications.

**Requirements revealed:** Simple REST API, fast response, trivial Docker deployment, visit counters, token-protected admin endpoints.

### Journey 2: Marcos — Visitor clicking a short link

Marcos receives a message with a link `https://l1nk.zip/x7k9m`. He doesn't know or care what l1nkZip is — he just wants to see the content. He clicks, and in under 100ms he's redirected to the original destination. If the destination were a known phishing URL, he'd see a warning page instead.

He never sees the infrastructure, never waits, never registers. The link "just works."

**Requirements revealed:** Transparent and ultra-fast redirection, optional phishing protection, zero friction for visitors.

### Journey 3: Sergio — Operator/Admin maintaining the instance

Sergio deploys l1nkZip on a $4/month VPS with SQLite + Litestream replicating to an S3 bucket. He configures environment variables in 5 minutes. He enables Prometheus metrics and builds a Grafana dashboard.

One day the VPS reboots unexpectedly. Litestream restores the database from S3 in seconds. Sergio checks `/health` to confirm everything is fine, queries `/metrics` to verify no anomalies, and moves on with his day. Zero proactive maintenance.

**Requirements revealed:** Data resilience via Litestream, health check endpoint, Prometheus metrics, env var configuration, structured logging, single-container deployment.

### Journey 4: Ana — CLI User managing links from the terminal

Ana is a sysadmin who prefers the terminal for everything. She installs `l1nkzip-cli` via pip, sets `L1NKZIP_API_URL` and `L1NKZIP_TOKEN` in her `.bashrc`. From there she runs `l1nkzip shorten https://very-long-example.com/page` and gets her short link without opening a browser.

She runs `l1nkzip list` to see all her links, `l1nkzip info x7k9m` to check details, and `l1nkzip update-phishtank` to update the phishing database. All without leaving her terminal workflow.

**Requirements revealed:** CLI companion with intuitive commands, env var authentication, CRUD operations on links, PhishTank management from CLI.

### Journey 5: Carlos — Integrator embedding l1nkZip in his product

Carlos builds a marketing campaign management app. He needs an integrated URL shortening service — he doesn't want to depend on an external service like Bitly because his clients require data to stay within their infrastructure.

He deploys l1nkZip as an internal microservice in his Kubernetes cluster. He uses the API to create short links automatically when clients create campaigns. The `/health` endpoint feeds Kubernetes health checks, and `/metrics` feeds his existing observability stack. He configures PostgreSQL as the database backend since his team already operates it. Rate limiting protects against abuse if a campaign goes viral.

His clients never know l1nkZip exists — it's invisible infrastructure that "just works."

**Requirements revealed:** API-first without UI, multi-database backend support, health checks for orchestrators, metrics for observability, rate limiting, Kubernetes deployment, clean REST integration.

### Journey Requirements Summary

| Journey | Key Capabilities |
|---|---|
| Developer (Elena) | REST API, fast deployment, visit counters, admin token |
| Visitor (Marcos) | Redirection < 100ms, phishing protection, zero friction |
| Operator (Sergio) | Litestream resilience, health check, metrics, logging, Docker |
| CLI User (Ana) | CLI companion, link CRUD, PhishTank management, env config |
| Integrator (Carlos) | API-first, multi-DB, K8s-ready, rate limiting, observability |

## API Backend Specific Requirements

### Endpoint Specifications

| Endpoint | Method | Auth | Description | Rate Limit |
|---|---|---|---|---|
| `/url` | POST | None | Create short link from long URL | 10/min |
| `/{link}` | GET | None | Redirect to original URL (HTTP 307) | 120/min |
| `/health` | GET | Token | Database health check | None |
| `/metrics` | GET | None | Prometheus metrics endpoint | None |
| `/urls` | GET | Token | List all shortened URLs | None |

### Authentication Model

- Token-based authentication via `TOKEN` environment variable
- Token required only for admin endpoints (`/health`, `/urls`)
- Public endpoints (URL creation and redirection) require no authentication
- No user accounts, no OAuth, no session management

### Data Schemas

- **Request:** JSON body with `url` field for URL creation
- **Response:** JSON with short link URL
- **Redirect:** HTTP 307 with `Location` header
- **OpenAPI docs:** Auto-generated at `/docs` (Swagger UI)

### Rate Limiting

- Implemented via SlowAPI middleware
- Configurable via environment variables (`RATE_LIMIT_CREATE`, `RATE_LIMIT_REDIRECT`)
- Default: 10 requests/minute for creation, 120/minute for redirects
- Protects against mass URL creation and enumeration attacks

### CLI Client

- Official CLI companion: [l1nkzip-cli](https://github.com/dorogoy/l1nkzip-cli)
- Commands: `shorten`, `info`, `list`, `update-phishtank`
- Configured via `L1NKZIP_API_URL` and `L1NKZIP_TOKEN` environment variables

## Product Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP — already implemented and in production at l1nk.zip. The MVP validates that a simple, self-hosted URL shortener with near-zero hosting cost fills a real need.

**Resource Requirements:** Solo developer (Sergio), part-time maintenance and feature development.

### Phase 1 — MVP (Implemented)

**Core User Journeys Supported:**
- Developer (Elena) — URL creation via API
- Visitor (Marcos) — Transparent redirection
- Operator (Sergio) — Single-container deployment with observability

**Capabilities:**
- URL shortening via `POST /url` and redirection via `GET /{link}`
- SQLite database with Litestream replication
- Token-based admin endpoints (list URLs, health check)
- PhishTank integration (optional)
- Docker deployment with environment-based configuration
- Prometheus metrics (optional)
- Rate limiting via SlowAPI
- Structured logging (JSON/text)

### Phase 2 — Growth (Partially Implemented)

- Redis caching for high-traffic URLs
- Official CLI companion (l1nkzip-cli)
- Multi-database backend support (PostgreSQL, MySQL, Oracle, CockroachDB)
- Structured JSON logging with configurable levels
- Advanced monitoring dashboards and alerting rules

### Phase 3 — Expansion (Future)

- Custom URL slugs (user-chosen short codes)
- Analytics dashboard with visit patterns and geo data
- Web UI for URL management
- Distributed tracing for complex request flows
- Multi-instance horizontal scaling support
- API versioning strategy
- Bulk URL operations endpoint
- Expiration dates for short links
- Webhook notifications on URL events

### Risk Mitigation Strategy

**Technical Risks:** Low. All core technology choices (FastAPI, SQLite/Litestream, Pony ORM) are proven and stable. Multi-DB support via Pony ORM reduces lock-in risk.

**Market Risks:** Low. The project targets a clear niche (self-hosted, privacy-focused, low-cost) with existing community validation via GitHub adoption.

**Resource Risks:** Minimal operational burden due to architecture choices (SQLite, single container). Development pace is sustainable as a solo part-time project.

## Functional Requirements

### URL Management

- FR1: API consumers can submit a long URL and receive a unique short link
- FR2: API consumers can configure a custom encoding alphabet for short link generation
- FR3: API consumers can retrieve the original URL from a short link identifier
- FR4: The system can generate short, unique identifiers using a bit-shuffling algorithm
- FR5: Visitors can be redirected from a short link to the original URL via HTTP redirect

### Visit Tracking

- FR6: The system can count visits to each shortened URL
- FR7: The system can increment visit counts asynchronously to avoid blocking redirects
- FR8: Admins can view visit counts for individual URLs

### Administration

- FR9: Admins can list all shortened URLs in the system via a token-protected endpoint
- FR10: Admins can verify system health including database connectivity
- FR11: Admins can authenticate using a token passed via environment configuration

### Caching

- FR12: The system can cache URL mappings in an optional external cache layer
- FR13: The system can serve redirects from cache without querying the database
- FR14: The system can gracefully degrade when the cache layer is unavailable
- FR15: The system can populate the cache with URL mappings on first access

### Phishing Protection

- FR16: The system can check submitted URLs against the PhishTank database
- FR17: The system can block creation of short links for known phishing URLs
- FR18: The system can block redirection to known phishing URLs
- FR19: Admins can update the PhishTank database via CLI or API

### Observability

- FR20: The system can expose Prometheus-compatible metrics at a dedicated endpoint
- FR21: The system can track and report request counts, latencies, and error rates
- FR22: The system can produce structured logs in JSON or text format
- FR23: The system can log with configurable severity levels (DEBUG, INFO, WARN, ERROR)

### Rate Limiting

- FR24: The system can enforce configurable rate limits on URL creation requests
- FR25: The system can enforce configurable rate limits on URL redirection requests
- FR26: The system can reject requests exceeding rate limits with appropriate HTTP responses

### Database & Storage

- FR27: The system can store URL mappings in SQLite (default)
- FR28: The system can store URL mappings in PostgreSQL, MySQL, Oracle, or CockroachDB
- FR29: The system can replicate SQLite data to S3-compatible storage via Litestream
- FR30: The system can recover SQLite data from S3 backup after data loss

### Configuration & Deployment

- FR31: Operators can configure all settings via environment variables
- FR32: Operators can deploy the system as a single Docker container
- FR33: Operators can deploy the system in Kubernetes with health checks
- FR34: The system can expose auto-generated OpenAPI documentation

### CLI Integration

- FR35: CLI users can shorten URLs from the command line
- FR36: CLI users can retrieve information about existing short links
- FR37: CLI users can list all shortened URLs (admin)
- FR38: CLI users can update the PhishTank database (admin)

## Non-Functional Requirements

### Performance

- NFR1: URL redirection must complete in under 100ms at p95 (cache miss) and under 10ms (cache hit)
- NFR2: URL creation must complete in under 200ms at p95 including encoding and database write
- NFR3: The system must handle at least 100 concurrent requests without degradation
- NFR4: Cache lookup must add no more than 5ms latency to the redirect path
- NFR5: Database operations must not block the async event loop

### Security

- NFR6: Admin endpoints must reject requests without a valid token with HTTP 401/403
- NFR7: All URLs must be validated before storage to prevent injection attacks
- NFR8: Rate limiting must be enforced before request processing to prevent abuse
- NFR9: PhishTank checks must complete within a configurable timeout to avoid blocking
- NFR10: No sensitive data (tokens, database credentials) must appear in logs

### Scalability

- NFR11: The system must operate as a single-instance service (horizontal scaling not required for MVP)
- NFR12: Redis caching must reduce database load proportionally to cache hit rate
- NFR13: The system must handle SQLite databases up to 10GB without performance degradation
- NFR14: Litestream replication must not impact request latency during backup operations

### Integration

- NFR15: The system must support Redis as optional cache with graceful degradation on failure
- NFR16: Prometheus metrics must be exposed in standard exposition format compatible with any scraper
- NFR17: PhishTank integration must support both anonymous and API key modes
- NFR18: Database backend must be swappable via environment configuration without code changes
- NFR19: Structured logs must be consumable by standard log aggregation tools (ELK, Loki, etc.)
