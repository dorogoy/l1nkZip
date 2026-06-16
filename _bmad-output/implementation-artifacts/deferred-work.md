# Deferred Work

## Deferred from: code review of story 5-1-servidor-mcp-sse (2026-05-24)

- F8: No rate limiting on MCP endpoints — SSE holds persistent connections and messages accepts arbitrary POSTs, neither has `@limiter.limit()`. Likely scoped to Story 5.3 (admin/security).
- F9: Test assertions accept overly wide status code ranges — `assert response.status_code in [400, 500, 422]` accepts 500 as valid. Should be tightened once MCP library behavior is stable.
- F10: `handle_messages` re-raises as generic 500 for all exception types — Missing session (400/404), malformed JSON (422), and actual crashes all produce 500. Better error differentiation once MCP exception hierarchy is understood.

## Deferred from: code review of 5-2-exposicion-de-herramientas-publicas-de-gestion-shorten-y-get_url (2026-06-16)

- MCP handlers import and catch `fastapi.HTTPException` from `l1nkzip.main` validators (`l1nkzip/mcp.py:64, 101`) — pre-existing structural coupling; refactoring `validate_url`/`validate_short_link` to return a neutral result would touch existing HTTP endpoints.
- Unknown tool raises bare `ValueError` (`l1nkzip/mcp.py:60`) — deferred until the MCP SDK error contract is verified.
