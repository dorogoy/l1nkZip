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
    ("ssrf_cgnat_ip", "http://100.64.0.1", 422),
    ("ssrf_multicast_ip", "http://224.0.0.1", 422),
    ("ssrf_ipv4_mapped_loopback", "http://[::ffff:127.0.0.1]", 422),
    ("ssrf_ipv4_mapped_private", "http://[::ffff:10.0.0.1]", 422),
    ("ssrf_ipv4_mapped_cgnat", "http://[::ffff:100.64.0.1]", 422),
    ("ssrf_ipv4_mapped_link_local", "http://[::ffff:169.254.169.254]", 422),
    ("ssrf_ipv4_mapped_hex_loopback", "http://[::ffff:7f00:1]", 422),
    ("ssrf_nat64_loopback", "http://[64:ff9b::127.0.0.1]", 422),
    ("ssrf_nat64_private", "http://[64:ff9b::10.0.0.1]", 422),
    ("ssrf_6to4_loopback", "http://[2002:7f00:0001::]", 422),
    ("ssrf_6to4_private", "http://[2002:0a00:0001::]", 422),
    ("ssrf_isatap_loopback", "http://[2000::5efe:7f00:1]", 422),
    ("ssrf_isatap_private", "http://[2000::5efe:10.0.0.1]", 422),
]

# Test cases for admin token validation
invalid_tokens = [
    ("short_token", "short", 401, "Invalid admin token"),
    ("unauthorized_token", "invalidtoken123!", 401, "Unauthorized"),
    ("empty_token", " ", 401, "Invalid admin token"),  # Use space instead of empty string
    ("colon_token", "a" * 16 + ":", 401, "Invalid admin token format"),
    ("dot_token", "a" * 16 + ".", 401, "Invalid admin token format"),
]


@pytest.mark.parametrize("test_name, url, expected_status", invalid_urls)
def test_invalid_url_creation(client, test_name, url, expected_status):
    """Test URL creation with invalid URLs"""
    response = client.post("/url", json={"url": url})
    assert response.status_code == expected_status
    assert "detail" in response.json()


@pytest.mark.parametrize("test_name, token, expected_status, expected_detail", invalid_tokens)
def test_invalid_admin_tokens(client, test_name, token, expected_status, expected_detail):
    """Test admin endpoints with invalid tokens"""
    # Test list endpoint
    response = client.get(f"/list/{token}")
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail

    # Test phishtank update endpoint
    response = client.get(f"/phishtank/update/{token}")
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


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


def test_validate_short_link_rejects_trailing_newline():
    """Verify validate_short_link rejects inputs with trailing newlines (re.match vs re.fullmatch fix)."""
    from fastapi import HTTPException

    from l1nkzip.main import validate_short_link

    with pytest.raises(HTTPException) as exc_info:
        validate_short_link("abcd\n")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid short link format"


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


def test_validate_admin_token_character_restrictions():
    """Verify validate_admin_token rejects tokens containing unallowed characters."""
    from fastapi import HTTPException

    from l1nkzip.main import validate_admin_token

    valid_token = "a" * 15 + "!"
    assert validate_admin_token(valid_token) == valid_token

    # Hyphen, plus, underscore, equals should be valid
    for char in ["-", "+", "_", "="]:
        token = "a" * 15 + char
        assert validate_admin_token(token) == token

    # Characters in ASCII range + to = (like :, ., /, ;, <, ,) must be rejected
    for char in [":", ".", "/", ";", "<", ","]:
        token = "a" * 15 + char
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_token(token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid admin token format"

    # Trailing newline must also be rejected
    with pytest.raises(HTTPException) as exc_info:
        validate_admin_token("a" * 16 + "\n")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid admin token format"


def test_404_invalid_site_url_scheme(client, monkeypatch):
    """Test that setting site_url to a non-HTTP(S) scheme (e.g. javascript:) does not render the link in 404 page."""
    from l1nkzip.config import Settings, settings

    s = Settings(site_url="  javascript:alert(1)  ")
    assert s.site_url is None

    s_valid = Settings(site_url="  https://example.com  ")
    assert s_valid.site_url == "https://example.com"

    monkeypatch.setattr(settings, "site_url", None)
    response = client.get("/404")
    assert response.status_code == 404
    assert "<a href=" not in response.text


def test_404_valid_site_url_scheme_renders_link(client, monkeypatch):
    """Test that a valid HTTP(S) site_url still renders the homepage link on the 404 page."""
    from l1nkzip.config import settings

    monkeypatch.setattr(settings, "site_url", "https://example.com/")
    response = client.get("/404")
    assert response.status_code == 404
    assert 'href="https://example.com/"' in response.text


@pytest.mark.parametrize(
    "url",
    [
        "http://[::ffff:127.0.0.1]",
        "http://[::ffff:10.0.0.1]",
        "http://[::ffff:169.254.169.254]",
        "http://[::ffff:7f00:1]",
    ],
)
@pytest.mark.asyncio
async def test_validate_url_blocks_ipv4_mapped_ipv6(monkeypatch, url):
    """IPv4-mapped IPv6 addresses targeting private/loopback/link-local ranges must be blocked."""
    from fastapi import HTTPException

    from l1nkzip import main
    from l1nkzip.main import validate_url

    monkeypatch.setattr(main.validators, "url", lambda _: True)
    with pytest.raises(HTTPException) as exc_info:
        await validate_url(url)
    assert exc_info.value.status_code == 422
    assert "local or private network" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_url_allows_public_ipv4_mapped_ipv6(monkeypatch):
    """Public IPv4-mapped IPv6 addresses must be allowed."""
    from l1nkzip import main
    from l1nkzip.main import validate_url

    monkeypatch.setattr(main.validators, "url", lambda _: True)
    public_url = "http://[::ffff:8.8.8.8]"
    assert await validate_url(public_url) == public_url


@pytest.mark.asyncio
async def test_validate_url_allows_public_translation_ipv6(monkeypatch):
    """Public IPv6 translation addresses (NAT64 / 6to4) targeting public IPv4 must be allowed."""
    from l1nkzip import main
    from l1nkzip.main import validate_url

    monkeypatch.setattr(main.validators, "url", lambda _: True)
    public_nat64 = "http://[64:ff9b::8.8.8.8]"
    public_6to4 = "http://[2002:0808:0808::]"
    public_isatap = "http://[2000::5efe:8.8.8.8]"
    assert await validate_url(public_nat64) == public_nat64
    assert await validate_url(public_6to4) == public_6to4
    assert await validate_url(public_isatap) == public_isatap
