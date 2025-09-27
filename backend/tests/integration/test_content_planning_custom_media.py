"""
Integration test for custom media selection in content planning workflow
Tests the complete flow from content plan creation to custom media integration.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.main import app
from src.lib.database import get_db
from src.services.custom_media_service import CustomMediaService
from src.services.enhanced_content_planner import EnhancedContentPlanner


client = TestClient(app)


class TestContentPlanningCustomMediaIntegration:
    """Integration tests for custom media in content planning workflow"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock(spec=Session)
        return mock_session

    @pytest.fixture
    def sample_content_plan(self):
        """Sample content plan data"""
        return {
            "plan_id": str(uuid.uuid4()),
            "script_id": str(uuid.uuid4()),
            "assets": {
                "images": [
                    {
                        "id": "ai_img_001",
                        "type": "image",
                        "prompt": "Professional office background",
                        "style": "corporate",
                        "estimated_cost": 0.04
                    }
                ],
                "videos": [],
                "audio": [
                    {
                        "id": "ai_audio_001",
                        "type": "narration",
                        "text": "Welcome to our presentation",
                        "estimated_cost": 0.50
                    }
                ]
            },
            "summary": {
                "images": 1,
                "videos": 0,
                "audio": 1,
                "total_assets": 2
            },
            "estimated_costs": {
                "images": 0.04,
                "videos": 0.00,
                "audio": 0.50,
                "total": 0.54
            }
        }

    def test_add_custom_media_to_content_plan_flow(self, mock_db_session, sample_content_plan):
        """Test complete flow of adding custom media to content plan"""
        plan_id = sample_content_plan["plan_id"]

        with patch('src.services.custom_media_service.get_db_session') as mock_get_db:
            mock_get_db.return_value = mock_db_session

            with patch.object(EnhancedContentPlanner, 'get_generation_plan') as mock_get_plan:
                mock_get_plan.return_value = sample_content_plan

                with patch.object(CustomMediaService, 'validate_media_file') as mock_validate:
                    mock_validate.return_value = {
                        "path": "custom_logo.png",
                        "name": "custom_logo.png",
                        "size": 15360,
                        "type": "image",
                        "format": "png",
                        "dimensions": {"width": 512, "height": 512}
                    }

                    # Test: Add custom media
                    payload = {
                        "file_path": "custom_logo.png",
                        "description": "Company logo for branding",
                        "usage_intent": "overlay",
                        "scene_association": "intro"
                    }

                    response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)

                    assert response.status_code == 201
                    data = response.json()
                    assert data["file_path"] == "custom_logo.png"
                    assert data["description"] == "Company logo for branding"
                    assert data["usage_intent"] == "overlay"
                    assert "id" in data
                    assert "selected_at" in data

    def test_custom_media_integration_with_generation_plan(self, sample_content_plan):
        """Test integration of custom media with existing generation plan"""
        plan_id = sample_content_plan["plan_id"]

        with patch.object(EnhancedContentPlanner, 'get_generation_plan') as mock_get_plan:
            mock_get_plan.return_value = sample_content_plan

            with patch.object(EnhancedContentPlanner, 'update_generation_plan') as mock_update_plan:
                mock_update_plan.return_value = True

                with patch.object(CustomMediaService, 'add_custom_media') as mock_add_media:
                    # Setup mock custom media asset
                    custom_asset = {
                        "id": str(uuid.uuid4()),
                        "file_path": "background_music.mp3",
                        "description": "Ambient background music",
                        "usage_intent": "background_audio",
                        "file_info": {
                            "path": "background_music.mp3",
                            "type": "audio",
                            "duration": 180.0
                        },
                        "selected_at": "2025-09-27T10:00:00Z"
                    }
                    mock_add_media.return_value = custom_asset

                    payload = {
                        "file_path": "background_music.mp3",
                        "description": "Ambient background music",
                        "usage_intent": "background_audio"
                    }

                    response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)

                    assert response.status_code == 201

                    # Verify the plan update was called with custom media
                    mock_update_plan.assert_called_once()
                    update_args = mock_update_plan.call_args
                    assert custom_asset["id"] in str(update_args)

    def test_update_custom_media_in_content_plan_flow(self, sample_content_plan):
        """Test updating custom media within content plan"""
        plan_id = sample_content_plan["plan_id"]
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'update_custom_media') as mock_update:
            updated_asset = {
                "id": asset_id,
                "file_path": "updated_image.jpg",
                "description": "Updated description",
                "usage_intent": "background",
                "scene_association": "outro",
                "updated_at": "2025-09-27T10:30:00Z"
            }
            mock_update.return_value = updated_asset

            payload = {
                "file_path": "updated_image.jpg",
                "description": "Updated description",
                "scene_association": "outro"
            }

            response = client.put(f"/api/content-planning/{plan_id}/custom-media/{asset_id}", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["file_path"] == "updated_image.jpg"
            assert data["description"] == "Updated description"
            assert "updated_at" in data

    def test_remove_custom_media_from_content_plan_flow(self, sample_content_plan):
        """Test removing custom media from content plan"""
        plan_id = sample_content_plan["plan_id"]
        asset_id = str(uuid.uuid4())

        with patch.object(CustomMediaService, 'remove_custom_media') as mock_remove:
            mock_remove.return_value = True

            with patch.object(EnhancedContentPlanner, 'update_generation_plan') as mock_update_plan:
                mock_update_plan.return_value = True

                response = client.delete(f"/api/content-planning/{plan_id}/custom-media/{asset_id}")

                assert response.status_code == 204
                mock_remove.assert_called_once_with(plan_id, asset_id)

    def test_custom_media_validation_integration(self, sample_content_plan):
        """Test custom media validation integration with file system"""
        plan_id = sample_content_plan["plan_id"]

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            # Test invalid file format
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

    def test_custom_media_duplicate_prevention(self, sample_content_plan):
        """Test prevention of duplicate custom media in same plan"""
        plan_id = sample_content_plan["plan_id"]

        with patch.object(CustomMediaService, 'add_custom_media') as mock_add:
            # First addition succeeds
            first_asset = {
                "id": str(uuid.uuid4()),
                "file_path": "logo.png",
                "description": "Company logo",
                "usage_intent": "overlay"
            }
            mock_add.return_value = first_asset

            payload = {
                "file_path": "logo.png",
                "description": "Company logo",
                "usage_intent": "overlay"
            }

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 201

            # Second addition of same file should fail
            from src.lib.exceptions import ContentPlanningError
            mock_add.side_effect = ContentPlanningError("File already selected for this plan")

            response = client.post(f"/api/content-planning/{plan_id}/custom-media", json=payload)
            assert response.status_code == 409