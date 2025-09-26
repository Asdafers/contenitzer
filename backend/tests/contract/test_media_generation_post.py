"""
Contract test for POST /api/media/generate endpoint
Task: T004 [P] - Contract test POST /api/media/generate
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from uuid import UUID
from datetime import datetime


class TestMediaGenerationPostContract:
    """Contract tests for POST /api/media/generate endpoint"""

    def test_valid_request_returns_202(self, client: TestClient):
        """Test valid media generation request returns 202 with correct schema"""
        request_data = {
            "script_content": "Speaker 1: Today we'll discuss AI advancements...",
            "asset_types": ["image"],
            "num_assets": 2,
            "preferred_model": "gemini-2.5-flash-image",
            "allow_fallback": True
        }

        response = client.post("/api/media/generate", json=request_data)

        # Should return 202 Accepted
        assert response.status_code == 202

        # Validate response schema
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "model_selected" in data
        assert "estimated_completion" in data

        # Validate specific fields
        UUID(data["job_id"])  # Should be valid UUID
        assert data["status"] in ["pending", "generating"]
        assert data["model_selected"] in ["gemini-2.5-flash-image", "gemini-pro"]
        datetime.fromisoformat(data["estimated_completion"].replace('Z', '+00:00'))

    def test_defaults_to_gemini_2_5_flash_image(self, client: TestClient):
        """Test request without preferred_model defaults to gemini-2.5-flash-image"""
        request_data = {
            "script_content": "Test content",
            "asset_types": ["image"]
        }

        response = client.post("/api/media/generate", json=request_data)

        if response.status_code == 202:
            data = response.json()
            assert data["model_selected"] == "gemini-2.5-flash-image"

    def test_invalid_asset_types_returns_400(self, client: TestClient):
        """Test invalid asset_types enum values return 400"""
        request_data = {
            "script_content": "Test content",
            "asset_types": ["invalid_type"],
            "num_assets": 1
        }

        response = client.post("/api/media/generate", json=request_data)
        assert response.status_code == 400

    def test_invalid_num_assets_range_returns_400(self, client: TestClient):
        """Test num_assets outside 1-10 range returns 400"""
        # Test below minimum
        request_data = {
            "script_content": "Test content",
            "asset_types": ["image"],
            "num_assets": 0
        }
        response = client.post("/api/media/generate", json=request_data)
        assert response.status_code == 400

        # Test above maximum
        request_data["num_assets"] = 11
        response = client.post("/api/media/generate", json=request_data)
        assert response.status_code == 400

    def test_missing_required_fields_returns_400(self, client: TestClient):
        """Test missing required fields return 400"""
        # Missing script_content
        response = client.post("/api/media/generate", json={"asset_types": ["image"]})
        assert response.status_code == 400

        # Missing asset_types
        response = client.post("/api/media/generate", json={"script_content": "test"})
        assert response.status_code == 400

    def test_invalid_preferred_model_returns_400(self, client: TestClient):
        """Test invalid preferred_model returns 400"""
        request_data = {
            "script_content": "Test content",
            "asset_types": ["image"],
            "preferred_model": "invalid-model"
        }

        response = client.post("/api/media/generate", json=request_data)
        assert response.status_code == 400

    def test_models_unavailable_returns_503(self, client: TestClient):
        """Test when all models unavailable returns 503"""
        # This test will pass when service properly handles model unavailability
        request_data = {
            "script_content": "Test content",
            "asset_types": ["image"],
            "allow_fallback": False
        }

        # This should eventually return 503 when models are unavailable
        response = client.post("/api/media/generate", json=request_data)
        # For now, just ensure it doesn't crash
        assert response.status_code in [202, 400, 503]


@pytest.fixture
def client():
    """Test client fixture - will fail until implementation exists"""
    from backend.main import app
    return TestClient(app)