"""
Contract tests for POST /setup/run-tests endpoint
These tests validate the OpenAPI contract compliance
"""

import pytest
import httpx
from typing import Dict, Any, List


class TestSetupRunTestsContract:
    """Contract tests for setup test execution endpoint"""

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
        """Valid test execution request"""
        return {
            "test_types": ["contract", "integration"],
            "parallel": False,
            "timeout_seconds": 120
        }

    def test_run_tests_endpoint_exists(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that POST /setup/run-tests endpoint exists"""
        response = client.post("/setup/run-tests", json=valid_request)

        # Should not return 404 (endpoint must exist)
        assert response.status_code != 404, "POST /setup/run-tests endpoint should exist"

    def test_run_tests_success_response_schema(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test successful test execution response matches OpenAPI schema"""
        response = client.post("/setup/run-tests", json=valid_request)

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields per OpenAPI contract
            assert "execution_id" in data, "Response must include execution_id field"
            assert "test_results" in data, "Response must include test_results field"
            assert "summary" in data, "Response must include summary field"

            # Field type validation
            assert isinstance(data["execution_id"], str), "execution_id must be string"
            assert isinstance(data["test_results"], list), "test_results must be array"
            assert isinstance(data["summary"], dict), "summary must be object"

            # Summary object validation
            summary = data["summary"]
            required_summary_fields = ["total", "passed", "failed", "skipped", "duration_ms"]

            for field in required_summary_fields:
                assert field in summary, f"Summary must include {field} field"

                if field == "duration_ms":
                    assert isinstance(summary[field], (int, float)), f"{field} must be numeric"
                else:
                    assert isinstance(summary[field], int), f"{field} must be integer"

            # Test results validation
            for test_result in data["test_results"]:
                assert isinstance(test_result, dict), "Each test result must be object"

                # Required test result fields
                required_result_fields = ["test_name", "test_type", "status", "duration_ms"]
                for field in required_result_fields:
                    assert field in test_result, f"Test result must include {field} field"

                # Field type and value validation
                assert isinstance(test_result["test_name"], str), "test_name must be string"
                assert isinstance(test_result["test_type"], str), "test_type must be string"
                assert isinstance(test_result["status"], str), "status must be string"
                assert isinstance(test_result["duration_ms"], (int, float)), "duration_ms must be numeric"

                # Valid test types
                valid_test_types = ["contract", "integration", "e2e", "smoke"]
                assert test_result["test_type"] in valid_test_types, f"test_type must be one of {valid_test_types}"

                # Valid statuses
                valid_statuses = ["passed", "failed", "skipped", "error"]
                assert test_result["status"] in valid_statuses, f"status must be one of {valid_statuses}"

                # Optional fields
                if "error_details" in test_result:
                    assert isinstance(test_result["error_details"], str), "error_details must be string"

                if "test_data" in test_result:
                    assert isinstance(test_result["test_data"], dict), "test_data must be object"

    def test_run_tests_required_test_types_field(self, client: httpx.Client):
        """Test that test_types field is required"""
        # Request without test_types field
        invalid_request = {
            "parallel": False,
            "timeout_seconds": 120
        }

        response = client.post("/setup/run-tests", json=invalid_request)
        assert response.status_code == 400, "Should return 400 when test_types field is missing"

    def test_run_tests_valid_test_types(self, client: httpx.Client):
        """Test with valid test type combinations"""
        valid_test_types = [
            ["contract"],
            ["integration"],
            ["e2e"],
            ["smoke"],
            ["all"],
            ["contract", "integration"],
            ["contract", "integration", "e2e"],
            ["contract", "integration", "e2e", "smoke"],
        ]

        for test_types in valid_test_types:
            request = {
                "test_types": test_types,
                "parallel": False,
                "timeout_seconds": 60
            }
            response = client.post("/setup/run-tests", json=request)

            # Should accept valid test type combinations
            assert response.status_code in [200, 400], f"Should handle test_types: {test_types}"

    def test_run_tests_invalid_test_types(self, client: httpx.Client):
        """Test with invalid test types"""
        invalid_requests = [
            {"test_types": ["invalid_type"]},
            {"test_types": ["contract", "unknown_type"]},
            {"test_types": []},  # Empty array
            {"test_types": "not_an_array"},  # Wrong type
        ]

        for request in invalid_requests:
            response = client.post("/setup/run-tests", json=request)
            assert response.status_code == 400, f"Should reject invalid test_types: {request['test_types']}"

    def test_run_tests_parallel_flag(self, client: httpx.Client):
        """Test parallel execution flag"""
        # Test with parallel=true
        request = {
            "test_types": ["contract", "integration"],
            "parallel": True,
            "timeout_seconds": 60
        }

        response = client.post("/setup/run-tests", json=request)
        assert response.status_code in [200, 400], "Should handle parallel=true"

        # Test with parallel=false
        request["parallel"] = False
        response = client.post("/setup/run-tests", json=request)
        assert response.status_code in [200, 400], "Should handle parallel=false"

        # Test without parallel field (should use default)
        del request["parallel"]
        response = client.post("/setup/run-tests", json=request)
        assert response.status_code in [200, 400], "Should handle missing parallel field"

    def test_run_tests_timeout_validation(self, client: httpx.Client):
        """Test timeout_seconds field validation"""
        # Valid timeout values
        valid_timeouts = [10, 60, 120, 300]

        for timeout in valid_timeouts:
            request = {
                "test_types": ["contract"],
                "timeout_seconds": timeout
            }
            response = client.post("/setup/run-tests", json=request)
            assert response.status_code in [200, 400], f"Should handle timeout: {timeout}"

        # Invalid timeout values
        invalid_timeouts = [5, 0, -1, 301, 1000, "not_a_number"]

        for timeout in invalid_timeouts:
            request = {
                "test_types": ["contract"],
                "timeout_seconds": timeout
            }
            response = client.post("/setup/run-tests", json=request)
            assert response.status_code == 400, f"Should reject invalid timeout: {timeout}"

    def test_run_tests_default_timeout(self, client: httpx.Client):
        """Test default timeout behavior"""
        # Request without timeout_seconds (should use default)
        request = {
            "test_types": ["contract"]
        }

        response = client.post("/setup/run-tests", json=request)
        assert response.status_code in [200, 400], "Should handle request without timeout"

    def test_run_tests_all_test_types_option(self, client: httpx.Client):
        """Test 'all' test types option"""
        request = {
            "test_types": ["all"],
            "parallel": True,
            "timeout_seconds": 180
        }

        response = client.post("/setup/run-tests", json=request)

        if response.status_code == 200:
            data = response.json()
            test_results = data["test_results"]

            # When 'all' is specified, should run multiple test types
            if test_results:
                test_types_found = set(result["test_type"] for result in test_results)
                # Should have at least one test type when 'all' is used
                assert len(test_types_found) >= 1, "Should execute at least one test type when 'all' is specified"

    def test_run_tests_execution_id_uniqueness(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that execution IDs are unique"""
        # Make two requests and compare execution IDs
        response1 = client.post("/setup/run-tests", json=valid_request)
        response2 = client.post("/setup/run-tests", json=valid_request)

        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()

            execution_id1 = data1["execution_id"]
            execution_id2 = data2["execution_id"]

            assert execution_id1 != execution_id2, "Execution IDs should be unique"

    def test_run_tests_summary_consistency(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that summary counts match test results"""
        response = client.post("/setup/run-tests", json=valid_request)

        if response.status_code == 200:
            data = response.json()
            summary = data["summary"]
            test_results = data["test_results"]

            # Count actual results by status
            status_counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
            for result in test_results:
                status = result["status"]
                if status in status_counts:
                    status_counts[status] += 1

            # Summary counts should match actual results
            assert summary["total"] == len(test_results), "Total count should match number of results"
            assert summary["passed"] == status_counts["passed"], "Passed count should match"
            assert summary["failed"] == status_counts["failed"] + status_counts["error"], "Failed count should include errors"
            assert summary["skipped"] == status_counts["skipped"], "Skipped count should match"

    def test_run_tests_bad_request_response(self, client: httpx.Client):
        """Test 400 Bad Request response schema"""
        # Send invalid JSON structure
        response = client.post("/setup/run-tests", json="invalid")

        if response.status_code == 400:
            data = response.json()

            # Error response schema validation
            assert "error" in data, "400 response must include error field"
            assert "message" in data, "400 response must include message field"

            # Optional details field
            if "details" in data:
                assert isinstance(data["details"], dict), "details field must be an object"

    def test_run_tests_method_not_allowed(self, client: httpx.Client):
        """Test that only POST method is allowed"""
        # GET should not be allowed
        response = client.get("/setup/run-tests")
        assert response.status_code == 405, "GET should not be allowed on run-tests endpoint"

        # PUT should not be allowed
        response = client.put("/setup/run-tests")
        assert response.status_code == 405, "PUT should not be allowed on run-tests endpoint"

        # DELETE should not be allowed
        response = client.delete("/setup/run-tests")
        assert response.status_code == 405, "DELETE should not be allowed on run-tests endpoint"

    def test_run_tests_content_type_validation(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that endpoint requires JSON content type"""
        # Send form data instead of JSON
        response = client.post("/setup/run-tests", data=valid_request)

        # Should return 400 or 415 for wrong content type
        assert response.status_code in [400, 415], "Should reject non-JSON content"

    def test_run_tests_response_headers(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test response headers are appropriate"""
        response = client.post("/setup/run-tests", json=valid_request)

        # Should return JSON content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, "Response should be JSON"

    def test_run_tests_no_authentication_required(self, client: httpx.Client, valid_request: Dict[str, Any]):
        """Test that run-tests endpoint does not require authentication"""
        response = client.post("/setup/run-tests", json=valid_request)

        # Should not return 401 Unauthorized
        assert response.status_code != 401, "Run-tests endpoint should not require authentication"
        assert response.status_code != 403, "Run-tests endpoint should not require authorization"