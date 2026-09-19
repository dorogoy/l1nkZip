from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_CREATE", "100/minute")
    monkeypatch.setenv("RATE_LIMIT_REDIRECT", "200/minute")
    monkeypatch.setenv("DB_TYPE", "inmemory")

    import sys

    for m in ["l1nkzip.config", "l1nkzip.models", "l1nkzip.main"]:
        if m in sys.modules:
            del sys.modules[m]

    from l1nkzip.main import app

    return TestClient(app)


# Test cases for URL validation
invalid_urls = [
    ("missing_scheme", "example.com", 422),
    ("invalid_scheme", "ftp://example.com", 422),
    ("javascript_scheme", "javascript:alert(1)", 422),
    ("overlength_url", "https://example.com/" + "a" * 2048, 422),
    ("empty_url", "", 422),
    ("ssrf_localhost", "http://localhost", 422),
    ("ssrf_subdomain_localhost", "http://foo.localhost", 422),
    ("ssrf_loopback_ip", "http://127.0.0.1", 422),
    ("ssrf_private_ip_10", "http://10.0.0.1", 422),
    ("ssrf_private_ip_192", "http://192.168.1.1", 422),
    ("ssrf_metadata_ip", "http://169.254.169.254", 422),
    ("ssrf_integer_ip", "http://2130706433", 422),
    ("ssrf_hex_ip", "http://0x7f000001", 422),
    ("ssrf_octal_ip", "http://0177.0.0.1", 422),
    ("ssrf_shorthand_ip", "http://127.1", 422),
    ("ssrf_zero_ip", "http://0", 422),
]

# Test cases for admin token validation
invalid_tokens = [
    ("short_token", "short", 401),
    ("invalid_chars", "invalid!@#$%token", 401),
    ("empty_token", " ", 401),  # Use space instead of empty string
]


@pytest.mark.parametrize("test_name, url, expected_status", invalid_urls)
def test_invalid_url_creation(client, test_name, url, expected_status):
    """Test URL creation with invalid URLs"""
    response = client.post("/url", json={"url": url})
    assert response.status_code == expected_status
    assert "detail" in response.json()


@pytest.mark.parametrize("test_name, token, expected_status", invalid_tokens)
def test_invalid_admin_tokens(client, test_name, token, expected_status):
    """Test admin endpoints with invalid tokens"""
    # Test list endpoint
    response = client.get(f"/list/{token}")
    assert response.status_code == expected_status

    # Test phishtank update endpoint
    response = client.get(f"/phishtank/update/{token}")
    assert response.status_code == expected_status


def test_phishing_url_creation(client):
    """Test URL creation with phishing URL"""
    # Since PhishTank is not enabled in test environment, this should succeed
    # In production with PhishTank enabled, this would return 403
    response = client.post("/url", json={"url": "http://phishing-example.com"})
    assert response.status_code == 200  # No phishing check in test environment


def test_valid_url_creation(client):
    """Test URL creation with valid URL"""
    response = client.post("/url", json={"url": "https://example.com"})
    assert response.status_code == 200
    assert "link" in response.json()


def test_redirect_with_invalid_short_link(client):
    """Test redirection with invalid short link format"""
    response = client.get("/invalid!link")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "http://2130706433",
        "http://0x7f000001",
        "http://0177.0.0.1",
        "http://127.1",
        "http://0",
    ],
)
@pytest.mark.asyncio
async def test_validate_url_blocks_alt_ipv4_forms(monkeypatch, url):
    """Alternative IPv4 forms must be blocked by the SSRF check itself,
    not only by upstream format validation (validators/pydantic),
    whose behavior is not guaranteed across versions."""
    from fastapi import HTTPException

    from l1nkzip import main
    from l1nkzip.main import validate_url

    monkeypatch.setattr(main.validators, "url", lambda _: True)
    with pytest.raises(HTTPException) as exc_info:
        await validate_url(url)
    assert exc_info.value.status_code == 422
    assert "local or private network" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_url_blocks_dns_resolved_private_ip(monkeypatch):
    """Hostnames resolving to private/loopback IP addresses must be blocked to prevent SSRF."""
    import socket

    from fastapi import HTTPException

    from l1nkzip import main
    from l1nkzip.main import validate_url

    monkeypatch.setattr(main.validators, "url", lambda _: True)

    async def mock_getaddrinfo(host, port):
        if host == "private.internal.example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.50", 80))]
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]

    loop = main.asyncio.get_running_loop()
    monkeypatch.setattr(loop, "getaddrinfo", mock_getaddrinfo)

    # Should raise 422 for domain resolving to private IP
    with pytest.raises(HTTPException) as exc_info:
        await validate_url("http://private.internal.example.com")
    assert exc_info.value.status_code == 422
    assert "local or private network" in exc_info.value.detail

    # Should pass for domain resolving to public IP
    assert await validate_url("http://public.example.com") == "http://public.example.com"
