"""
Contract tests for POST /setup/test-connectivity endpoint
These tests validate the OpenAPI contract compliance
"""

import pytest
import httpx
from typing import Dict, Any, List


class TestSetupConnectivityContract:
    """Contract tests for setup connectivity testing endpoint"""

    @pytest.fixture
    def base_url(self) -> str:
        """Base URL for API tests"""
        return "http://localhost:8000"

    @pytest.fixture
    def client(self, base_url: str) -> httpx.Client:
        """HTTP client for making requests"""
        return httpx.Client(base_url=base_url)

    @pytest.fixture
    def valid_request(self) -> Dict[str, Any]:
        """Valid connectivity test request"""
        return {
            "services": ["redis", "youtube_api", "openai_api"],
            "timeout_seconds": 10
        }

    def test_connectivity_endpoint_exists(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that POST /setup/test-connectivity endpoint exists"""
        response = client.post("/setup/test-connectivity", json=valid_request)

        # Should not return 404 (endpoint must exist)
        assert response.status_code != 404, "POST /setup/test-connectivity endpoint should exist"

    def test_connectivity_success_response_schema(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test successful connectivity response matches OpenAPI schema"""
        response = client.post("/setup/test-connectivity", json=valid_request)

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields per OpenAPI contract
            assert "results" in data, "Response must include results field"
            assert "overall_success" in data, "Response must include overall_success field"

            # Field type validation
            assert isinstance(data["results"], dict), "results field must be an object"
            assert isinstance(data["overall_success"], bool), "overall_success field must be boolean"

            # Results validation for each requested service
            results = data["results"]
            requested_services = valid_request["services"]

            for service in requested_services:
                assert service in results, f"Results must include {service}"

                service_result = results[service]
                assert isinstance(service_result, dict), f"{service} result must be an object"

                # Required fields for each service result
                assert "connected" in service_result, f"{service} must have connected field"
                assert "response_time_ms" in service_result, f"{service} must have response_time_ms field"

                # Field type validation
                assert isinstance(service_result["connected"], bool), f"{service} connected must be boolean"
                assert isinstance(service_result["response_time_ms"], (int, float)), f"{service} response_time_ms must be numeric"

                # Optional fields
                if "error" in service_result:
                    assert isinstance(service_result["error"], str), f"{service} error must be string"

                if "details" in service_result:
                    assert isinstance(service_result["details"], dict), f"{service} details must be object"

    def test_connectivity_required_services_field(self, client: httpx.Client):
        """Test that services field is required"""
        # Request without services field
        invalid_request = {
            "timeout_seconds": 10
        }

        response = client.post("/setup/test-connectivity", json=invalid_request)
        assert response.status_code == 400, "Should return 400 when services field is missing"

    def test_connectivity_valid_services(self, client: httpx.Client):
        """Test with valid service names"""
        valid_services = [
            ["redis"],
            ["youtube_api"],
            ["openai_api"],
            ["all"],
            ["redis", "youtube_api"],
            ["redis", "youtube_api", "openai_api"],
        ]

        for services in valid_services:
            request = {"services": services}
            response = client.post("/setup/test-connectivity", json=request)

            # Should accept valid service combinations
            assert response.status_code in [200, 400], f"Should handle services: {services}"

    def test_connectivity_invalid_services(self, client: httpx.Client):
        """Test with invalid service names"""
        invalid_requests = [
            {"services": ["invalid_service"]},
            {"services": ["redis", "unknown_service"]},
            {"services": []},  # Empty array
            {"services": "not_an_array"},  # Wrong type
        ]

        for request in invalid_requests:
            response = client.post("/setup/test-connectivity", json=request)
            assert response.status_code == 400, f"Should reject invalid services: {request['services']}"

    def test_connectivity_timeout_validation(self, client: httpx.Client):
        """Test timeout_seconds field validation"""
        # Valid timeout values
        valid_timeouts = [1, 10, 30, 60]

        for timeout in valid_timeouts:
            request = {
                "services": ["redis"],
                "timeout_seconds": timeout
            }
            response = client.post("/setup/test-connectivity", json=request)
            assert response.status_code in [200, 400], f"Should handle timeout: {timeout}"

        # Invalid timeout values
        invalid_timeouts = [0, -1, 61, 100, "not_a_number"]

        for timeout in invalid_timeouts:
            request = {
                "services": ["redis"],
                "timeout_seconds": timeout
            }
            response = client.post("/setup/test-connectivity", json=request)
            assert response.status_code == 400, f"Should reject invalid timeout: {timeout}"

    def test_connectivity_default_timeout(self, client: httpx.Client):
        """Test default timeout behavior"""
        # Request without timeout_seconds (should use default)
        request = {
            "services": ["redis"]
        }

        response = client.post("/setup/test-connectivity", json=request)
        assert response.status_code in [200, 400], "Should handle request without timeout"

    def test_connectivity_all_services_option(self, client: httpx.Client):
        """Test 'all' services option"""
        request = {
            "services": ["all"],
            "timeout_seconds": 15
        }

        response = client.post("/setup/test-connectivity", json=request)

        if response.status_code == 200:
            data = response.json()
            results = data["results"]

            # When 'all' is specified, should test standard services
            expected_services = ["redis", "youtube_api", "openai_api"]

            for service in expected_services:
                # At least some services should be tested when 'all' is used
                # (Implementation may decide which services to include)
                pass  # Specific validation depends on implementation

    def test_connectivity_bad_request_response(self, client: httpx.Client):
        """Test 400 Bad Request response schema"""
        # Send invalid JSON structure
        response = client.post("/setup/test-connectivity", json="invalid")

        if response.status_code == 400:
            data = response.json()

            # Error response schema validation
            assert "error" in data, "400 response must include error field"
            assert "message" in data, "400 response must include message field"

            # Optional details field
            if "details" in data:
                assert isinstance(data["details"], dict), "details field must be an object"

    def test_connectivity_method_not_allowed(self, client: httpx.Client):
        """Test that only POST method is allowed"""
        # GET should not be allowed
        response = client.get("/setup/test-connectivity")
        assert response.status_code == 405, "GET should not be allowed on test-connectivity endpoint"

        # PUT should not be allowed
        response = client.put("/setup/test-connectivity")
        assert response.status_code == 405, "PUT should not be allowed on test-connectivity endpoint"

        # DELETE should not be allowed
        response = client.delete("/setup/test-connectivity")
        assert response.status_code == 405, "DELETE should not be allowed on test-connectivity endpoint"

    def test_connectivity_content_type_validation(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that endpoint requires JSON content type"""
        # Send form data instead of JSON
        response = client.post("/setup/test-connectivity", data=valid_request)

        # Should return 400 or 415 for wrong content type
        assert response.status_code in [400, 415], "Should reject non-JSON content"

    def test_connectivity_response_headers(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test response headers are appropriate"""
        response = client.post("/setup/test-connectivity", json=valid_request)

        # Should return JSON content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, "Response should be JSON"

    def test_connectivity_no_authentication_required(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that connectivity endpoint does not require authentication"""
        response = client.post("/setup/test-connectivity", json=valid_request)

        # Should not return 401 Unauthorized
        assert response.status_code != 401, "Connectivity endpoint should not require authentication"
        assert response.status_code != 403, "Connectivity endpoint should not require authorization"

    @pytest.mark.parametrize("service", ["redis", "youtube_api", "openai_api"])
    def test_connectivity_individual_service_results(self, client: httpx.Client, service: str):
        """Test connectivity testing for individual services"""
        request = {
            "services": [service],
            "timeout_seconds": 5
        }

        response = client.post("/setup/test-connectivity", json=request)

        if response.status_code == 200:
            data = response.json()
            results = data["results"]

            assert service in results, f"Results should include {service}"

            service_result = results[service]
            assert "connected" in service_result, f"{service} should have connection status"
            assert "response_time_ms" in service_result, f"{service} should have response time"

            # Response time should be reasonable (not negative)
            assert service_result["response_time_ms"] >= 0, f"{service} response time should be non-negative"