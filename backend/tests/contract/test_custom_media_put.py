"""
Contract test for PUT /api/content-planning/{id}/custom-media/{asset_id} endpoint
Tests the API contract for updating custom media in content plans.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

from src.main import app
from src.services.custom_media_service import CustomMediaService


client = TestClient(app)


class TestCustomMediaPutContract:
    """Contract tests for PUT /api/content-planning/{id}/custom-media/{asset_id} endpoint"""

    def test_update_custom_media_success(self):
        """Test successful update of custom media in content plan"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            # Setup mock response
            mock_updated_asset = {
                "id": asset_id,
                "file_path": "new_image.jpg",
                "description": "Updated description",
                "usage_intent": "foreground",
                "scene_association": "outro",
                "file_info": {
                    "path": "new_image.jpg",
                    "name": "new_image.jpg",
                    "size": 2048,
                    "type": "image",
                    "format": "jpg"
                },
                "selected_at": "2025-09-27T10:00:00Z",
                "updated_at": "2025-09-27T10:30:00Z"
            }
            mock_update.return_value = mock_updated_asset

            # Request payload
            payload = {
                "file_path": "new_image.jpg",
                "description": "Updated description",
                "usage_intent": "foreground",
                "scene_association": "outro"
            }

            # Make request
            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == asset_id
            assert data["file_path"] == "new_image.jpg"
            assert data["description"] == "Updated description"
            assert data["usage_intent"] == "foreground"
            assert "updated_at" in data

    def test_update_custom_media_partial_update(self):
        """Test partial update of custom media (only some fields)"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            mock_updated_asset = {
                "id": asset_id,
                "file_path": "original_image.jpg",  # Unchanged
                "description": "Updated description only",  # Changed
                "usage_intent": "background",  # Unchanged
                "scene_association": None,
                "updated_at": "2025-09-27T10:30:00Z"
            }
            mock_update.return_value = mock_updated_asset

            # Only update description
            payload = {
                "description": "Updated description only"
            }

            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated description only"

    def test_update_custom_media_invalid_plan_id(self):
        """Test updating custom media with invalid plan ID format"""
        asset_id = str(uuid.uuid4())
        payload = {"description": "Updated description"}

        response = client.put(
            f"/api/content-planning/invalid-uuid/custom-media/{asset_id}",
            json=payload
        )
        assert response.status_code == 422  # Validation error

    def test_update_custom_media_invalid_asset_id(self):
        """Test updating custom media with invalid asset ID format"""
        plan_id = str(uuid.uuid4())
        payload = {"description": "Updated description"}

        response = client.put(
            f"/api/content-planning/{plan_id}/custom-media/invalid-uuid",
            json=payload
        )
        assert response.status_code == 422  # Validation error

    def test_update_custom_media_plan_not_found(self):
        """Test updating custom media in non-existent content plan"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            from src.lib.exceptions import ContentPlanningError
            mock_update.side_effect = ContentPlanningError(f"Content plan {plan_id} not found")

            payload = {"description": "Updated description"}

            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_update_custom_media_asset_not_found(self):
        """Test updating non-existent custom media asset"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            from src.lib.exceptions import ContentPlanningError
            mock_update.side_effect = ContentPlanningError(f"Custom media asset {asset_id} not found")

            payload = {"description": "Updated description"}

            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_update_custom_media_invalid_file_path(self):
        """Test updating custom media with invalid file path"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            from src.lib.exceptions import MediaBrowsingError
            mock_update.side_effect = MediaBrowsingError("File not found: invalid.jpg")

            payload = {
                "file_path": "invalid.jpg",
                "description": "Updated with invalid file"
            }

            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            assert response.status_code == 400
            assert "File not found" in response.json()["detail"]

    def test_update_custom_media_empty_payload(self):
        """Test updating custom media with empty payload"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            from src.lib.exceptions import ContentPlanningError
            mock_update.side_effect = ContentPlanningError("No fields to update")

            payload = {}

            response = client.put(
                f"/api/content-planning/{plan_id}/custom-media/{asset_id}",
                json=payload
            )

            assert response.status_code == 400
            assert "No fields to update" in response.json()["detail"]