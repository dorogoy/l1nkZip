"""
Tests for public MCP tools (shorten_url and get_original_url).

These tests exercise the tool handlers registered in l1nkzip.mcp. Handler functions
are invoked directly because the MCP decorator returns the original callable, allowing
us to validate behavior without driving the full SSE/JSON-RPC transport.
"""

import asyncio
from contextlib import contextmanager
import json
import logging
import re
import sys
from unittest.mock import patch

import mcp.types as types
import pytest

from l1nkzip.config import Settings


def _get_handlers():
    test_settings = Settings()
    test_settings.db_type = "inmemory"
    test_settings.redis_server = None
    test_settings.metrics_enabled = True
    test_settings.phishtank = None
    test_settings.rate_limit_create = "1000/minute"
    test_settings.rate_limit_redirect = "2000/minute"

    # Reload main so handlers are wired with the patched settings.
    sys.modules.pop("l1nkzip.main", None)
    sys.modules.pop("l1nkzip.mcp", None)

    with patch("l1nkzip.config.settings", test_settings):
        from l1nkzip.main import app  # noqa: F401 - imports app to wire mcp handlers
        from l1nkzip.mcp import handle_call_tool, handle_list_tools

        return handle_list_tools, handle_call_tool


@contextmanager
def _get_app():
    test_settings = Settings()
    test_settings.db_type = "inmemory"
    test_settings.redis_server = None
    test_settings.metrics_enabled = True
    test_settings.phishtank = None
    test_settings.rate_limit_create = "1000/minute"
    test_settings.rate_limit_redirect = "2000/minute"

    sys.modules.pop("l1nkzip.main", None)

    with patch("l1nkzip.config.settings", test_settings):
        from l1nkzip.main import app

        yield app


@pytest.fixture
def handlers():
    list_tools, call_tool = _get_handlers()
    return list_tools, call_tool


class TestListTools:
    """AC 1: tool discovery via list_tools."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_both_tools(self, handlers):
        list_tools, _ = handlers
        tools = await list_tools()

        names = [t.name for t in tools]
        assert "shorten_url" in names
        assert "get_original_url" in names

    @pytest.mark.asyncio
    async def test_shorten_url_schema(self, handlers):
        list_tools, _ = handlers
        tools = await list_tools()
        shorten = next(t for t in tools if t.name == "shorten_url")

        assert shorten.description
        schema = shorten.inputSchema
        assert schema["type"] == "object"
        assert "url" in schema["properties"]
        assert schema["properties"]["url"]["type"] == "string"
        assert "url" in schema["required"]

    @pytest.mark.asyncio
    async def test_get_original_url_schema(self, handlers):
        list_tools, _ = handlers
        tools = await list_tools()
        get_url = next(t for t in tools if t.name == "get_original_url")

        assert get_url.description
        schema = get_url.inputSchema
        assert schema["type"] == "object"
        assert "link" in schema["properties"]
        assert schema["properties"]["link"]["type"] == "string"
        assert "link" in schema["required"]

    @pytest.mark.asyncio
    async def test_list_urls_present_in_tools(self, handlers):
        list_tools, _ = handlers
        tools = await list_tools()
        names = [t.name for t in tools]
        assert "list_urls" in names

    @pytest.mark.asyncio
    async def test_list_urls_schema(self, handlers):
        list_tools, _ = handlers
        tools = await list_tools()
        list_urls = next(t for t in tools if t.name == "list_urls")

        assert list_urls.description
        schema = list_urls.inputSchema
        assert schema["type"] == "object"
        assert "token" in schema["properties"]
        assert schema["properties"]["token"]["type"] == "string"
        assert "token" in schema["required"]
        assert "limit" in schema["properties"]
        assert schema["properties"]["limit"]["type"] == "integer"
        assert schema["properties"]["limit"].get("default") == 100


class TestShortenUrlTool:
    """AC 2: shorten_url execution."""

    @pytest.mark.asyncio
    async def test_shorten_valid_url_returns_full_link(self, handlers):
        _, call_tool = handlers
        result = await call_tool("shorten_url", {"url": "https://example.com"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].text.startswith("https://l1nk.zip/")

    @pytest.mark.asyncio
    async def test_shorten_missing_url_argument_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("shorten_url", {})

    @pytest.mark.asyncio
    async def test_shorten_non_dict_arguments_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("shorten_url", "not-a-dict")

    @pytest.mark.asyncio
    async def test_shorten_non_string_url_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("shorten_url", {"url": 123})

    @pytest.mark.asyncio
    async def test_shorten_invalid_url_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("shorten_url", {"url": "not-a-url"})

    @pytest.mark.asyncio
    async def test_shorten_dangerous_scheme_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("shorten_url", {"url": "javascript:alert(1)"})

    @pytest.mark.asyncio
    async def test_shorten_phishing_url_raises(self, handlers):
        _, call_tool = handlers

        class FakePhish:
            phish_detail_url = "https://phishtank.org/detail/test"

        with (
            patch("l1nkzip.config.settings.phishtank", "test-api-key"),
            patch("l1nkzip.main.retry_phishtank_check") as mock_retry,
        ):
            mock_retry.return_value = FakePhish()
            with pytest.raises(ValueError, match="phishing"):
                await call_tool("shorten_url", {"url": "https://phishing.com"})

    @pytest.mark.asyncio
    async def test_shorten_duplicate_returns_same_link(self, handlers):
        _, call_tool = handlers
        first = await call_tool("shorten_url", {"url": "https://duplicate.com"})
        second = await call_tool("shorten_url", {"url": "https://duplicate.com"})

        assert first[0].text == second[0].text


class TestGetOriginalUrlTool:
    """AC 3: get_original_url execution."""

    @pytest.mark.asyncio
    async def test_get_original_url_after_shorten(self, handlers):
        _, call_tool = handlers
        shorten_result = await call_tool("shorten_url", {"url": "https://example.com"})
        full_link = shorten_result[0].text
        short_link = full_link.replace("https://l1nk.zip/", "")

        result = await call_tool("get_original_url", {"link": short_link})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].text == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_original_url_missing_link_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("get_original_url", {})

    @pytest.mark.asyncio
    async def test_get_original_url_invalid_format_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("get_original_url", {"link": "bad!"})

    @pytest.mark.asyncio
    async def test_get_original_url_nonexistent_link_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("get_original_url", {"link": "nonexistent"})

    @pytest.mark.asyncio
    async def test_get_original_url_cache_hit_returns_cached_url(self, handlers):
        _, call_tool = handlers
        shorten_result = await call_tool("shorten_url", {"url": "https://cached.com"})
        full_link = shorten_result[0].text
        short_link = full_link.replace("https://l1nk.zip/", "")

        fake_cache = type(
            "Cache",
            (),
            {
                "is_enabled": lambda self: True,
                "get": lambda self, key: "https://cached.com",
                "set": lambda self, key, value: True,
            },
        )()

        with patch("l1nkzip.mcp.cache", fake_cache):
            result = await call_tool("get_original_url", {"link": short_link})

        assert result[0].text == "https://cached.com"

    @pytest.mark.asyncio
    async def test_get_original_url_phishing_url_raises(self, handlers):
        _, call_tool = handlers

        class FakePhish:
            phish_detail_url = "https://phishtank.org/detail/test"

        shorten_result = await call_tool("shorten_url", {"url": "https://phishing-redirect.com"})
        full_link = shorten_result[0].text
        short_link = full_link.replace("https://l1nk.zip/", "")

        with (
            patch("l1nkzip.config.settings.phishtank", "test-api-key"),
            patch("l1nkzip.main.retry_phishtank_check") as mock_retry,
        ):
            mock_retry.return_value = FakePhish()
            with pytest.raises(ValueError, match="phishing"):
                await call_tool("get_original_url", {"link": short_link})


class TestUnknownTool:
    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, handlers):
        _, call_tool = handlers
        with pytest.raises(ValueError):
            await call_tool("does_not_exist", {})


VALID_TOKEN = "test-admin-token-12345"


@pytest.fixture
def list_urls_handlers(test_settings):
    import l1nkzip.main  # noqa: F401
    from l1nkzip.mcp import handle_call_tool, handle_list_tools

    with patch("l1nkzip.config.settings", test_settings):
        yield handle_list_tools, handle_call_tool


class TestListUrlsTool:
    @pytest.mark.asyncio
    async def test_valid_token_returns_json_list(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        await call_tool("shorten_url", {"url": "https://list-example.com"})

        result = await call_tool("list_urls", {"token": VALID_TOKEN})

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        data = json.loads(result[0].text)
        assert isinstance(data, list)
        assert len(data) >= 1
        item = data[0]
        for key in ("link", "full_link", "url", "visits"):
            assert key in item

    @pytest.mark.asyncio
    async def test_custom_limit_passed_to_get_visits(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with patch("l1nkzip.models.get_visits", return_value=[]) as mock_get:
            result = await call_tool("list_urls", {"token": VALID_TOKEN, "limit": 5})

        mock_get.assert_called_once_with(5)
        assert result[0].text == "[]"

    @pytest.mark.asyncio
    async def test_default_limit_is_100(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with patch("l1nkzip.models.get_visits", return_value=[]) as mock_get:
            await call_tool("list_urls", {"token": VALID_TOKEN})

        mock_get.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_missing_token_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Unauthorized"):
            await call_tool("list_urls", {})

    @pytest.mark.asyncio
    async def test_wrong_token_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Unauthorized"):
            await call_tool("list_urls", {"token": "a-different-valid-tok"})

    @pytest.mark.asyncio
    async def test_short_token_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Unauthorized"):
            await call_tool("list_urls", {"token": "short"})

    @pytest.mark.asyncio
    async def test_bad_chars_token_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Unauthorized"):
            await call_tool("list_urls", {"token": "bad token with spaces"})

    @pytest.mark.asyncio
    async def test_limit_below_one_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Limit"):
            await call_tool("list_urls", {"token": VALID_TOKEN, "limit": 0})

    @pytest.mark.asyncio
    async def test_limit_above_1000_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Limit"):
            await call_tool("list_urls", {"token": VALID_TOKEN, "limit": 1001})

    @pytest.mark.asyncio
    async def test_non_dict_arguments_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Invalid arguments"):
            await call_tool("list_urls", "not-a-dict")

    @pytest.mark.asyncio
    async def test_non_string_token_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="Unauthorized"):
            await call_tool("list_urls", {"token": 12345})

    @pytest.mark.asyncio
    async def test_non_integer_limit_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="limit"):
            await call_tool("list_urls", {"token": VALID_TOKEN, "limit": "100"})

    @pytest.mark.asyncio
    async def test_boolean_limit_rejected(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with pytest.raises(ValueError, match="limit"):
            await call_tool("list_urls", {"token": VALID_TOKEN, "limit": True})

    @pytest.mark.asyncio
    async def test_empty_result_serializes_empty_json_array(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with patch("l1nkzip.models.get_visits", return_value=[]):
            result = await call_tool("list_urls", {"token": VALID_TOKEN})

        assert result[0].text == "[]"

    @pytest.mark.asyncio
    async def test_db_error_raises_generic_value_error(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with patch("l1nkzip.models.get_visits", side_effect=RuntimeError("connection lost")):
            with pytest.raises(ValueError, match="Failed to retrieve URL list"):
                await call_tool("list_urls", {"token": VALID_TOKEN})

    @pytest.mark.asyncio
    async def test_db_error_message_does_not_leak_internal_detail(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        with patch("l1nkzip.models.get_visits", side_effect=RuntimeError("connection lost")):
            with pytest.raises(ValueError) as exc_info:
                await call_tool("list_urls", {"token": VALID_TOKEN})

        assert "connection lost" not in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_never_appears_in_logs(self, list_urls_handlers, caplog):
        _, call_tool = list_urls_handlers
        caplog.set_level(logging.ERROR)
        secret = VALID_TOKEN
        with patch("l1nkzip.models.get_visits", side_effect=RuntimeError("boom")):
            with pytest.raises(ValueError):
                await call_tool("list_urls", {"token": secret})

        for record in caplog.records:
            assert secret not in record.getMessage()
            assert secret not in str(record.__dict__)

    @pytest.mark.asyncio
    async def test_get_visits_runs_via_executor(self, list_urls_handlers):
        _, call_tool = list_urls_handlers
        loop = asyncio.get_running_loop()
        with (
            patch.object(loop, "run_in_executor", wraps=loop.run_in_executor) as executor_spy,
            patch("l1nkzip.models.get_visits", return_value=[]) as mock_get,
        ):
            await call_tool("list_urls", {"token": VALID_TOKEN})

        assert executor_spy.called
        assert mock_get.called


async def _drive_sse_messages(app, timeout: float = 3.0):
    sse_scope = {
        "type": "http",
        "method": "GET",
        "path": "/mcp/sse",
        "raw_path": b"/mcp/sse",
        "query_string": b"",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "asgi": {"version": "3.0"},
    }
    chunks: list[bytes] = []

    async def sse_receive():
        await asyncio.Event().wait()

    async def sse_send(message):
        if message["type"] == "http.response.body":
            body = message.get("body", b"") or b""
            if body:
                chunks.append(body)

    task = asyncio.create_task(app(sse_scope, sse_receive, sse_send))

    session_id = None
    deadline = asyncio.get_running_loop().time() + timeout
    while session_id is None and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.02)
        blob = b"".join(chunks).decode("utf-8", errors="replace")
        match = re.search(r"session_id=([0-9a-f]+)", blob)
        if match:
            session_id = match.group(1)

    if session_id is None:
        task.cancel()
        raise AssertionError("No session_id received from SSE endpoint")

    async def post_message(message):
        payload = json.dumps(message).encode("utf-8")
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp/messages",
            "raw_path": b"/mcp/messages",
            "query_string": f"session_id={session_id}".encode(),
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode()),
            ],
            "server": ("testserver", 80),
            "client": ("testclient", 12345),
            "asgi": {"version": "3.0"},
        }
        fed = {"done": False}

        async def receive():
            if not fed["done"]:
                fed["done"] = True
                return {"type": "http.request", "body": payload, "more_body": False}
            await asyncio.Event().wait()

        async def send(m):
            pass

        await app(scope, receive, send)

    async def wait_for_response(id_value):
        needle = f'"id": {id_value}'
        alt = f'"id":{id_value}'
        end = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < end:
            blob = b"".join(chunks).decode("utf-8", errors="replace")
            if needle in blob or alt in blob:
                return blob
            await asyncio.sleep(0.02)
        return b"".join(chunks).decode("utf-8", errors="replace")

    await post_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1.0"},
            },
        }
    )
    await wait_for_response(1)
    await post_message({"jsonrpc": "2.0", "method": "notifications/initialized"})
    await post_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "list_urls", "arguments": {}},
        }
    )
    blob = await wait_for_response(2)

    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass
    return blob


class TestListUrlsSSEIntegration:
    def test_missing_token_returns_error_over_sse(self):
        with _get_app() as app:
            blob = asyncio.run(_drive_sse_messages(app))

        assert '"id": 2' in blob or '"id":2' in blob
        assert '"isError":true' in blob
        assert "Unauthorized" in blob
