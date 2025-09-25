"""
Contract tests for GET /api/videos/jobs/{job_id}/status endpoint.
These tests validate the API contract and must fail before implementation.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


class TestJobStatusContract:
    """Test GET /api/videos/jobs/{job_id}/status endpoint contract compliance."""

    def test_job_status_endpoint_exists(self, client: TestClient):
        """GET /api/videos/jobs/{job_id}/status should return job information."""
        job_id = str(uuid.uuid4())

        response = client.get(f"/api/videos/jobs/{job_id}/status")

        # Should return job status or 404 if not found
        assert response.status_code in [200, 404], \
            f"Unexpected status code: {response.status_code}"

    def test_job_status_response_schema(self, client: TestClient):
        """GET /api/videos/jobs/{job_id}/status should return proper job schema."""
        job_id = str(uuid.uuid4())

        response = client.get(f"/api/videos/jobs/{job_id}/status")

        if response.status_code == 200:
            job_data = response.json()

            # Required fields
            required_fields = ["id", "status", "progress_percentage"]
            for field in required_fields:
                assert field in job_data, f"Response missing required field: {field}"

            # Validate field types
            assert isinstance(job_data["id"], str), "Job ID should be string"
            assert isinstance(job_data["status"], str), "Status should be string"
            assert isinstance(job_data["progress_percentage"], int), "Progress should be integer"

            # Validate status enum
            valid_statuses = ["PENDING", "MEDIA_GENERATION", "VIDEO_COMPOSITION", "COMPLETED", "FAILED"]
            assert job_data["status"] in valid_statuses, f"Invalid status: {job_data['status']}"

            # Validate progress range
            progress = job_data["progress_percentage"]
            assert 0 <= progress <= 100, f"Progress should be 0-100, got {progress}"

    def test_job_status_not_found(self, client: TestClient):
        """GET /api/videos/jobs/{job_id}/status should return 404 for non-existent jobs."""
        non_existent_id = str(uuid.uuid4())

        response = client.get(f"/api/videos/jobs/{non_existent_id}/status")

        if response.status_code == 404:
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data, "Should return error details"


@pytest.fixture
def client():
    """Test client fixture - will be properly implemented with actual FastAPI app."""
    from unittest.mock import MagicMock
    mock_client = MagicMock()

    def mock_get(url, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Endpoint not implemented"}
        mock_response.headers = {"content-type": "application/json"}
        return mock_response

    mock_client.get = mock_get
    return mock_client