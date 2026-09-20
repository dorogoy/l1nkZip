"""Tests for security headers middleware."""


def test_security_headers_present(test_client):
    """All responses must carry the standard security headers."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Content-Security-Policy") == "frame-ancestors 'none'"
    assert response.headers.get("Strict-Transport-Security") == "max-age=63072000; includeSubDomains"
    assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=()"
    assert response.headers.get("X-Permitted-Cross-Domain-Policies") == "none"
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
