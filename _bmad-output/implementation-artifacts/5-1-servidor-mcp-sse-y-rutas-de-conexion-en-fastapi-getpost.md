# Story 5.1: Servidor MCP SSE y Rutas de Conexión en FastAPI (GET/POST)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an AI agent,
I want to initiate a Model Context Protocol session using SSE (Server-Sent Events) transport,
so that I can discover and call l1nkZip tools remotely.

## Acceptance Criteria

1. **GET Endpoint `/mcp/sse`**:
   - Must be exposed under tags `["mcp"]`.
   - Must establish a Server-Sent Events (SSE) connection stream when called by a client.
   - The SSE event stream must emit an initial `endpoint` event containing the POST endpoint URL with a generated `sessionId` query parameter (e.g., `/mcp/messages?sessionId=<uuid>`).
   - Must handle the bidirectional transport lifecycle asynchronously using `SseServerTransport.connect_sse`.

2. **POST Endpoint `/mcp/messages`**:
   - Must receive incoming JSON-RPC 2.0 messages from MCP clients via POST requests.
   - Requires `sessionId` as a query parameter to route messages to the correct active stream.
   - Must utilize `SseServerTransport.handle_post_message` to process incoming messages.

3. **Graceful Lifespan and Disconnection Handling**:
   - On application shutdown, active SSE transport streams and connections must be closed gracefully, ensuring no resources or event loops are leaked.
   - Abrupt client disconnections (e.g., network timeout, client closed tab/process) must be caught and handled gracefully (e.g. log the drop as `DEBUG` or `INFO` and suppress/cleanup connections instead of throwing unhandled 500 errors).

4. **Robust Middleware & Cross-Cutting Integration**:
   - SSE and messages endpoints must integrate smoothly with existing FastAPI middlewares (rate limiting, Prometheus metrics, structured logging).
   - Ensure errors occurring during transport connections or requests are logged with structured logs using `get_logger(__name__)` and do not crash the service.

## Tasks / Subtasks

- [x] Create core MCP server module (`l1nkzip/mcp.py`) (AC: 1, 2)
  - [x] Initialize `mcp_server` from `mcp.server.Server("l1nkzip-mcp-server")`
  - [x] Initialize `sse_transport` from `mcp.server.sse.SseServerTransport("/mcp/messages")`
- [x] Mount SSE and message routes in `l1nkzip/main.py` (AC: 1, 2, 3)
  - [x] Add `GET /mcp/sse` endpoint calling `sse_transport.connect_sse` and running the server loop
  - [x] Support catching connection cancel / disconnection exceptions gracefully
  - [x] Add `POST /mcp/messages` endpoint calling `sse_transport.handle_post_message`
  - [x] Log connection starts and ends using structured logging
- [x] Implement and verify automated testing (AC: 1, 2, 3, 4)
  - [x] Create `tests/api/test_mcp.py` to test connection handshake and message handling
  - [x] Ensure `make check` (ruff check + format, ty check) passes without errors
  - [x] Ensure `make test` succeeds and database connection/transports behave as expected

### Review Findings

- [x] [Review][Patch] F1: No graceful shutdown/lifespan handler for active SSE connections [main.py, mcp.py]
- [x] [Review][Dismiss] F2: No graceful degradation if `mcp` package is unavailable — dismissed, MCP is a required dependency
- [x] [Review][Patch] F3: Missing return type annotations on endpoint functions [main.py:462, main.py:484]
- [x] [Review][Patch] F4: `request._send` uses private Starlette attribute — add comment documenting necessity [main.py:467, main.py:489]
- [x] [Review][Patch] F5: `handle_sse` silently swallows non-CancelledError exceptions — should re-raise or respond for pre-upgrade errors [main.py:476-480]
- [x] [Review][Patch] F6: No module-level logger in `mcp.py` — project context requires `logger = get_logger(__name__)` [mcp.py]
- [x] [Review][Patch] F7: Test `receive()` helper returns request body on every call (busy-loop) — should block after first call [test_mcp.py:52-53]
- [x] [Review][Defer] F8: No rate limiting on MCP endpoints — deferred, scoped to Story 5.3 [main.py:461-497]
- [x] [Review][Defer] F9: Test assertions accept overly wide status code ranges — deferred, tighten once MCP library behavior is stable [test_mcp.py:80, test_mcp.py:87]
- [x] [Review][Defer] F10: `handle_messages` re-raises as generic 500 for all exception types — deferred, better error differentiation in future iteration [main.py:491-496]

## Dev Notes

### Key Architecture Patterns
- **Monolithic Single Process (AD1)**: The MCP server must run within the existing FastAPI/Uvicorn process. Do not spawn separate subprocesses or listen on separate ports.
- **Graceful Optional Components (AD4 / ARCH-5)**: Ensure that the MCP integration behaves gracefully. If clients disconnect abruptly, catch connection-closed errors, log them as `WARNING` or `DEBUG`, and clean up resources without raising unhandled 500 errors or crashing.
- **Structured Logging (AD7)**: Use `logger = get_logger(__name__)` to log SSE connections, session creation/destruction, and message processing with `extra` metadata.
- **Settings Access**: Access any MCP settings (such as checking if MCP is enabled or securing admin tools later) using the injected `Settings` singleton via `l1nkzip.config.settings`.

### Implementation Steps
1. In `l1nkzip/mcp.py`:
   ```python
   from mcp.server import Server
   from mcp.server.sse import SseServerTransport

   # Initialize server
   mcp_server = Server("l1nkzip-mcp-server")
   
   # Initialize transport pointing to the POST endpoint
   sse_transport = SseServerTransport("/mcp/messages")
   ```
2. In `l1nkzip/main.py`, import `mcp_server` and `sse_transport`, and register the routes:
   ```python
   import asyncio
   from l1nkzip.mcp import mcp_server, sse_transport

   @app.get("/mcp/sse", tags=["mcp"])
   async def handle_sse(request: Request):
       try:
           async with sse_transport.connect_sse(
               request.scope, request.receive, request._send
           ) as streams:
               await mcp_server.run(
                   streams[0],
                   streams[1],
                   mcp_server.create_initialization_options(),
               )
       except asyncio.CancelledError:
           logger.info("MCP SSE client connection cancelled/disconnected gracefully")
       except Exception as e:
           logger.warning(
               "Unexpected disconnect in MCP SSE connection",
               extra={"error": str(e)}
           )

   @app.post("/mcp/messages", tags=["mcp"])
   async def handle_messages(request: Request):
       try:
           await sse_transport.handle_post_message(
               request.scope, request.receive, request._send
           )
       except Exception as e:
           logger.error(
               "Error handling MCP message POST request",
               extra={"error": str(e)}
           )
           raise HTTPException(status_code=500, detail="Internal server error in message route")
   ```

### Testing Standards Summary
- Write integration tests in `tests/api/test_mcp.py` to test GET `/mcp/sse` and POST `/mcp/messages` routes.
- You can mock or construct standard Starlette scopes to simulate requests or use `async_client` to GET `/mcp/sse` and check if the headers returned are `text/event-stream` and include initial events.
- Run tests via `make test-api` or `uv run pytest tests/api/test_mcp.py`.

### Manual Verification
To manually verify that the SSE endpoint functions correctly and returns the session location, run a short python script or use a curl command:
```bash
# Verify headers and SSE stream location
curl -N -i http://localhost:8000/mcp/sse
```
Expected output includes:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```
And the SSE body should contain:
```sse
event: endpoint
data: /mcp/messages?sessionId=<uuid>
```

### Project Structure Notes
- New file: `l1nkzip/mcp.py` containing MCP server setup.
- Modified file: `l1nkzip/main.py` importing and using the MCP routes.
- Modified file: `pyproject.toml` dependencies updated to include `mcp>=1.1.3`, `sse-starlette>=3.4.4`, and `httpx-sse>=0.4.3` (already done).

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#AD8: Model Context Protocol (MCP) Server via SSE](file:///_bmad-output/planning-artifacts/architecture.md#L164-L175)
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1: Servidor MCP SSE y Rutas de Conexión en FastAPI (GET/POST)](file:///_bmad-output/planning-artifacts/epics.md#L252-L266)

## Dev Agent Record

### Agent Model Used

Gemini 3.5 Flash (Medium)

### Debug Log References

- SSE stream testing with TestClient blocks indefinitely due to long-lived connection; resolved by using raw ASGI interface with asyncio task cancellation
- MCP library uses `session_id` (underscore) as query parameter, not `sessionId` (camelCase)

### Completion Notes List

- Created `l1nkzip/mcp.py` with `mcp_server` (Server) and `sse_transport` (SseServerTransport) singletons
- Added `GET /mcp/sse` endpoint with graceful CancelledError and exception handling, structured logging
- Added `POST /mcp/messages` endpoint with error handling and structured logging
- Added "mcp" tag to OpenAPI tags in `l1nkzip/config.py`
- Added "l1nkzip.mcp" to structured logging setup in `l1nkzip/logging.py`
- Created 13 integration tests in `tests/api/test_mcp.py` covering: SSE endpoint method validation, POST message endpoint validation, OpenAPI schema integration, module import verification, and SSE stream handshake (headers, endpoint event, session_id format, cache-control, keep-alive)
- All 13 MCP tests pass; no regressions in existing test suite (9 pre-existing failures unrelated to this story)
- `make check` passes: ruff check, ruff format, ty check all clean

### File List
- [NEW] `l1nkzip/mcp.py`
- [MODIFY] `l1nkzip/main.py`
- [MODIFY] `l1nkzip/config.py`
- [MODIFY] `l1nkzip/logging.py`
- [NEW] `tests/api/test_mcp.py`

### Change Log
- 2026-05-24: Implemented MCP SSE server endpoints (GET /mcp/sse, POST /mcp/messages) with graceful disconnection handling and 13 integration tests
