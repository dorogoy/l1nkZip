# MCP Integration

L1nkZip ships with an embedded [Model Context Protocol (MCP)][MCP] server, so AI agents and LLM-powered clients can discover and invoke its URL management capabilities directly. The server uses the [Server-Sent Events (SSE)][SSE] transport and speaks [JSON-RPC 2.0][JSON-RPC], exposing shortening, retrieval, and administrative tools through a single, discoverable interface.

MCP is always enabled. There is no environment variable to toggle it — once L1nkZip is running, the endpoints below are available.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp/sse` | `GET` | Opens a persistent SSE stream and returns the message endpoint URL |
| `/mcp/messages` | `POST` | Receives JSON-RPC 2.0 messages from the client |

### Establishing a session

A session begins with a `GET` to `/mcp/sse`. The server responds with an `event-stream` and emits an initial `endpoint` event containing the POST URL (including a `session_id` query parameter) that the client must use for all subsequent messages:

```bash
curl -N -i https://l1nk.zip/mcp/sse
```

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

The SSE body contains:

```sse
event: endpoint
data: /mcp/messages?session_id=<id>
```

After receiving the endpoint, the client initializes the protocol and can list/call tools by POSTing JSON-RPC 2.0 messages to `/mcp/messages?session_id=<id>`. The connection stays open until the client disconnects; abrupt disconnections are handled gracefully by the server.

## Available tools

L1nkZip exposes three MCP tools. Two are public, one requires administrative authorization.

### `shorten_url`

Shorten a long URL and return the short link. PhishTank protection (if enabled) applies exactly as it does on the REST API.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | yes | The long URL to shorten (must start with `http://` or `https://`) |

Returns the fully-qualified short URL (e.g. `https://l1nk.zip/abc123`).

### `get_original_url`

Retrieve the destination URL for a previously shortened link. Serves from cache when available and records a visit, just like a browser redirect.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `link` | string | yes | The short link identifier (4–20 chars from `[a-zA-Z0-9_-]`) |

Returns the original destination URL.

### `list_urls` (admin)

List shortened URLs with their statistics. **Requires the admin token** configured via the `TOKEN` environment variable.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | yes | Admin authorization token |
| `limit` | integer | no | Maximum number of URLs to return. Default: `100`. Range: `1`–`1000` |

Returns a JSON array of link records (identifier, destination URL, visit count). Calls with a missing or invalid token are rejected.

## Connecting from an MCP client

Any MCP-compatible client can connect to the SSE endpoint. Using the reference [MCP Python SDK][MCP SDK] as an example:

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("https://l1nk.zip/mcp/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        tools = await session.list_tools()

        result = await session.call_tool(
            "shorten_url",
            arguments={"url": "https://www.google.com"},
        )
        print(result.content[0].text)
```

For administrative operations, pass the token as a tool argument:

```python
result = await session.call_tool(
    "list_urls",
    arguments={"token": "YOUR_ADMIN_TOKEN", "limit": 50},
)
```

## Security notes

- Public tools (`shorten_url`, `get_original_url`) inherit the same protections as the REST API: URL validation, PhishTank checks, and rate limiting semantics.
- The `list_urls` tool validates the admin token using the same mechanism as the REST admin endpoints (length and character whitelist, then comparison against `TOKEN`).
- Never expose or log your admin token. See the [Self-hosting](/l1nkZip/selfhosting) guide for token configuration.

[MCP]: https://modelcontextprotocol.io
[SSE]: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
[JSON-RPC]: https://www.jsonrpc.org
[MCP SDK]: https://github.com/modelcontextprotocol/python-sdk
