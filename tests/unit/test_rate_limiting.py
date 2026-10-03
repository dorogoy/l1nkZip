import sys

from fastapi import Request
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client(monkeypatch):
    """Test client fixture with higher rate limits for testing"""
    # Set higher rate limits for testing to avoid conflicts between tests
    monkeypatch.setenv("RATE_LIMIT_CREATE", "100/minute")
    monkeypatch.setenv("RATE_LIMIT_REDIRECT", "200/minute")
    monkeypatch.setenv("DB_TYPE", "inmemory")  # Use in-memory database for tests

    # Force reload of modules to pick up new environment variables
    import sys

    modules_to_clear = ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]

    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    # Import after setting environment variables
    from l1nkzip.main import app

    return TestClient(app)


class TestRateLimiting:
    """Test cases for rate limiting functionality"""

    def test_url_creation_rate_limit(self, client):
        """Test that URL creation works (rate limiting disabled for tests)"""
        url_data = {"url": "https://example.com"}

        # With high rate limits for testing, multiple requests should succeed
        for _i in range(10):
            response = client.post("/url", json=url_data)
            assert response.status_code == 200

    def test_rate_limit_exceeded_returns_429(self, monkeypatch):
        """Test that exceeding rate limits returns HTTP 429 with appropriate error payload."""
        monkeypatch.setenv("RATE_LIMIT_CREATE", "2/minute")
        monkeypatch.setenv("DB_TYPE", "inmemory")

        import sys

        for mod in ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]:
            if mod in sys.modules:
                del sys.modules[mod]

        from l1nkzip.main import app

        test_client = TestClient(app)
        url_data = {"url": "https://example.com"}

        assert test_client.post("/url", json=url_data).status_code == 200
        assert test_client.post("/url", json=url_data).status_code == 200

        res = test_client.post("/url", json=url_data)
        assert res.status_code == 429
        assert "Rate limit exceeded" in res.json().get("error", "")

    def test_health_endpoint_works(self, client):
        """Test that the health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_url_creation_works(self, client):
        """Test that URL creation works and returns proper response"""
        url_data = {"url": "https://example.com"}

        response = client.post("/url", json=url_data)
        assert response.status_code == 200

        response_data = response.json()
        assert "link" in response_data
        assert "full_link" in response_data
        assert "url" in response_data
        assert "visits" in response_data

    def test_multiple_url_creations(self, client):
        """Test that multiple URL creations work"""
        urls = [
            {"url": "https://example.com"},
            {"url": "https://google.com"},
            {"url": "https://github.com"},
        ]

        # All creations should succeed with high rate limits
        for url_data in urls:
            response = client.post("/url", json=url_data)
            assert response.status_code == 200

    def test_admin_endpoints_not_rate_limited(self, client):
        """Test that admin endpoints are not rate limited"""
        # Health check should not be rate limited
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

        # List endpoint should not be rate limited (requires token)
        for _ in range(10):
            response = client.get("/list/__change_me__")
            assert response.status_code == 401  # Unauthorized but not rate limited


def _mcp_request(host: str) -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/mcp/sse",
            "raw_path": b"/mcp/sse",
            "query_string": b"",
            "headers": [],
            "client": (host, 1234),
            "server": ("testserver", 80),
        }
    )


def _reload_app():
    for mod in ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]:
        if mod in sys.modules:
            del sys.modules[mod]
    from l1nkzip.main import app

    return app


class TestMcpRateLimits:
    """MCP create/resolve limits use the process-wide limiter, keyed by client IP."""

    @pytest.mark.asyncio
    async def test_shorten_url_shares_post_url_budget(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_CREATE", "2/minute")
        monkeypatch.setenv("DB_TYPE", "inmemory")
        app = _reload_app()
        client = TestClient(app)

        assert client.post("/url", json={"url": "https://example.com"}).status_code == 200
        assert client.post("/url", json={"url": "https://example.org"}).status_code == 200

        from l1nkzip.mcp import handle_call_tool, mcp_request

        same_client = mcp_request.set(_mcp_request("testclient"))
        try:
            with pytest.raises(ValueError, match="Rate limit exceeded"):
                await handle_call_tool("shorten_url", {"url": "https://example.net"})
        finally:
            mcp_request.reset(same_client)

        blocked = client.post("/url", json={"url": "https://example.edu"})
        assert blocked.status_code == 429

        other_client = mcp_request.set(_mcp_request("203.0.113.9"))
        try:
            created = await handle_call_tool("shorten_url", {"url": "https://example.co"})
        finally:
            mcp_request.reset(other_client)
        assert created[0].text

    @pytest.mark.asyncio
    async def test_get_original_url_limit_is_per_ip_not_per_connection(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_CREATE", "20/minute")
        monkeypatch.setenv("RATE_LIMIT_REDIRECT", "2/minute")
        monkeypatch.setenv("DB_TYPE", "inmemory")
        app = _reload_app()
        client = TestClient(app)
        created = client.post("/url", json={"url": "https://example.com"})
        assert created.status_code == 200
        link = created.json()["link"]

        from l1nkzip.mcp import handle_call_tool, mcp_request

        first = mcp_request.set(_mcp_request("198.51.100.4"))
        try:
            assert await handle_call_tool("get_original_url", {"link": link})
            assert await handle_call_tool("get_original_url", {"link": link})
        finally:
            mcp_request.reset(first)

        second_connection = mcp_request.set(_mcp_request("198.51.100.4"))
        try:
            with pytest.raises(ValueError, match="Rate limit exceeded"):
                await handle_call_tool("get_original_url", {"link": link})
        finally:
            mcp_request.reset(second_connection)

        other_ip = mcp_request.set(_mcp_request("198.51.100.8"))
        try:
            resolved = await handle_call_tool("get_original_url", {"link": link})
        finally:
            mcp_request.reset(other_ip)
        assert resolved[0].text == "https://example.com/"
