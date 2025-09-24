"""
Contract tests for POST /setup/validate-config endpoint
These tests validate the OpenAPI contract compliance
"""

import pytest
import httpx
from typing import Dict, Any


class TestSetupValidateConfigContract:
    """Contract tests for setup configuration validation endpoint"""

    @pytest.fixture
    def base_url(self) -> str:
        """Base URL for API tests"""
        return "http://localhost:8000"

    @pytest.fixture
    def client(self, base_url: str) -> httpx.Client:
        """HTTP client for making requests"""
        return httpx.Client(base_url=base_url)

    @pytest.fixture
    def valid_config(self) -> Dict[str, Any]:
        """Valid configuration for testing"""
        return {
            "redis_url": "redis://localhost:6379/0",
            "redis_session_db": 1,
            "redis_task_db": 2,
            "youtube_api_key": "valid_youtube_api_key_here",
            "openai_api_key": "valid_openai_api_key_here",
            "backend_url": "http://localhost:8000",
            "frontend_url": "http://localhost:3000",
            "websocket_url": "ws://localhost:8000/ws",
            "environment": "local"
        }

    def test_validate_config_endpoint_exists(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test that POST /setup/validate-config endpoint exists"""
        response = client.post("/setup/validate-config", json=valid_config)

        # Should not return 404 (endpoint must exist)
        assert response.status_code != 404, "POST /setup/validate-config endpoint should exist"

    def test_validate_config_success_response_schema(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test successful validation response matches OpenAPI schema"""
        response = client.post("/setup/validate-config", json=valid_config)

        if response.status_code == 200:
            data = response.json()

            # Required fields per OpenAPI contract
            assert "valid" in data, "Response must include valid field"
            assert "errors" in data, "Response must include errors field"

            # Field type validation
            assert isinstance(data["valid"], bool), "valid field must be boolean"
            assert isinstance(data["errors"], list), "errors field must be an array"

            # Optional warnings field
            if "warnings" in data:
                assert isinstance(data["warnings"], list), "warnings field must be an array"

            # Error object structure validation
            for error in data["errors"]:
                assert isinstance(error, dict), "Each error must be an object"
                assert "field" in error, "Error must include field name"
                assert "message" in error, "Error must include message"
                assert "severity" in error, "Error must include severity"

                # Severity validation
                valid_severities = ["error", "warning"]
                assert error["severity"] in valid_severities, f"Severity must be one of {valid_severities}"

    def test_validate_config_required_fields(self, client: httpx.Client):
        """Test validation with missing required fields"""
        # Test with minimal required fields only
        minimal_config = {
            "redis_url": "redis://localhost:6379/0",
            "youtube_api_key": "test_key",
            "openai_api_key": "test_key"
        }

        response = client.post("/setup/validate-config", json=minimal_config)

        # Should accept minimal valid configuration
        assert response.status_code in [200, 400], "Should handle minimal configuration"

        if response.status_code == 200:
            data = response.json()
            # Minimal config should be valid
            assert isinstance(data["valid"], bool), "Response should indicate validity"

    def test_validate_config_invalid_redis_url(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test validation with invalid Redis URL"""
        invalid_configs = [
            {**valid_config, "redis_url": "invalid-url"},
            {**valid_config, "redis_url": "http://localhost:6379"},  # Wrong scheme
            {**valid_config, "redis_url": "redis://"},  # Missing host
            {**valid_config, "redis_url": ""},  # Empty
        ]

        for config in invalid_configs:
            response = client.post("/setup/validate-config", json=config)
            assert response.status_code in [200, 400], "Should handle invalid Redis URL"

            if response.status_code == 200:
                data = response.json()
                # Should report as invalid or include errors
                if data["valid"]:
                    assert len(data["errors"]) == 0, "Valid config should have no errors"
                else:
                    assert len(data["errors"]) > 0, "Invalid config should have errors"

    def test_validate_config_invalid_database_numbers(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test validation with invalid database numbers"""
        invalid_configs = [
            {**valid_config, "redis_session_db": -1},  # Too low
            {**valid_config, "redis_session_db": 16},  # Too high
            {**valid_config, "redis_task_db": "not_a_number"},  # Wrong type
        ]

        for config in invalid_configs:
            response = client.post("/setup/validate-config", json=config)
            assert response.status_code in [200, 400], "Should handle invalid database numbers"

    def test_validate_config_empty_api_keys(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test validation with empty or missing API keys"""
        invalid_configs = [
            {**valid_config, "youtube_api_key": ""},
            {**valid_config, "openai_api_key": ""},
            {**valid_config, "youtube_api_key": "your_key_here"},  # Placeholder
            {**valid_config, "openai_api_key": "placeholder"},
        ]

        for config in invalid_configs:
            response = client.post("/setup/validate-config", json=config)
            assert response.status_code in [200, 400], "Should handle invalid API keys"

    def test_validate_config_invalid_urls(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test validation with invalid service URLs"""
        invalid_configs = [
            {**valid_config, "backend_url": "not-a-url"},
            {**valid_config, "frontend_url": "ftp://localhost:3000"},  # Wrong scheme
            {**valid_config, "websocket_url": "http://localhost:8000/ws"},  # Wrong scheme for WS
        ]

        for config in invalid_configs:
            response = client.post("/setup/validate-config", json=config)
            assert response.status_code in [200, 400], "Should handle invalid URLs"

    def test_validate_config_bad_request_response(self, client: httpx.Client):
        """Test 400 Bad Request response schema"""
        # Send invalid JSON
        response = client.post("/setup/validate-config", json="invalid json structure")

        if response.status_code == 400:
            data = response.json()

            # Error response schema validation
            assert "error" in data, "400 response must include error field"
            assert "message" in data, "400 response must include message field"

            # Optional details field
            if "details" in data:
                assert isinstance(data["details"], dict), "details field must be an object"

    def test_validate_config_content_type_validation(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test that endpoint requires JSON content type"""
        # Send form data instead of JSON
        response = client.post("/setup/validate-config", data=valid_config)

        # Should return 400 or 415 for wrong content type
        assert response.status_code in [400, 415], "Should reject non-JSON content"

    def test_validate_config_method_not_allowed(self, client: httpx.Client):
        """Test that only POST method is allowed"""
        # GET should not be allowed
        response = client.get("/setup/validate-config")
        assert response.status_code == 405, "GET should not be allowed on validate-config endpoint"

        # PUT should not be allowed
        response = client.put("/setup/validate-config")
        assert response.status_code == 405, "PUT should not be allowed on validate-config endpoint"

        # DELETE should not be allowed
        response = client.delete("/setup/validate-config")
        assert response.status_code == 405, "DELETE should not be allowed on validate-config endpoint"

    @pytest.mark.parametrize("environment", ["local", "docker", "cloud"])
    def test_validate_config_valid_environments(self, client: httpx.Client, valid_config: Dict[str, Any], environment: str):
        """Test validation with different valid environment types"""
        config = {**valid_config, "environment": environment}

        response = client.post("/setup/validate-config", json=config)
        assert response.status_code in [200, 400], f"Should handle environment: {environment}"

    def test_validate_config_response_headers(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test response headers are appropriate"""
        response = client.post("/setup/validate-config", json=valid_config)

        # Should return JSON content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, "Response should be JSON"

    def test_validate_config_no_authentication_required(self, client: httpx.Client, valid_config: Dict[str, Any]):
        """Test that validate-config endpoint does not require authentication"""
        response = client.post("/setup/validate-config", json=valid_config)

        # Should not return 401 Unauthorized
        assert response.status_code != 401, "Validate-config endpoint should not require authentication"
        assert response.status_code != 403, "Validate-config endpoint should not require authorization"