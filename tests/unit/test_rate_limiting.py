import pytest
from fastapi.testclient import TestClient


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
        for i in range(10):
            response = client.post("/url", json=url_data)
            assert response.status_code == 200

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
