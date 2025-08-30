import pytest
from fastapi.testclient import TestClient

from l1nkzip.main import app

client = TestClient(app)

# Test cases for URL validation
invalid_urls = [
    ("missing_scheme", "example.com", 422),
    ("invalid_scheme", "ftp://example.com", 422),
    ("javascript_scheme", "javascript:alert(1)", 422),
    ("overlength_url", "https://example.com/" + "a" * 2048, 422),
    ("empty_url", "", 422),
]

# Test cases for admin token validation
invalid_tokens = [
    ("short_token", "short", 401),
    ("invalid_chars", "invalid!@#$%token", 401),
    ("empty_token", " ", 401),  # Use space instead of empty string
]


@pytest.mark.parametrize("test_name, url, expected_status", invalid_urls)
def test_invalid_url_creation(test_name, url, expected_status):
    """Test URL creation with invalid URLs"""
    response = client.post("/url", json={"url": url})
    assert response.status_code == expected_status
    assert "detail" in response.json()


@pytest.mark.parametrize("test_name, token, expected_status", invalid_tokens)
def test_invalid_admin_tokens(test_name, token, expected_status):
    """Test admin endpoints with invalid tokens"""
    # Test list endpoint
    response = client.get(f"/list/{token}")
    assert response.status_code == expected_status

    # Test phishtank update endpoint
    response = client.get(f"/phishtank/update/{token}")
    assert response.status_code == expected_status


def test_phishing_url_creation():
    """Test URL creation with phishing URL"""
    # Since PhishTank is not enabled in test environment, this should succeed
    # In production with PhishTank enabled, this would return 403
    response = client.post("/url", json={"url": "http://phishing-example.com"})
    assert response.status_code == 200  # No phishing check in test environment


def test_valid_url_creation():
    """Test URL creation with valid URL"""
    response = client.post("/url", json={"url": "https://example.com"})
    assert response.status_code == 200
    assert "link" in response.json()


def test_redirect_with_invalid_short_link():
    """Test redirection with invalid short link format"""
    response = client.get("/invalid!link")
    assert response.status_code == 404
