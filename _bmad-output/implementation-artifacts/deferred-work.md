# Deferred Work

## Deferred from: code review of story 5-1-servidor-mcp-sse (2026-05-24)

- F8: No rate limiting on MCP endpoints — SSE holds persistent connections and messages accepts arbitrary POSTs, neither has `@limiter.limit()`. Likely scoped to Story 5.3 (admin/security).
- F9: Test assertions accept overly wide status code ranges — `assert response.status_code in [400, 500, 422]` accepts 500 as valid. Should be tightened once MCP library behavior is stable.
- F10: `handle_messages` re-raises as generic 500 for all exception types — Missing session (400/404), malformed JSON (422), and actual crashes all produce 500. Better error differentiation once MCP exception hierarchy is understood.

## Deferred from: code review of 5-2-exposicion-de-herramientas-publicas-de-gestion-shorten-y-get_url (2026-06-16)

- MCP handlers import and catch `fastapi.HTTPException` from `l1nkzip.main` validators (`l1nkzip/mcp.py:64, 101`) — pre-existing structural coupling; refactoring `validate_url`/`validate_short_link` to return a neutral result would touch existing HTTP endpoints.
- Unknown tool raises bare `ValueError` (`l1nkzip/mcp.py:60`) — deferred until the MCP SDK error contract is verified.

## Deferred from: code review of story 5-3-herramientas-mcp-administrativas-y-seguridad-por-token (2026-06-16)

- Timing side-channel on `token != settings.token` (`l1nkzip/mcp.py:273`) — pre-existing pattern in all admin endpoints (`main.py:263,283`); requires transversal fix using `hmac.compare_digest`.
- NULL `link` column in DB causes masked ValidationError in `get_visits` (`l1nkzip/models.py:42,100`) — `Link.link` is `Optional(str)` but `LinkInfo.link` is `str`; pre-existing model issue.
- Default token `__change_me__` (14 chars) never passes `validate_admin_token` length check (`l1nkzip/config.py:18`, `l1nkzip/main.py:105`) — pre-existing config issue; no startup warning emitted.
