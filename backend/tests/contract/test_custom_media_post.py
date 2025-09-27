"""
Contract test for POST /api/content-planning/{id}/custom-media endpoint
Tests the API contract for adding custom media to content plans.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

from src.main import app
from src.services.custom_media_service import CustomMediaService


client = TestClient(app)


class TestCustomMediaPostContract:
    """Contract tests for POST /api/content-planning/{id}/custom-media endpoint"""

    def test_add_custom_media_success(self):
        """Test successful addition of custom media to content plan"""
        plan_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            # Setup mock response
            mock_asset = {
                "id": str(uuid.uuid4()),
                "file_path": "test_image.jpg",
                "description": "Test image for background",
                "usage_intent": "background",
                "file_info": {
                    "path": "test_image.jpg",
                    "name": "test_image.jpg",
                    "size": 1024,
                    "type": "image",
                    "format": "jpg"
                },
                "selected_at": "2025-09-27T10:00:00Z"
            }
            mock_add.return_value = mock_asset

            # Request payload
            payload = {
                "file_path": "test_image.jpg",
                "description": "Test image for background",
                "usage_intent": "background",
                "scene_association": "intro"
            }

            # Make request
            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)

            # Assert response
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["file_path"] == "test_image.jpg"
            assert data["description"] == "Test image for background"
            assert data["usage_intent"] == "background"
            assert "selected_at" in data

    def test_add_custom_media_invalid_plan_id(self):
        """Test adding custom media with invalid plan ID format"""
        payload = {
            "file_path": "test_image.jpg",
            "description": "Test image",
            "usage_intent": "background"
        }

        response = client.post("/api/content-planning/invalid-uuid/custom-media", json=payload)
        assert response.status_code == 422  # Validation error

    def test_add_custom_media_missing_required_fields(self):
        """Test adding custom media with missing required fields"""
        plan_id = str(uuid.uuid4())

        # Missing file_path
        payload = {
            "description": "Test image",
            "usage_intent": "background"
        }
        response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
        assert response.status_code == 422

        # Missing usage_intent
        payload = {
            "file_path": "test_image.jpg",
            "description": "Test image"
        }
        response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
        assert response.status_code == 422

    def test_add_custom_media_invalid_file_path(self):
        """Test adding custom media with invalid file path"""
        plan_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            from src.lib.exceptions import MediaBrowsingError
            mock_add.side_effect = MediaBrowsingError("File not found: invalid.jpg")

            payload = {
                "file_path": "invalid.jpg",
                "description": "Invalid file",
                "usage_intent": "background"
            }

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 400
            assert "File not found" in response.json()["detail"]

    def test_add_custom_media_plan_not_found(self):
        """Test adding custom media to non-existent content plan"""
        plan_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            from src.lib.exceptions import ContentPlanningError
            mock_add.side_effect = ContentPlanningError(f"Content plan {plan_id} not found")

            payload = {
                "file_path": "test_image.jpg",
                "description": "Test image",
                "usage_intent": "background"
            }

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_add_custom_media_unsupported_file_type(self):
        """Test adding custom media with unsupported file type"""
        plan_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            from src.lib.exceptions import MediaBrowsingError
            mock_add.side_effect = MediaBrowsingError("Unsupported file format: .txt")

            payload = {
                "file_path": "document.txt",
                "description": "Text document",
                "usage_intent": "background"
            }

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 400
            assert "Unsupported file format" in response.json()["detail"]

    def test_add_custom_media_duplicate_file(self):
        """Test adding duplicate custom media to same content plan"""
        plan_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            from src.lib.exceptions import ContentPlanningError
            mock_add.side_effect = ContentPlanningError("File already selected for this plan")

            payload = {
                "file_path": "test_image.jpg",
                "description": "Duplicate image",
                "usage_intent": "background"
            }

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 409  # Conflict
            assert "already selected" in response.json()["detail"]