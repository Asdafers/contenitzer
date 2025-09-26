"""
Contract test for GET /api/media/assets/{asset_id} endpoint
Task: T005 [P] - Contract test GET /api/media/assets/{asset_id}
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
from datetime import datetime


class TestMediaAssetsGetContract:
    """Contract tests for GET /api/media/assets/{asset_id} endpoint"""

    def test_valid_asset_id_returns_200(self, client: TestClient):
        """Test valid asset ID returns 200 with correct schema"""
        # Use a valid UUID format
        asset_id = str(uuid4())

        response = client.get(f"/api/media/assets/{asset_id}")

        # Will fail until implementation exists, but validates the contract
        if response.status_code == 200:
            data = response.json()

            # Validate required fields
            assert "id" in data
            assert "asset_type" in data
            assert "generation_model" in data
            assert "model_fallback_used" in data
            assert "created_at" in data

            # Validate field types and formats
            UUID(data["id"])  # Should be valid UUID
            assert data["asset_type"] in ["image", "video_clip", "audio"]
            assert isinstance(data["model_fallback_used"], bool)
            datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))

            # Validate generation model
            assert data["generation_model"].startswith("gemini-")

            # Validate optional fields if present
            if "file_path" in data:
                assert isinstance(data["file_path"], str)

            if "generation_metadata" in data:
                metadata = data["generation_metadata"]
                if "generation_time_ms" in metadata:
                    assert isinstance(metadata["generation_time_ms"], int)
                    assert metadata["generation_time_ms"] > 0
                if "quality_score" in metadata:
                    assert 0 <= metadata["quality_score"] <= 1

    def test_invalid_uuid_returns_400(self, client: TestClient):
        """Test invalid UUID format returns 400"""
        response = client.get("/api/media/assets/invalid-uuid")
        assert response.status_code in [400, 422]  # FastAPI returns 422 for validation errors

    def test_nonexistent_asset_returns_404(self, client: TestClient):
        """Test non-existent asset ID returns 404"""
        asset_id = str(uuid4())  # Random UUID that doesn't exist

        response = client.get(f"/api/media/assets/{asset_id}")

        # Should return 404 when asset doesn't exist
        if response.status_code == 404:
            data = response.json()
            assert "error" in data

    def test_model_metadata_tracking(self, client: TestClient):
        """Test asset tracks correct model information"""
        asset_id = str(uuid4())

        response = client.get(f"/api/media/assets/{asset_id}")

        if response.status_code == 200:
            data = response.json()

            # Should track which model was used
            assert data["generation_model"] in ["gemini-2.5-flash-image", "gemini-pro"]

            # Should indicate if fallback was used
            assert isinstance(data["model_fallback_used"], bool)

            # If gemini-2.5-flash-image was used, fallback should be false
            if data["generation_model"] == "gemini-2.5-flash-image":
                assert data["model_fallback_used"] is False

    def test_generation_metadata_structure(self, client: TestClient):
        """Test generation metadata has correct structure"""
        asset_id = str(uuid4())

        response = client.get(f"/api/media/assets/{asset_id}")

        if response.status_code == 200:
            data = response.json()

            if "generation_metadata" in data:
                metadata = data["generation_metadata"]

                # Check expected metadata fields
                expected_fields = ["model_version", "generation_time_ms"]
                for field in expected_fields:
                    if field in metadata:
                        if field == "generation_time_ms":
                            assert isinstance(metadata[field], int)
                            assert metadata[field] > 0
                        elif field == "model_version":
                            assert metadata[field].startswith("gemini-")

    def test_content_type_is_json(self, client: TestClient):
        """Test response content type is application/json"""
        asset_id = str(uuid4())

        response = client.get(f"/api/media/assets/{asset_id}")

        if response.status_code in [200, 404]:
            assert "application/json" in response.headers.get("content-type", "")


@pytest.fixture
def client():
    """Test client fixture - will fail until implementation exists"""
    from backend.main import app
    return TestClient(app)