import asyncio
from contextlib import contextmanager
import re
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from l1nkzip.config import Settings


@contextmanager
def _get_app():
    test_settings = Settings()
    test_settings.db_type = "inmemory"
    test_settings.redis_server = None
    test_settings.metrics_enabled = True
    test_settings.phishtank = None
    test_settings.rate_limit_create = "1000/minute"
    test_settings.rate_limit_redirect = "2000/minute"

    # Reload main so it picks up the patched settings at import time.
    sys.modules.pop("l1nkzip.main", None)

    with patch("l1nkzip.config.settings", test_settings):
        from l1nkzip.main import app

        yield app


@pytest.fixture
def mcp_test_client():
    with _get_app() as app:
        yield TestClient(app)


async def _collect_sse_messages(app, path: str = "/mcp/sse", timeout: float = 2.0):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "server": ("testserver", 80),
        "asgi": {"version": "3.0"},
    }
    received = []

    called = False

    async def receive():
        nonlocal called
        if not called:
            called = True
            return {"type": "http.request", "body": b""}
        await asyncio.Event().wait()

    async def send(message):
        received.append(message)

    task = asyncio.create_task(app(scope, receive, send))
    await asyncio.sleep(timeout)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass
    return received


class TestMCPSSEEndpoint:
    def test_sse_endpoint_post_method_not_allowed(self, mcp_test_client):
        response = mcp_test_client.post("/mcp/sse")
        assert response.status_code == 405


class TestMCPMessagesEndpoint:
    def test_messages_endpoint_post_without_session(self, mcp_test_client):
        response = mcp_test_client.post(
            "/mcp/messages",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
        )
        assert response.status_code in [400, 500, 422]

    def test_messages_endpoint_post_with_invalid_session(self, mcp_test_client):
        response = mcp_test_client.post(
            "/mcp/messages?session_id=00000000000000000000000000000000",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
        )
        assert response.status_code in [400, 500, 404]

    def test_messages_endpoint_get_not_allowed(self, mcp_test_client):
        response = mcp_test_client.get("/mcp/messages")
        assert response.status_code == 405


class TestMCPOpenAPIIntegration:
    def test_mcp_endpoints_in_openapi(self, mcp_test_client):
        response = mcp_test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/mcp/sse" in paths
        assert "/mcp/messages" in paths

    def test_mcp_sse_tagged_correctly(self, mcp_test_client):
        response = mcp_test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        sse_path = schema["paths"].get("/mcp/sse", {})
        get_op = sse_path.get("get", {})
        assert "mcp" in get_op.get("tags", [])

    def test_mcp_messages_tagged_correctly(self, mcp_test_client):
        response = mcp_test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        messages_path = schema["paths"].get("/mcp/messages", {})
        post_op = messages_path.get("post", {})
        assert "mcp" in post_op.get("tags", [])

    def test_mcp_tag_in_openapi_tags(self, mcp_test_client):
        response = mcp_test_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        tag_names = [t["name"] for t in schema.get("tags", [])]
        assert "mcp" in tag_names


class TestMCPModuleImports:
    def test_mcp_module_exports(self):
        from l1nkzip.mcp import mcp_server, sse_transport

        assert mcp_server is not None
        assert sse_transport is not None
        assert mcp_server.name == "l1nkzip-mcp-server"

    def test_sse_transport_endpoint(self):
        from l1nkzip.mcp import sse_transport

        assert "/mcp/messages" in str(sse_transport._endpoint)


class TestMCPSSEStreamIntegration:
    def test_sse_stream_handshake(self):
        with _get_app() as app:
            messages = asyncio.run(_collect_sse_messages(app, timeout=0.5))

        response_start = next(m for m in messages if m["type"] == "http.response.start")
        assert response_start["status"] == 200

        headers_dict = {k.decode(): v.decode() for k, v in response_start["headers"]}
        assert "text/event-stream" in headers_dict.get("content-type", "")

        body_chunks = [m for m in messages if m["type"] == "http.response.body"]
        full_body = b"".join(m.get("body", b"") for m in body_chunks).decode("utf-8", errors="replace")
        assert "event: endpoint" in full_body

        session_pattern = r"/mcp/messages\?session_id=[0-9a-f]+"
        assert re.search(session_pattern, full_body), f"No session_id found in: {full_body[:500]}"

    def test_sse_stream_has_cache_control(self):
        with _get_app() as app:
            messages = asyncio.run(_collect_sse_messages(app, timeout=0.5))

        response_start = next(m for m in messages if m["type"] == "http.response.start")
        headers_dict = {k.decode(): v.decode() for k, v in response_start["headers"]}
        cache_control = headers_dict.get("cache-control", "")
        assert "no-store" in cache_control or "no-cache" in cache_control

    def test_sse_stream_connection_keep_alive(self):
        with _get_app() as app:
            messages = asyncio.run(_collect_sse_messages(app, timeout=0.5))

        response_start = next(m for m in messages if m["type"] == "http.response.start")
        headers_dict = {k.decode(): v.decode() for k, v in response_start["headers"]}
        assert headers_dict.get("connection") == "keep-alive"
