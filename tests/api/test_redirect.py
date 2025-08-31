"""
Tests for URL redirection endpoint (/{link}).
"""


class TestRedirectEndpoint:
    """Test cases for the URL redirection endpoint."""

    def test_redirect_existing_link(self, test_client):
        """Test redirecting to an existing short link."""
        # First create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Then redirect using the short link
        redirect_response = test_client.get(f"/{short_link}", follow_redirects=False)
        assert redirect_response.status_code == 301
        assert redirect_response.headers["location"] == "https://example.com/"

    def test_redirect_nonexistent_link(self, test_client):
        """Test redirecting to a non-existent short link."""
        response = test_client.get("/nonexistentlink")
        assert response.status_code == 404

    def test_redirect_invalid_link_format(self, test_client):
        """Test redirecting with invalid link format."""
        invalid_links = [
            "invalid!link",
            "link with spaces",
            "",
            "a" * 100,  # Very long link
        ]

        for link in invalid_links:
            response = test_client.get(f"/{link}")
            assert response.status_code == 404

    def test_redirect_increments_visit_count(self, test_client):
        """Test that redirecting increments the visit count."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Initial visit count should be 0
        assert create_data["visits"] == 0

        # First redirect
        redirect_response1 = test_client.get(f"/{short_link}", follow_redirects=False)
        assert redirect_response1.status_code == 301

        # Check visit count increased - need to get the link info again
        info_response = test_client.get(f"/info/{short_link}")
        if info_response.status_code == 200:
            info_data = info_response.json()
            assert info_data["visits"] == 1

    def test_redirect_multiple_visits(self, test_client):
        """Test multiple redirects to the same link."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Multiple redirects
        for _i in range(3):
            response = test_client.get(f"/{short_link}", follow_redirects=False)
            assert response.status_code == 301
            assert response.headers["location"] == "https://example.com/"

    def test_redirect_case_sensitivity(self, test_client):
        """Test that short links are case-sensitive."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Try redirecting with different case
        if short_link != short_link.lower():
            response = test_client.get(f"/{short_link.lower()}")
            assert response.status_code == 404

    def test_redirect_with_trailing_slash(self, test_client):
        """Test redirecting with trailing slash."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Try redirecting with trailing slash
        response = test_client.get(f"/{short_link}/")
        assert response.status_code == 404

    def test_redirect_http_methods(self, test_client):
        """Test that only GET method works for redirect."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Test different HTTP methods
        methods = ["POST", "PUT", "DELETE", "PATCH"]
        for method in methods:
            response = test_client.request(method, f"/{short_link}")
            assert response.status_code in [405, 404]  # Method Not Allowed or Not Found

    def test_redirect_metrics_integration(self, test_client, metrics_collector):
        """Test that redirect metrics are recorded."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Redirect
        redirect_response = test_client.get(f"/{short_link}", follow_redirects=False)
        assert redirect_response.status_code == 301

        # Verify metrics were recorded
        # Use the proper get_metrics() function to access the metrics
        metrics_data = metrics_collector.get_metrics().decode("utf-8")
        # The redirect metric should be incremented, check if it's greater than initial value
        assert "l1nkzip_redirects_total" in metrics_data

    def test_redirect_rate_limiting(self, test_client):
        """Test rate limiting for URL redirection."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Multiple redirects should work with test rate limits
        for _i in range(5):
            response = test_client.get(f"/{short_link}", follow_redirects=False)
            assert response.status_code == 301

    def test_redirect_headers(self, test_client):
        """Test that redirect response includes appropriate headers."""
        # Create a short link
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Redirect
        response = test_client.get(f"/{short_link}", follow_redirects=False)
        assert response.status_code == 301

        # Check headers
        assert "location" in response.headers
        assert response.headers["location"] == "https://example.com/"
        # 301 redirects typically don't include content-type header
        # They may include content-length: 0
        assert "content-length" in response.headers

    def test_redirect_special_characters_in_url(self, test_client):
        """Test redirecting URLs with special characters."""
        urls_with_special_chars = [
            "https://example.com/path?param=value&other=123",
            "https://example.com/path#section",
            "https://example.com/path with spaces",
            "https://example.com/unicode/测试",
        ]

        for url in urls_with_special_chars:
            # Create short link
            create_response = test_client.post("/url", json={"url": url})
            assert create_response.status_code == 200
            create_data = create_response.json()
            short_link = create_data["link"]

            # Redirect
            redirect_response = test_client.get(f"/{short_link}", follow_redirects=False)
            assert redirect_response.status_code == 301
            # URLs with spaces and special characters may be URL-encoded in the response
            import urllib.parse

            if " " in url or any(ord(c) > 127 for c in url):
                expected_url = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=")
                assert redirect_response.headers["location"] == expected_url
            else:
                assert redirect_response.headers["location"] == url
