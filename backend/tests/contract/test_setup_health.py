"""
Contract tests for GET /setup/health endpoint
These tests validate the OpenAPI contract compliance
"""

import pytest
import httpx
from typing import Dict, Any


class TestSetupHealthContract:
    """Contract tests for setup health endpoint"""

    @pytest.fixture
    def base_url(self) -> str:
        """Base URL for API tests"""
        return "http://localhost:8000"

    @pytest.fixture
    def client(self, base_url: str) -> httpx.Client:
        """HTTP client for making requests"""
        return httpx.Client(base_url=base_url)

    def test_health_endpoint_exists(self, client: httpx.Client):
        """Test that GET /setup/health endpoint exists"""
        response = client.get("/setup/health")

        # Should not return 404 (endpoint must exist)
        assert response.status_code != 404, "GET /setup/health endpoint should exist"

    def test_health_success_response_schema(self, client: httpx.Client):
        """Test successful health check response matches OpenAPI schema"""
        response = client.get("/setup/health")

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields per OpenAPI contract
            assert "overall_status" in data, "Response must include overall_status"
            assert "services" in data, "Response must include services"
            assert "timestamp" in data, "Response must include timestamp"

            # overall_status validation
            valid_statuses = ["healthy", "degraded", "unhealthy"]
            assert data["overall_status"] in valid_statuses, f"overall_status must be one of {valid_statuses}"

            # services field validation
            services = data["services"]
            assert isinstance(services, dict), "services must be an object"

            # Required service checks
            required_services = ["redis", "backend", "frontend", "websocket"]
            for service in required_services:
                assert service in services, f"Service '{service}' must be included in health check"

                service_data = services[service]
                assert "status" in service_data, f"Service '{service}' must have status field"
                assert "last_check" in service_data, f"Service '{service}' must have last_check field"

                # Service status validation
                service_statuses = ["healthy", "unhealthy", "starting", "stopped"]
                assert service_data["status"] in service_statuses, f"Service status must be one of {service_statuses}"

            # timestamp validation (should be ISO format)
            timestamp = data["timestamp"]
            assert isinstance(timestamp, str), "timestamp must be a string"
            # Basic ISO format check (will validate datetime parsing in integration tests)
            assert "T" in timestamp or " " in timestamp, "timestamp should be in ISO format"

    def test_health_service_unavailable_response(self, client: httpx.Client):
        """Test 503 Service Unavailable response matches schema"""
        response = client.get("/setup/health")

        if response.status_code == 503:
            data = response.json()

            # Error response schema validation
            assert "error" in data, "503 response must include error field"
            assert "message" in data, "503 response must include message field"

            # Optional details field
            if "details" in data:
                assert isinstance(data["details"], dict), "details field must be an object"

    def test_health_response_headers(self, client: httpx.Client):
        """Test response headers are appropriate"""
        response = client.get("/setup/health")

        # Should return JSON content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, "Response should be JSON"

    def test_health_method_not_allowed(self, client: httpx.Client):
        """Test that only GET method is allowed"""
        # POST should not be allowed
        response = client.post("/setup/health")
        assert response.status_code == 405, "POST should not be allowed on health endpoint"

        # PUT should not be allowed
        response = client.put("/setup/health")
        assert response.status_code == 405, "PUT should not be allowed on health endpoint"

        # DELETE should not be allowed
        response = client.delete("/setup/health")
        assert response.status_code == 405, "DELETE should not be allowed on health endpoint"

    def test_health_no_authentication_required(self, client: httpx.Client):
        """Test that health endpoint does not require authentication"""
        # Health endpoint should be publicly accessible
        response = client.get("/setup/health")

        # Should not return 401 Unauthorized
        assert response.status_code != 401, "Health endpoint should not require authentication"
        assert response.status_code != 403, "Health endpoint should not require authorization"

    def test_health_response_performance(self, client: httpx.Client):
        """Test that health endpoint responds within reasonable time"""
        import time

        start_time = time.time()
        response = client.get("/setup/health")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Health check should respond within 5 seconds
        assert response_time < 5000, f"Health endpoint should respond within 5000ms, took {response_time:.2f}ms"

    @pytest.mark.parametrize("service_name", ["redis", "backend", "frontend", "websocket"])
    def test_health_service_status_fields(self, client: httpx.Client, service_name: str):
        """Test each service has required status fields"""
        response = client.get("/setup/health")

        if response.status_code == 200:
            data = response.json()
            services = data.get("services", {})

            if service_name in services:
                service = services[service_name]

                # Required fields
                assert "status" in service, f"{service_name} must have status field"
                assert "last_check" in service, f"{service_name} must have last_check field"

                # Optional fields that should be present when available
                optional_fields = ["response_time_ms", "error_message", "connection_details"]
                for field in optional_fields:
                    if field in service:
                        # Validate field types when present
                        if field == "response_time_ms":
                            assert isinstance(service[field], (int, float)), f"{field} must be numeric"
                        elif field == "error_message":
                            assert isinstance(service[field], str), f"{field} must be string"
                        elif field == "connection_details":
                            assert isinstance(service[field], dict), f"{field} must be object"