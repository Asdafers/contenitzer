"""
Integration test for media file browsing workflow
Tests the complete flow from file system scanning to API response.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from src.main import app
from src.services.media_browsing_service import MediaBrowsingService


client = TestClient(app)


class TestMediaBrowsingIntegrationFlow:
    """Integration tests for media browsing workflow"""

    @pytest.fixture
    def temp_media_dir(self):
        """Create temporary media directory with test files"""
        temp_dir = tempfile.mkdtemp()
        media_dir = Path(temp_dir) / "media"
        media_dir.mkdir()

        # Create test subdirectories
        (media_dir / "images").mkdir()
        (media_dir / "videos").mkdir()
        (media_dir / "audio").mkdir()

        # Create test files
        test_files = [
            "images/test_image1.jpg",
            "images/test_image2.png",
            "images/subfolder/nested_image.jpg",
            "videos/test_video1.mp4",
            "videos/test_video2.mp4",
            "audio/test_audio1.mp3",
            "audio/test_audio2.wav",
            "documents/readme.txt"  # Should be ignored
        ]

        for file_path in test_files:
            full_path = media_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Test content for {file_path}")

        yield media_dir
        shutil.rmtree(temp_dir)

    def test_browse_media_files_integration_flow(self, temp_media_dir):
        """Test complete media browsing flow with real file system"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # Test 1: Browse root directory
            response = client.get("/api/media/browse")
            assert response.status_code == 200

            data = response.json()
            assert "files" in data
            assert data["current_path"] == ""
            assert data["total_count"] > 0

            # Should find supported media files
            file_names = [f["name"] for f in data["files"]]
            assert "test_image1.jpg" in file_names
            assert "test_video1.mp4" in file_names
            assert "readme.txt" not in file_names  # Unsupported format excluded

    def test_browse_media_files_with_filters_integration(self, temp_media_dir):
        """Test media browsing with file type filters"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # Test: Filter by image files only
            response = client.get("/api/media/browse?file_type=image")
            assert response.status_code == 200

            data = response.json()
            image_files = data["files"]

            # All returned files should be images
            for file_info in image_files:
                assert file_info["type"] == "image"
                assert file_info["format"] in ["jpg", "png"]

            # Should not contain video or audio files
            file_types = [f["type"] for f in image_files]
            assert "video" not in file_types
            assert "audio" not in file_types

    def test_browse_subdirectory_integration_flow(self, temp_media_dir):
        """Test browsing subdirectories"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # Test: Browse images subdirectory
            response = client.get("/api/media/browse?path=images")
            assert response.status_code == 200

            data = response.json()
            assert data["current_path"] == "images"
            assert data["parent_path"] == ""

            # Should find image files in images directory
            file_names = [f["name"] for f in data["files"]]
            assert "test_image1.jpg" in file_names
            assert "test_image2.png" in file_names

    def test_pagination_integration_flow(self, temp_media_dir):
        """Test pagination with real file system"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # Test: Get first page with limit
            response = client.get("/api/media/browse?limit=2&offset=0")
            assert response.status_code == 200

            data = response.json()
            assert len(data["files"]) <= 2
            total_count = data["total_count"]

            # Test: Get second page
            response = client.get(f"/api/media/browse?limit=2&offset=2")
            assert response.status_code == 200

            data2 = response.json()
            assert data2["total_count"] == total_count  # Same total

            # Files should be different (assuming more than 2 files exist)
            if total_count > 2:
                first_page_names = {f["name"] for f in data["files"]}
                second_page_names = {f["name"] for f in data2["files"]}
                assert first_page_names != second_page_names

    def test_get_file_info_integration_flow(self, temp_media_dir):
        """Test getting detailed file information"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # First, browse to get available files
            response = client.get("/api/media/browse?file_type=image")
            assert response.status_code == 200

            files = response.json()["files"]
            if files:
                test_file = files[0]
                file_path = test_file["path"]

                # Test: Get detailed file info
                response = client.get(f"/api/media/info/{file_path}")
                assert response.status_code == 200

                file_info = response.json()
                assert file_info["path"] == file_path
                assert file_info["type"] in ["image", "video", "audio"]
                assert file_info["size"] > 0
                assert "name" in file_info
                assert "format" in file_info

    def test_error_handling_integration_flow(self, temp_media_dir):
        """Test error handling in integration flow"""
        with patch('src.services.media_browsing_service.MediaBrowsingService._get_media_root') as mock_root:
            mock_root.return_value = temp_media_dir

            # Test: Browse non-existent subdirectory
            response = client.get("/api/media/browse?path=nonexistent")
            assert response.status_code == 400

            # Test: Get info for non-existent file
            response = client.get("/api/media/info/nonexistent.jpg")
            assert response.status_code == 404

            # Test: Invalid file type filter
            response = client.get("/api/media/browse?file_type=invalid")
            assert response.status_code == 400