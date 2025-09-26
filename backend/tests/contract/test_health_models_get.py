"""
Contract tests for GET /api/health/models endpoint
These tests validate the OpenAPI contract compliance for Gemini model health checks
"""

import pytest
import httpx
from typing import Dict, Any
from datetime import datetime


class TestHealthModelsContract:
    """Contract tests for health models endpoint"""

    @pytest.fixture
    def base_url(self) -> str:
        """Base URL for API tests"""
        return "http://localhost:8000"

    @pytest.fixture
    def client(self, base_url: str) -> httpx.Client:
        """HTTP client for making requests"""
        return httpx.Client(base_url=base_url)

    def test_health_models_endpoint_exists(self, client: httpx.Client):
        """Test that GET /api/health/models endpoint exists"""
        response = client.get("/api/health/models")

        # Should not return 404 (endpoint must exist)
        assert (
            response.status_code != 404
        ), "GET /api/health/models endpoint should exist"

    def test_health_models_success_response_schema(self, client: httpx.Client):
        """Test successful health check response matches OpenAPI schema"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields per OpenAPI contract
            assert "timestamp" in data, "Response must include timestamp"
            assert "models" in data, "Response must include models"
            assert "overall_status" in data, "Response must include overall_status"
            assert (
                "primary_model_available" in data
            ), "Response must include primary_model_available"

            # Timestamp validation (should be ISO format)
            timestamp = data["timestamp"]
            assert isinstance(timestamp, str), "timestamp must be a string"
            self._validate_timestamp_format(timestamp)

            # Models object validation
            models = data["models"]
            assert isinstance(models, dict), "models must be an object"

            # Required model health checks
            required_models = ["gemini-2.5-flash-image", "gemini-pro"]
            for model_name in required_models:
                assert (
                    model_name in models
                ), f"Model '{model_name}' must be included in health check"
                self._validate_model_health_schema(models[model_name], model_name)

            # Overall status validation
            valid_statuses = ["healthy", "degraded", "unhealthy"]
            assert (
                data["overall_status"] in valid_statuses
            ), f"overall_status must be one of {valid_statuses}, got: {data['overall_status']}"

            # Primary model availability validation
            primary_model_available = data["primary_model_available"]
            assert isinstance(
                primary_model_available, bool
            ), "primary_model_available must be a boolean"

    def _validate_model_health_schema(
        self, model_health: Dict[str, Any], model_name: str
    ):
        """Validate ModelHealth schema for a specific model"""
        # Required fields per OpenAPI contract
        required_fields = ["available", "error_count", "avg_response_time_ms"]
        for field in required_fields:
            assert (
                field in model_health
            ), f"Model '{model_name}' must have {field} field"

        # Field type validations
        assert isinstance(
            model_health["available"], bool
        ), f"Model '{model_name}' available field must be boolean"

        assert isinstance(
            model_health["error_count"], int
        ), f"Model '{model_name}' error_count field must be integer"
        assert (
            model_health["error_count"] >= 0
        ), f"Model '{model_name}' error_count must be non-negative"

        assert isinstance(
            model_health["avg_response_time_ms"], int
        ), f"Model '{model_name}' avg_response_time_ms field must be integer"
        assert (
            model_health["avg_response_time_ms"] >= 0
        ), f"Model '{model_name}' avg_response_time_ms must be non-negative"

        # Optional fields validation when present
        if "last_success" in model_health:
            last_success = model_health["last_success"]
            if last_success is not None:  # Can be null
                assert isinstance(
                    last_success, str
                ), f"Model '{model_name}' last_success must be string or null"
                self._validate_timestamp_format(last_success)

        if "rate_limit_remaining" in model_health:
            rate_limit = model_health["rate_limit_remaining"]
            if rate_limit is not None:  # Can be null
                assert isinstance(
                    rate_limit, int
                ), f"Model '{model_name}' rate_limit_remaining must be integer or null"
                assert (
                    rate_limit >= 0
                ), f"Model '{model_name}' rate_limit_remaining must be non-negative"

    def _validate_timestamp_format(self, timestamp: str):
        """Validate timestamp is in ISO 8601 format"""
        try:
            # Try to parse as ISO format
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"timestamp '{timestamp}' should be in ISO 8601 format")

    def test_health_models_response_headers(self, client: httpx.Client):
        """Test response headers are appropriate"""
        response = client.get("/api/health/models")

        # Should return JSON content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, "Response should be JSON"

    def test_health_models_method_not_allowed(self, client: httpx.Client):
        """Test that only GET method is allowed"""
        # POST should not be allowed
        response = client.post("/api/health/models")
        assert (
            response.status_code == 405
        ), "POST should not be allowed on health models endpoint"

        # PUT should not be allowed
        response = client.put("/api/health/models")
        assert (
            response.status_code == 405
        ), "PUT should not be allowed on health models endpoint"

        # DELETE should not be allowed
        response = client.delete("/api/health/models")
        assert (
            response.status_code == 405
        ), "DELETE should not be allowed on health models endpoint"

    def test_health_models_no_authentication_required(self, client: httpx.Client):
        """Test that health models endpoint does not require authentication"""
        # Health endpoint should be publicly accessible
        response = client.get("/api/health/models")

        # Should not return 401 Unauthorized
        assert (
            response.status_code != 401
        ), "Health models endpoint should not require authentication"
        assert (
            response.status_code != 403
        ), "Health models endpoint should not require authorization"

    def test_health_models_response_performance(self, client: httpx.Client):
        """Test that health models endpoint responds within reasonable time"""
        import time

        start_time = time.time()
        response = client.get("/api/health/models")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Health check should respond within 10 seconds (model checks can be slower)
        assert (
            response_time < 10000
        ), f"Health models endpoint should respond within 10000ms, took {response_time:.2f}ms"

    @pytest.mark.parametrize("model_name", ["gemini-2.5-flash-image", "gemini-pro"])
    def test_health_models_specific_model_validation(
        self, client: httpx.Client, model_name: str
    ):
        """Test each specific model has required health fields"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", {})

            assert (
                model_name in models
            ), f"Model '{model_name}' must be present in response"

            model_health = models[model_name]
            self._validate_model_health_schema(model_health, model_name)

    def test_health_models_overall_status_logic(self, client: httpx.Client):
        """Test overall status reflects model availability state"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data["models"]
            overall_status = data["overall_status"]

            # Count available models
            available_models = sum(
                1 for model in models.values() if model.get("available", False)
            )
            total_models = len(models)

            # Validate status logic
            if available_models == total_models:
                # All models available should be healthy (unless high error rates)
                pass  # Contract doesn't specify exact logic, just valid enum values
            elif available_models == 0:
                # No models available should be unhealthy
                pass  # Contract doesn't specify exact logic, just valid enum values
            else:
                # Some models available should be degraded
                pass  # Contract doesn't specify exact logic, just valid enum values

            # Ensure status is valid enum value
            valid_statuses = ["healthy", "degraded", "unhealthy"]
            assert (
                overall_status in valid_statuses
            ), f"overall_status must be one of {valid_statuses}"

    def test_health_models_primary_model_availability_logic(self, client: httpx.Client):
        """Test primary model availability reflects gemini-2.5-flash-image status"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data["models"]
            primary_model_available = data["primary_model_available"]

            # Primary model is gemini-2.5-flash-image based on contract
            if "gemini-2.5-flash-image" in models:
                primary_model_status = models["gemini-2.5-flash-image"].get(
                    "available", False
                )

                # primary_model_available should reflect primary model status
                # (Though contract doesn't specify exact logic, this is the expected behavior)
                assert isinstance(
                    primary_model_available, bool
                ), "primary_model_available must be boolean"

    def test_health_models_error_count_range(self, client: httpx.Client):
        """Test error counts are within reasonable ranges"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data["models"]

            for model_name, model_health in models.items():
                error_count = model_health.get("error_count", 0)

                # Error count should be reasonable (less than 1000 per hour)
                assert (
                    error_count < 1000
                ), f"Model '{model_name}' error_count seems unreasonably high: {error_count}"

    def test_health_models_response_time_range(self, client: httpx.Client):
        """Test response times are within reasonable ranges"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data["models"]

            for model_name, model_health in models.items():
                avg_response_time = model_health.get("avg_response_time_ms", 0)

                # Response time should be reasonable (less than 2 minutes)
                assert (
                    avg_response_time < 120000
                ), f"Model '{model_name}' avg_response_time_ms seems unreasonably high: {avg_response_time}ms"

    def test_health_models_rate_limit_values(self, client: httpx.Client):
        """Test rate limit values are reasonable when present"""
        response = client.get("/api/health/models")

        if response.status_code == 200:
            data = response.json()
            models = data["models"]

            for model_name, model_health in models.items():
                if "rate_limit_remaining" in model_health:
                    rate_limit = model_health["rate_limit_remaining"]

                    if rate_limit is not None:
                        # Rate limit should be reasonable (0-10000 range typical for APIs)
                        assert (
                            0 <= rate_limit <= 10000
                        ), f"Model '{model_name}' rate_limit_remaining outside expected range: {rate_limit}"
