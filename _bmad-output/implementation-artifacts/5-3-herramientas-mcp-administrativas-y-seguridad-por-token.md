# Story 5.3: Herramientas MCP Administrativas y Seguridad por Token

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an authorized AI agent,
I want administrative capabilities (like listing all shortened URLs) exposed as secure MCP tools protected by the standard token authentication,
so that I can manage the link index.

## Acceptance Criteria

1. **Admin Tool Discovery (`list_urls` in `list_tools`)**:
   - The MCP server must additionally expose `list_urls` in the tools list alongside the existing `shorten_url` and `get_original_url`.
   - The `list_urls` schema must declare:
     - `token` (string, **required**) — the admin secret token.
     - `limit` (integer, optional, default 100) — maximum number of URLs to return.
   - The tool description must clearly state that admin authorization is required.

2. **Token Authentication Guard (`list_urls`)**:
   - When `list_urls` is called **without** a `token` argument, with an invalid-format token, or with a token that does not match `settings.token`, the tool call MUST return an MCP error result (raised `ValueError` surfaced by the SDK) stating the request is unauthorized.
   - Token validation MUST reuse the existing `validate_admin_token` helper from `l1nkzip.main` (format check: length >= 16 and character whitelist) followed by the equality check against `settings.token`, mirroring the `/list/{token}` and `/phishtank/update/{token}` endpoints exactly.
   - The token value MUST NEVER appear in logs, error messages, or returned content (NFR10).

3. **Admin Tool Execution (`list_urls`)**:
   - When `list_urls` is called with a valid token, it MUST return the complete list of shortened URLs with their stats (link, full_link, url, visits).
   - The `limit` argument MUST be validated to the range 1–1000 (reject out-of-range with a clear error, matching `/list/{token}`).
   - Database access MUST go through the existing `get_visits(limit)` function in `l1nkzip.models` (reuse — do NOT reinvent the query), executed via `run_in_executor` to avoid blocking the event loop (Pony ORM guardrail).
   - The returned `TextContent` MUST serialize the list of URLs as a JSON string (each item containing `link`, `full_link`, `url`, `visits`).

4. **Async & DB Isolation (Pony ORM Guardrail)**:
   - The synchronous `get_visits(limit)` call from the async MCP handler MUST run in a thread pool using `asyncio.get_running_loop().run_in_executor(None, get_visits, limit)`.

5. **Circular Dependency Prevention**:
   - `validate_admin_token` and `get_visits` (and any other `l1nkzip.main` / `l1nkzip.models` helpers not already imported at module level) MUST be imported **locally** inside the tool handler function to avoid circular imports during app startup. `settings`, `cache`, and `metrics` remain module-level imports (established in Story 5.2).

6. **Graceful Error Handling**:
   - Database errors during `get_visits` MUST be caught, logged at ERROR level with structured context (never including the token), and surfaced to the MCP client as a generic `ValueError("Failed to retrieve URL list")` — never leak internal details.
   - Non-dict `arguments`, non-string `token`, and non-integer `limit` MUST be rejected with clear `ValueError` messages (apply the hardening patterns established in Story 5.2's review).

## Tasks / Subtasks

- [x] Register `list_urls` admin tool in `l1nkzip/mcp.py` (AC: 1)
  - [x] Add `list_urls` `types.Tool` entry inside the existing `handle_list_tools` decorator handler (keep `shorten_url` and `get_original_url` intact)
  - [x] Define `inputSchema` with required `token` (string) and optional `limit` (integer, default 100)
- [x] Implement `list_urls` execution in `l1nkzip/mcp.py` (AC: 2, 3, 4, 5, 6)
  - [x] Add `list_urls` branch to the existing `handle_call_tool` dispatcher routing to a new `_handle_list_urls(arguments)` helper
  - [x] Inside `_handle_list_urls`: locally import `validate_admin_token` from `l1nkzip.main` and `get_visits` from `l1nkzip.models`
  - [x] Validate `arguments` is a dict; extract and type-check `token` (string) and `limit` (int, default 100)
  - [x] Run `validate_admin_token(token)` inside try/except — convert `HTTPException` and generic `Exception` to `ValueError("Unauthorized")` (never leak detail)
  - [x] Compare `token != settings.token` → raise `ValueError("Unauthorized")`
  - [x] Validate `limit` range 1–1000 → raise `ValueError` on violation
  - [x] Call `get_visits(limit)` via `loop.run_in_executor(None, get_visits, limit)`
  - [x] Serialize the returned `List[LinkInfo]` to a JSON string and return as `types.TextContent`
  - [x] Catch DB errors → log ERROR with structured context (NO token in `extra`), raise generic `ValueError`
- [x] Implement automated testing in `tests/api/test_mcp_tools.py` (AC: 1, 2, 3, 4, 5, 6)
  - [x] Add `list_urls` assertions to the existing `TestListTools` class (schema with `token` required + `limit` optional integer)
  - [x] Add a `TestListUrlsTool` class covering: valid token returns list, missing token rejected, wrong token rejected, malformed token rejected, limit range validation, non-dict arguments, non-string token, non-integer limit, empty result serialization, run_in_executor usage, token never logged
  - [x] Follow the clean-test rules in Dev Notes (no comments/docstrings, no `sys.modules` mutation)
  - [x] Ensure `make check` (ruff check + ruff format + ty) is clean
  - [x] Ensure `make test` passes with no regressions

## Dev Notes

### CRITICAL: Reuse Existing Auth — Do NOT Reinvent

The admin token validation logic **already exists** and MUST be reused verbatim. There are two layers, exactly as `/list/{token}` (main.py:279-284) and `/phishtank/update/{token}` (main.py:259-264) do:

```python
from l1nkzip.main import validate_admin_token

validate_admin_token(token)
if token != settings.token:
    raise ValueError("Unauthorized")
```

**`validate_admin_token` (main.py:103-115) does FORMAT validation only:**
- Rejects `None`/empty or length < 16 → `HTTPException(401, "Invalid admin token")`
- Rejects characters outside `^[a-zA-Z0-9!@#$%^&*()_+-=]+$` → `HTTPException(401, "Invalid admin token format")`
- Returns the token string on success

**The equality check `token != settings.token` is the ACTUAL authorization** — `validate_admin_token` only checks format. Both steps are required. `settings.token` defaults to `"__change_me__"` (config.py:18).

### Token Transport in MCP Context (AD8 Decision)

AD8 (architecture.md:174) states admin tools validate the token "passed via query parameter, header, or payload". MCP tool calls arrive as JSON-RPC `tools/call` messages whose `arguments` dict is the only application-level data surface (the SDK's `call_tool` handler signature is `(name: str, arguments: dict)` with no HTTP request context). Therefore, for MCP, the **payload** option is the only viable one: `token` is a required argument of the `list_urls` tool. This maintains parity with the existing admin endpoints' security semantics while adapting to the MCP transport.

### Pony ORM Guardrail (MANDATORY)

`get_visits` (models.py:97-106) is `@db_session` decorated and **synchronous**. Calling it directly from the async MCP handler will block the FastAPI event loop and break the `< 100ms p95` performance NFRs. Wrap it:

```python
loop = asyncio.get_running_loop()
link_list = await loop.run_in_executor(None, get_visits, limit)
```

This pattern is already established in `_handle_shorten_url` (mcp.py:100-102) and `_handle_get_original_url` (mcp.py:171).

### Existing Module-Level Imports (Established 5.2)

`l1nkzip/mcp.py` already imports these at module level (do NOT re-add or move):
- `asyncio`, `mcp.server.Server`, `mcp.server.sse.SseServerTransport`, `mcp.types as types`
- `l1nkzip.cache.cache`, `l1nkzip.config.settings`, `l1nkzip.logging.get_logger`, `l1nkzip.metrics.metrics`
- `logger = get_logger(__name__)`

The circular-import rule (from 5.2): `l1nkzip.main` helpers (`validate_url`, `validate_short_link`, `validate_admin_token`, `retry_phishtank_check`, `insert_link`, `set_visit`) must be imported **locally** inside each handler. `l1nkzip.models.get_visits` should also be imported locally for consistency (the existing handlers locally import `l1nkzip.models.increment_visit_async`).

### Dispatcher Extension Point

Extend the existing `handle_call_tool` (mcp.py:54-60) — add one branch, keep the rest intact:

```python
@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "shorten_url":
        return await _handle_shorten_url(arguments)
    if name == "get_original_url":
        return await _handle_get_original_url(arguments)
    if name == "list_urls":
        return await _handle_list_urls(arguments)
    raise ValueError(f"Unknown tool: {name}")
```

### Token Logging Prohibition (NFR10)

- NEVER put `token` in `logger.{level}(..., extra={...})` payloads.
- The existing `get_list` endpoint at main.py:307 violates this with `"token": token` in the extra dict — do NOT copy that pattern. This story must NOT propagate the token into logs.
- Error messages returned to the MCP client must say only `"Unauthorized"` — never echo the supplied token value.

### Return Serialization

`get_visits` returns `List[LinkInfo]` where `LinkInfo` (models.py:20-24) is a Pydantic model with `link: str`, `full_link: HttpUrl`, `url: HttpUrl`, `visits: int`. Serialize with `model_dump(mode="json")`:

```python
import json
data = [item.model_dump(mode="json") for item in link_list]
return [types.TextContent(type="text", text=json.dumps(data, default=str))]
```

`full_link` is a computed property on the `Link` entity (models.py:47-50) that builds from `settings.api_domain`. Note: `Link.full_link` uses `pathlib.Path(api_domain, link)` which collapses `//` in `https://` — this is a known quirk; for the MCP `list_urls` tool we return the `LinkInfo.full_link` value as-is from `get_visits` (do not reconstruct). The Story 5.2 review flagged that `shorten_url` builds the short URL via f-string to avoid this — that fix is local to `_handle_shorten_url` and does not apply here because `list_urls` returns multiple pre-built entries.

### Limit Validation (Mirror /list/{token})

main.py:287-288 validates `limit` to the range 1–1000. `list_urls` MUST enforce the same:

```python
if limit < 1 or limit > 1000:
    raise ValueError("Limit must be between 1 and 1000")
```

`get_visits` itself does not enforce the range (models.py:97), so the handler MUST validate before calling it.

### Hardened Argument Validation (From 5.2 Review)

Apply the exact patterns accepted in the 5.2 review to avoid reopening the same findings:
- `if not isinstance(arguments, dict): raise ValueError("Invalid arguments: expected object")`
- `token = arguments.get("token")` then `if not isinstance(token, str): raise ValueError(...)`
- `limit = arguments.get("limit", 100)` then coerce/validate: reject non-int truthy values, do NOT silently `str()`-coerce.

### Testing Standards (MANDATORY Clean-Test Rules)

**Three action items were left open at the end of Story 5.2's review — this story MUST resolve them for the new tests added (do not need to retrofit 5.2's existing tests, but new `list_urls` tests must follow the clean pattern):**

1. **No SSE/JSON-RPC bypass by default**: The 5.2 tests invoke handler callables directly because the MCP decorator returns the original callable. Prefer driving the handlers through the same direct-callable style for unit-level assertions (it is the established pattern in `test_mcp_tools.py`), BUT add at least one integration-style test that exercises the full SSE session → `tools/list` → `tools/call` flow for `list_urls` to prove the token guard works end-to-end. Use the patterns from `tests/api/test_mcp.py` (Story 5.1) as the reference for the SSE/JSON-RPC style.
2. **No Comments Pattern**: do NOT add docstrings or `# comment` lines to the test file. Module-level and class-level docstrings are already present in `test_mcp_tools.py` — do not add more; follow the existing file's convention.
3. **No `sys.modules` mutation**: the `_get_handlers()` helper in test_mcp_tools.py:18-22 currently deletes `sys.modules` entries to reset singletons. This causes cross-test pollution. For new `list_urls` tests, prefer the project's `conftest.py` fixtures (which already clear `l1nkzip.config`, `l1nkzip.models`, `l1nkzip.main` per test) and `patch("l1nkzip.config.settings", ...)` instead of manual `sys.modules` deletion. If you must reuse `_get_handlers()`, document inline why — but the cleaner path is the conftest fixture.

**Test coverage required for `list_urls`:**
- `TestListTools`: assert `list_urls` appears in tools list; assert schema has `token` (string, required) and `limit` (integer, optional).
- `TestListUrlsTool`:
  - valid token + default limit returns JSON list with expected fields
  - valid token + custom limit respected
  - missing `token` → `ValueError` / MCP error
  - wrong token (`token != settings.token`) → unauthorized
  - malformed token (length < 16 or bad chars) → unauthorized (via `validate_admin_token`)
  - `limit` below 1 / above 1000 → rejected
  - non-dict `arguments` → rejected
  - non-string `token` → rejected
  - non-integer `limit` → rejected (no silent coercion)
  - empty database → returns `"[]"` JSON
  - DB error from `get_visits` → caught, generic error raised, no internal details leaked
  - **assert the token value is absent from captured log records** (use `caplog`)

### Settings Fixture Pattern

The existing `_get_handlers()` (test_mcp_tools.py:18-36) constructs a `Settings()` instance with `db_type="inmemory"`, disables Redis/PhishTank, enables metrics, and raises rate limits. Reuse it — set `test_settings.token = "a-valid-test-token-1234"` (length >= 16, whitelisted chars) so auth can be exercised.

### Code Quality Rules (From project-context.md)

- **Line length**: 120 characters
- **Ruff rules**: F, E, W, I, N, B
- **No comments** in code unless explicitly requested
- **Type hints** on all function signatures
- **Lint command**: `make check` (runs `ruff check`, `ruff format --check`, `ty check`)
- **Format command**: `make fmt` if needed
- **Test command**: `make test` (runs check + all test suites)

### Project Structure Notes

- **Modified file**: `l1nkzip/mcp.py` — extend `handle_list_tools`, `handle_call_tool`, add `_handle_list_urls`.
- **Modified file**: `tests/api/test_mcp_tools.py` — extend `TestListTools`, add `TestListUrlsTool`.
- No new modules. No changes to `main.py` (routes already wired in 5.1), `config.py`, `models.py`, or `pyproject.toml`.
- Alignment with the unified structure: all MCP-related code lives in `l1nkzip/mcp.py`; all MCP tool tests live in `tests/api/test_mcp_tools.py`.

### References

- [Source: l1nkzip/main.py#validate_admin_token](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/main.py#L103-L115) — token format validation to reuse
- [Source: l1nkzip/main.py#get_list](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/main.py#L279-L309) — reference admin list endpoint (auth + limit pattern)
- [Source: l1nkzip/models.py#get_visits](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/models.py#L97-L106) — DB function to reuse
- [Source: l1nkzip/models.py#LinkInfo](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/models.py#L20-L24) — response model
- [Source: l1nkzip/mcp.py#handle_call_tool](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/mcp.py#L54-L60) — dispatcher to extend
- [Source: l1nkzip/mcp.py#_handle_shorten_url](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/mcp.py#L63-L121) — reference handler pattern (run_in_executor, local imports, error handling)
- [Source: l1nkzip/config.py#Settings.token](file:///home/sergio/Proyectos/dorogoy/l1nkZip/l1nkzip/config.py#L18) — token default
- [Source: _bmad-output/planning-artifacts/architecture.md#AD8](file:///home/sergio/Proyectos/dorogoy/l1nkZip/_bmad-output/planning-artifacts/architecture.md#L164-L174) — MCP + admin token decision
- [Source: _bmad-output/planning-artifacts/architecture.md#ARCH-9](file:///home/sergio/Proyectos/dorogoy/l1nkZip/_bmad-output/planning-artifacts/epics.md#L99) — unified token auth rule
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3](file:///home/sergio/Proyectos/dorogoy/l1nkZip/_bmad-output/planning-artifacts/epics.md#L281-L293) — story definition
- [Source: _bmad-output/project-context.md#Pony ORM Rules](file:///home/sergio/Proyectos/dorogoy/l1nkZip/_bmad-output/project-context.md#L51-L60) — async guardrail
- [Source: _bmad-output/implementation-artifacts/5-2-*.md#Review Findings](file:///home/sergio/Proyectos/dorogoy/l1nkZip/_bmad-output/implementation-artifacts/5-2-exposicion-de-herramientas-publicas-de-gestion-shorten-y-get_url.md#L142-L184) — patterns and action items to honor

## Dev Agent Record

### Agent Model Used

glm-5.2 (zai-coding-plan/glm-5.2)

### Debug Log References

- `make check`: ruff check + ruff format --check + ty — all passed clean.
- `make test`: unit 113 passed / 6 skipped; api 113 passed / 6 skipped; integration 36 passed / 2 skipped; 0 failures, 0 regressions.
- MCP SDK behavior verified: a `ValueError` raised inside a `call_tool` handler is surfaced by the SDK as a `CallToolResult` with `isError=true` (content carries the message). Confirmed via the SSE integration test capturing the full `{"jsonrpc":"2.0","id":2,"result":{"content":[...],"isError":true}}` response.

### Completion Notes List

- Registered the `list_urls` admin tool in `handle_list_tools` with a JSON schema declaring `token` (string, required) and `limit` (integer, optional, default 100); description states admin authorization is required (AC1).
- Added the `list_urls` dispatch branch to `handle_call_tool`, routing to a new `_handle_list_urls(arguments)` helper (AC1).
- `_handle_list_urls` reuses `validate_admin_token` (format check) and the `token != settings.token` equality check exactly as `/list/{token}` and `/phishtank/update/{token}` do (AC2). Both `HTTPException` and generic `Exception` from `validate_admin_token` are converted to `ValueError("Unauthorized")` with `from None` to suppress any detail leak.
- Argument hardening (per 5.2 review patterns): non-dict `arguments`, non-string `token`, and non-integer `limit` (including booleans — guarded via `isinstance(limit, bool)` before the `int` check) are all rejected with clear `ValueError` messages (AC6).
- `limit` range validated to 1–1000 before calling `get_visits`, mirroring `/list/{token}` (AC3).
- `get_visits` runs through `asyncio.get_running_loop().run_in_executor(None, get_visits, limit)` to honor the Pony ORM async guardrail (AC4). Local imports of `validate_admin_token` and `get_visits` inside the handler avoid circular imports (AC5).
- Return serialization uses `LinkInfo.model_dump(mode="json")` + `json.dumps(..., default=str)` producing `TextContent` with `link`, `full_link`, `url`, `visits` per item (AC3).
- DB errors are caught, logged at ERROR with structured context (`error`, `limit`) — never the token — and re-raised as a generic `ValueError("Failed to retrieve URL list")` (AC6, NFR10). The token value never enters `logger` extras or returned messages.
- Tests: extended `TestListTools` with `list_urls` presence + schema assertions. Added `TestListUrlsTool` (17 tests) covering valid token + default/custom limit, missing/wrong/short/bad-char token, limit range, non-dict args, non-string token, non-int/bool limit, empty result `[]`, DB error → generic message, no internal detail leak, token-never-logged (caplog), and `run_in_executor` usage.
- Clean-test rules honored for the new tests: the `list_urls_handlers` fixture uses `conftest.test_settings` + `patch("l1nkzip.mcp.settings", ...)` with no `sys.modules` mutation; no comments/docstrings added to the new tests.
- Added the SSE/JSON-RPC integration test (`TestListUrlsSSEIntegration`) that drives a full SSE session (initialize → initialized → tools/call) and asserts the missing-token call returns an `isError:true` result end-to-end, resolving the 5.2 action item for `list_urls`.

### File List

- Modified: `l1nkzip/mcp.py` — added `list_urls` tool definition, dispatch branch, and `_handle_list_urls` handler.
- Modified: `tests/api/test_mcp_tools.py` — extended `TestListTools`, added `list_urls_handlers` fixture, `_get_app`, `_drive_sse_messages` helper, `TestListUrlsTool`, and `TestListUrlsSSEIntegration`.

### Review Findings

- [x] [Review][Patch] AC2: missing token returns "Invalid token: must be a string" instead of "Unauthorized" [l1nkzip/mcp.py:263-264]
- [x] [Review][Patch] `test_bad_chars_token_rejected` uses whitelisted characters — bad-char rejection path untested [tests/api/test_mcp_tools.py:352]
- [x] [Review][Patch] `model_dump()` serialization outside try/except — raw Pydantic error leaks to MCP client on failure [l1nkzip/mcp.py:289]
- [x] [Review][Patch] `asyncio.get_event_loop()` deprecated in `_drive_sse_messages` — use `get_running_loop()` [tests/api/test_mcp_tools.py:467-468,511]
- [x] [Review][Defer] Timing side-channel on `token != settings.token` — pre-existing pattern across all admin endpoints, requires transversal fix (hmac.compare_digest)
- [x] [Review][Defer] NULL `link` column in DB causes masked ValidationError in `get_visits` — pre-existing model issue (Link.link is Optional)
- [x] [Review][Defer] Default token `__change_me__` (14 chars) never passes `validate_admin_token` length check — pre-existing config issue

## Change Log

- 2026-06-16: Implemented Story 5.3 — `list_urls` admin MCP tool with token-guard authentication reusing `validate_admin_token` + `settings.token` equality, `limit` (1–1000) validation, Pony ORM `run_in_executor` wrapping of `get_visits`, JSON-serialized `TextContent` response, and hardened argument/error handling. Added 19 new tests (unit + SSE integration) following clean-test rules; all quality gates and regression suites pass.
