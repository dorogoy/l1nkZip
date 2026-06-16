"""
Tests for public MCP tools (shorten_url and get_original_url).

These tests exercise the tool handlers registered in l1nkzip.mcp. Handler functions
are invoked directly because the MCP decorator returns the original callable, allowing
us to validate behavior without driving the full SSE/JSON-RPC transport.
"""

import sys
from unittest.mock import patch

import mcp.types as types
import pytest

from l1nkzip.config import Settings


def _get_handlers():
    modules_to_clear = ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main", "l1nkzip.mcp"]
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    test_settings = Settings()
    test_settings.db_type = "inmemory"
    test_settings.redis_server = None
    test_settings.metrics_enabled = True
    test_settings.phishtank = None
    test_settings.rate_limit_create = "1000/minute"
    test_settings.rate_limit_redirect = "2000/minute"

    with patch("l1nkzip.config.settings", test_settings):
        from l1nkzip.main import app  # noqa: F401 - imports app to wire mcp handlers
        from l1nkzip.mcp import handle_call_tool, handle_list_tools

    return handle_list_tools, handle_call_tool


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
            patch("l1nkzip.mcp.settings.phishtank", "test-api-key"),
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
            patch("l1nkzip.mcp.settings.phishtank", "test-api-key"),
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
