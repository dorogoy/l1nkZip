"""Tests for security headers middleware."""


def test_security_headers_present(test_client):
    """All responses must carry the standard security headers."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Content-Security-Policy") == "frame-ancestors 'none'"
