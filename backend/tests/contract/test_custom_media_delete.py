"""
Contract test for DELETE /api/content-planning/{id}/custom-media/{asset_id} endpoint
Tests the API contract for removing custom media from content plans.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import uuid

from src.main import app
from src.services.custom_media_service import CustomMediaService


client = TestClient(app)


class TestCustomMediaDeleteContract:
    """Contract tests for DELETE /api/content-planning/{id}/custom-media/{asset_id} endpoint"""

    def test_delete_custom_media_success(self):
        """Test successful deletion of custom media from content plan"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            mock_remove.return_value = True

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 204
            mock_remove.assert_called_once_with(plan_id, asset_id)

    def test_delete_custom_media_invalid_plan_id(self):
        """Test deleting custom media with invalid plan ID format"""
        asset_id = str(uuid.uuid4())

        response = client.delete(f"/api/content-planning/invalid-uuid/custom-media/{asset_id}")
        assert response.status_code == 422  # Validation error

    def test_delete_custom_media_invalid_asset_id(self):
        """Test deleting custom media with invalid asset ID format"""
        plan_id = str(uuid.uuid4())

        response = client.delete(f"/api/content-planning/{plan_id}/custom-media/invalid-uuid")
        assert response.status_code == 422  # Validation error

    def test_delete_custom_media_plan_not_found(self):
        """Test deleting custom media from non-existent content plan"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            from src.lib.exceptions import ContentPlanningError
            mock_remove.side_effect = ContentPlanningError(f"Content plan {plan_id} not found")

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_delete_custom_media_asset_not_found(self):
        """Test deleting non-existent custom media asset"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            from src.lib.exceptions import ContentPlanningError
            mock_remove.side_effect = ContentPlanningError(f"Custom media asset {asset_id} not found")

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_delete_custom_media_asset_not_in_plan(self):
        """Test deleting custom media asset that's not associated with the plan"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            from src.lib.exceptions import ContentPlanningError
            mock_remove.side_effect = ContentPlanningError(
                f"Asset {asset_id} not found in plan {plan_id}"
            )

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 404
            assert "not found in plan" in response.json()["detail"]

    def test_delete_custom_media_service_error(self):
        """Test error handling for service errors during deletion"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            mock_remove.side_effect = Exception("Database connection failed")

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_delete_custom_media_already_deleted(self):
        """Test deleting custom media that was already removed"""
        plan_id = str(uuid.uuid4())
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            mock_remove.return_value = False  # Indicates asset was not found/already deleted

            response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

            assert response.status_code == 404