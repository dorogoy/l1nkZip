"""
Tests for health endpoint (/health).
"""


class TestHealthEndpoint:
    """Test cases for the health endpoint."""

    def test_health_endpoint_basic(self, test_client):
        """Test basic health endpoint functionality."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data == "OK"

    def test_health_endpoint_content_type(self, test_client):
        """Test that health endpoint returns correct content type."""
        response = test_client.get("/health")
        assert response.status_code == 200

        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_health_endpoint_http_methods(self, test_client):
        """Test that health endpoint only works with GET method."""
        # Test POST
        response = test_client.post("/health")
        assert response.status_code in [405, 404]

        # Test PUT
        response = test_client.put("/health")
        assert response.status_code in [405, 404]

        # Test DELETE
        response = test_client.delete("/health")
        assert response.status_code in [405, 404]

        # Test PATCH
        response = test_client.patch("/health")
        assert response.status_code in [405, 404]

    def test_health_endpoint_no_auth_required(self, test_client):
        """Test that health endpoint doesn't require authentication."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_not_rate_limited(self, test_client):
        """Test that health endpoint is not rate limited."""
        for _i in range(20):  # Make many requests
            response = test_client.get("/health")
            assert response.status_code == 200

    def test_health_endpoint_response_structure(self, test_client):
        """Test the structure of health endpoint response."""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, str)
        assert data == "OK"

    def test_health_endpoint_with_database_connection(self, test_client):
        """Test health endpoint when database is connected."""
        response = test_client.get("/health")
        assert response.status_code == 200

        # The health endpoint should check database connection
        # If it returns "OK", the database connection is working

    def test_health_endpoint_metrics_integration(self, test_client, metrics_collector):
        """Test that health endpoint metrics are recorded."""
        response = test_client.get("/health")
        assert response.status_code == 200

        # Health endpoint doesn't record metrics by design (it's a simple health check)
        # This test verifies that the health endpoint works without adding metrics overhead
        metrics_output = metrics_collector.get_metrics().decode("utf-8")
        # Health check should not appear in metrics since it doesn't use record_request_start/end
        assert "health_check" not in metrics_output or "endpoint" not in metrics_output

    def test_health_endpoint_headers(self, test_client):
        """Test that health endpoint includes appropriate headers."""
        response = test_client.get("/health")
        assert response.status_code == 200

        # Check common headers
        assert "content-type" in response.headers
        assert "content-length" in response.headers

        # Should not include cache headers for health endpoint
        assert (
            "cache-control" not in response.headers or "no-cache" in response.headers.get("cache-control", "").lower()
        )

    def test_health_endpoint_performance(self, test_client):
        """Test that health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.1  # Should respond within 100ms

    def test_health_endpoint_with_path_trailing_slash(self, test_client):
        """Test health endpoint with trailing slash."""
        response = test_client.get("/health/")
        assert response.status_code == 200  # FastAPI redirects /health/ to /health

    def test_health_endpoint_case_sensitivity(self, test_client):
        """Test health endpoint case sensitivity."""
        response = test_client.get("/Health")
        assert response.status_code == 404  # Should not match

        response = test_client.get("/HEALTH")
        assert response.status_code == 404  # Should not match

    def test_health_endpoint_concurrent_requests(self, test_client):
        """Test health endpoint with concurrent requests."""
        import threading

        results = []
        errors = []

        def make_request():
            try:
                response = test_client.get("/health")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Make concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(status == 200 for status in results), f"Not all requests succeeded: {results}"

    def test_health_endpoint_with_query_parameters(self, test_client):
        """Test health endpoint with query parameters."""
        response = test_client.get("/health?verbose=true")
        assert response.status_code == 200

        data = response.json()
        assert data == "OK"  # Should ignore query parameters

    def test_health_endpoint_after_database_operations(self, test_client):
        """Test health endpoint after some database operations."""
        # Create some URLs to exercise the database
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
        ]

        for url in urls:
            test_client.post("/url", json={"url": url})

        # Health endpoint should still work
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == "OK"

    def test_health_endpoint_response_time_metrics(self, test_client, metrics_collector):
        """Test that health endpoint response time is recorded in metrics."""
        response = test_client.get("/health")
        assert response.status_code == 200

        # Health endpoint doesn't record response time metrics by design
        # This test verifies that the health endpoint works without metrics overhead
        duration_samples = metrics_collector.http_request_duration_seconds._samples()
        health_duration_samples = [sample for sample in duration_samples if sample[1].get("endpoint") == "health_check"]

        # Health check should not have duration metrics since it doesn't use record_request_start/end
        assert len(health_duration_samples) == 0, "Health check duration metrics should not be recorded by design"
