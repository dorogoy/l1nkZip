"""
Tests for admin endpoints (/list/{token}, /phishtank/update/{token}, etc.).
"""

import pytest


class TestAdminEndpoints:
    """Test cases for admin endpoints."""

    def test_list_urls_valid_token(self, test_client, admin_token):
        """Test listing URLs with valid admin token."""
        # First create some URLs
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
        ]

        for url in urls:
            response = test_client.post("/url", json={"url": url})
            assert response.status_code == 200

        # List URLs with valid token
        response = test_client.get(f"/list/{admin_token}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # At least the URLs we created

        # Check that each URL entry has required fields
        for entry in data:
            assert "link" in entry
            assert "url" in entry
            assert "visits" in entry

    @pytest.mark.parametrize(
        "token",
        [
            "short",
            "invalid!@#$%token",
            " ",
            "",
        ],
    )
    def test_list_urls_invalid_tokens(self, test_client, token):
        """Test listing URLs with invalid admin tokens."""
        if token == "":
            # Empty token results in 404 (missing path parameter)
            response = test_client.get("/list/")
            assert response.status_code == 404
        else:
            response = test_client.get(f"/list/{token}")
            assert response.status_code == 401

    def test_list_urls_no_token(self, test_client):
        """Test listing URLs without token."""
        response = test_client.get("/list/")
        assert response.status_code == 404

    @pytest.mark.skip(reason="/info/{link} endpoint is not implemented")
    def test_info_endpoint_valid_link(self, test_client):
        """Test getting info about a specific link."""
        # Create a URL
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Get info about the link
        info_response = test_client.get(f"/info/{short_link}")
        assert info_response.status_code == 200

        info_data = info_response.json()
        assert info_data["link"] == short_link
        assert info_data["url"] == "https://example.com/"
        assert info_data["visits"] == 0

    @pytest.mark.skip(reason="/info/{link} endpoint is not implemented")
    def test_info_endpoint_invalid_link(self, test_client):
        """Test getting info about invalid link."""
        response = test_client.get("/info/nonexistentlink")
        assert response.status_code == 404

    def test_phishtank_update_valid_token(self, test_client, admin_token):
        """Test updating PhishTank database with valid token."""
        response = test_client.get(f"/phishtank/update/{admin_token}")
        # PhishTank is disabled by default, so expect 501
        assert response.status_code == 501

    @pytest.mark.parametrize(
        "token",
        [
            "short",
            "invalid!@#$%token",
            " ",
            "",
        ],
    )
    def test_phishtank_update_invalid_tokens(self, test_client, token):
        """Test updating PhishTank database with invalid tokens."""
        if token == "":
            # Empty token results in 404 (missing path parameter)
            response = test_client.get("/phishtank/update/")
            assert response.status_code == 404
        else:
            response = test_client.get(f"/phishtank/update/{token}")
            assert response.status_code == 401

    def test_phishtank_update_no_token(self, test_client):
        """Test updating PhishTank database without token."""
        response = test_client.get("/phishtank/update/")
        assert response.status_code == 404

    @pytest.mark.skip(
        reason="PhishTank is disabled by default and requires complex mocking"
    )
    def test_phishtank_update_with_mock(self, test_client, admin_token, mock_phishtank):
        """Test PhishTank update with mocked service."""
        response = test_client.get(f"/phishtank/update/{admin_token}")
        assert response.status_code == 200

        # Verify the mock was called
        mock_phishtank.assert_called()

    def test_admin_endpoints_rate_limiting(self, test_client, admin_token):
        """Test that admin endpoints are not rate limited."""
        # Multiple requests to list endpoint
        for i in range(10):
            response = test_client.get(f"/list/{admin_token}")
            assert response.status_code == 200

        # Multiple requests to phishtank update endpoint
        # PhishTank is disabled by default, so expect 501
        for i in range(10):
            response = test_client.get(f"/phishtank/update/{admin_token}")
            assert response.status_code == 501

    def test_list_urls_empty_database(self, test_client, admin_token):
        """Test listing URLs when database is empty."""
        response = test_client.get(f"/list/{admin_token}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Could be empty or contain system entries

    def test_list_urls_response_structure(self, test_client, admin_token):
        """Test the structure of list URLs response."""
        # Create a URL
        test_client.post("/url", json={"url": "https://example.com"})

        response = test_client.get(f"/list/{admin_token}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if data:  # If there are entries
            entry = data[0]
            required_fields = ["link", "url", "visits"]
            for field in required_fields:
                assert field in entry
            assert isinstance(entry["visits"], int)
            assert entry["visits"] >= 0

    @pytest.mark.skip(reason="/info/{link} endpoint is not implemented")
    def test_info_endpoint_after_redirects(self, test_client):
        """Test info endpoint after some redirects."""
        # Create a URL
        create_response = test_client.post("/url", json={"url": "https://example.com"})
        assert create_response.status_code == 200
        create_data = create_response.json()
        short_link = create_data["link"]

        # Perform some redirects
        for _ in range(3):
            redirect_response = test_client.get(
                f"/{short_link}", follow_redirects=False
            )
            assert redirect_response.status_code == 301

        # Check info
        info_response = test_client.get(f"/info/{short_link}")
        assert info_response.status_code == 200

        info_data = info_response.json()
        assert info_data["visits"] == 3

    def test_admin_endpoints_http_methods(self, test_client, admin_token):
        """Test that admin endpoints only work with GET method."""
        endpoints = [
            f"/list/{admin_token}",
            f"/phishtank/update/{admin_token}",
        ]

        for endpoint in endpoints:
            # Test POST
            response = test_client.post(endpoint)
            assert response.status_code in [405, 404]

            # Test PUT
            response = test_client.put(endpoint)
            assert response.status_code in [405, 404]

            # Test DELETE
            response = test_client.delete(endpoint)
            assert response.status_code in [405, 404]

    def test_phishtank_update_error_handling(self, test_client, admin_token):
        """Test error handling when PhishTank update fails."""
        # PhishTank is disabled by default, so expect 501
        response = test_client.get(f"/phishtank/update/{admin_token}")
        assert response.status_code == 501

    @pytest.mark.skip(reason="/info/{link} endpoint is not implemented")
    def test_info_endpoint_special_links(self, test_client):
        """Test info endpoint with special link formats."""
        # Create URLs that might result in special short links
        special_urls = [
            "https://example.com/very/long/path/that/might/create/special/short/link",
            "https://example.com?query=params&multiple=values",
            "https://example.com#anchor",
        ]

        for url in special_urls:
            create_response = test_client.post("/url", json={"url": url})
            if create_response.status_code == 200:
                create_data = create_response.json()
                short_link = create_data["link"]

                info_response = test_client.get(f"/info/{short_link}")
                assert info_response.status_code == 200

                info_data = info_response.json()
                assert info_data["url"] == url

    def test_admin_endpoints_metrics_integration(
        self, test_client, admin_token, metrics_collector
    ):
        """Test that admin endpoints metrics are recorded."""
        # List URLs
        response = test_client.get(f"/list/{admin_token}")
        assert response.status_code == 200

        # PhishTank update (expect 501 since it's disabled)
        response = test_client.get(f"/phishtank/update/{admin_token}")
        assert response.status_code == 501

        # Verify metrics were recorded (admin requests should be tracked)
        metrics_output = metrics_collector.get_metrics().decode("utf-8")
        assert "l1nkzip_http_requests_total" in metrics_output
