"""
Contract test for GET /api/media/browse endpoint
Tests the API contract for media file browsing functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.main import app
from src.services.media_browsing_service import MediaBrowsingService
from src.api.media_browsing import MediaFileInfo, MediaBrowseResponse


client = TestClient(app)


class TestMediaBrowseGetContract:
    """Contract tests for GET /api/media/browse endpoint"""

    def test_browse_media_files_default_parameters(self):
        """Test browsing media files with default parameters"""
        # Mock the MediaBrowsingService
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            # Setup mock response
            mock_response = MediaBrowseResponse(
                files=[
                    MediaFileInfo(
                        path="test_image.jpg",
                        name="test_image.jpg",
                        size=1024,
                        type="image",
                        format="jpg",
                        thumbnail_url="/api/media/thumbnails/test_image.jpg",
                        dimensions={"width": 1920, "height": 1080}
                    )
                ],
                total_count=1,
                current_path="",
                parent_path=None
            )
            mock_browse.return_value = mock_response

            # Make request
            response = client.get("/api/media/browse")

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert "files" in data
            assert "total_count" in data
            assert "current_path" in data
            assert data["total_count"] == 1
            assert len(data["files"]) == 1

            # Verify file structure
            file = data["files"][0]
            assert file["path"] == "test_image.jpg"
            assert file["name"] == "test_image.jpg"
            assert file["type"] == "image"
            assert file["format"] == "jpg"

    def test_browse_media_files_with_path_filter(self):
        """Test browsing media files with path parameter"""
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            mock_response = MediaBrowseResponse(
                files=[],
                total_count=0,
                current_path="subfolder",
                parent_path=""
            )
            mock_browse.return_value = mock_response

            response = client.get("/api/media/browse?path=subfolder")

            assert response.status_code == 200
            data = response.json()
            assert data["current_path"] == "subfolder"
            mock_browse.assert_called_once_with(
                path="subfolder",
                file_type=None,
                limit=50,
                offset=0
            )

    def test_browse_media_files_with_type_filter(self):
        """Test browsing media files with file type filter"""
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            mock_response = MediaBrowseResponse(
                files=[],
                total_count=0,
                current_path="",
                parent_path=None
            )
            mock_browse.return_value = mock_response

            response = client.get("/api/media/browse?file_type=image")

            assert response.status_code == 200
            mock_browse.assert_called_once_with(
                path=None,
                file_type="image",
                limit=50,
                offset=0
            )

    def test_browse_media_files_with_pagination(self):
        """Test browsing media files with pagination parameters"""
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            mock_response = MediaBrowseResponse(
                files=[],
                total_count=100,
                current_path="",
                parent_path=None
            )
            mock_browse.return_value = mock_response

            response = client.get("/api/media/browse?limit=25&offset=50")

            assert response.status_code == 200
            mock_browse.assert_called_once_with(
                path=None,
                file_type=None,
                limit=25,
                offset=50
            )

    def test_browse_media_files_invalid_limit(self):
        """Test browsing with invalid limit parameter"""
        response = client.get("/api/media/browse?limit=0")
        assert response.status_code == 422  # Validation error

        response = client.get("/api/media/browse?limit=300")
        assert response.status_code == 422  # Validation error

    def test_browse_media_files_invalid_offset(self):
        """Test browsing with invalid offset parameter"""
        response = client.get("/api/media/browse?offset=-1")
        assert response.status_code == 422  # Validation error

    def test_browse_media_files_service_error(self):
        """Test error handling when service raises MediaBrowsingError"""
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            from src.lib.exceptions import MediaBrowsingError
            mock_browse.side_effect = MediaBrowsingError("Invalid path")

            response = client.get("/api/media/browse")

            assert response.status_code == 400
            assert "Invalid path" in response.json()["detail"]

    def test_browse_media_files_unexpected_error(self):
        """Test error handling for unexpected exceptions"""
        with patch.object(MediaBrowsingService, 'browse_files') as mock_browse:
            mock_browse.side_effect = Exception("Unexpected error")

            response = client.get("/api/media/browse")

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]


class TestMediaFileInfoGetContract:
    """Contract tests for GET /api/media/info/{file_path} endpoint"""

    def test_get_media_file_info_success(self):
        """Test successful file info retrieval"""
        with patch.object(MediaBrowsingService, 'get_file_info') as mock_get_info:
            mock_file_info = MediaFileInfo(
                path="test_video.mp4",
                name="test_video.mp4",
                size=5242880,
                type="video",
                format="mp4",
                duration=120.5,
                dimensions={"width": 1920, "height": 1080}
            )
            mock_get_info.return_value = mock_file_info

            response = client.get("/api/media/info/test_video.mp4")

            assert response.status_code == 200
            data = response.json()
            assert data["path"] == "test_video.mp4"
            assert data["type"] == "video"
            assert data["duration"] == 120.5

    def test_get_media_file_info_not_found(self):
        """Test file not found scenario"""
        with patch.object(MediaBrowsingService, 'get_file_info') as mock_get_info:
            mock_get_info.return_value = None

            response = client.get("/api/media/info/nonexistent.jpg")

            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]

    def test_get_media_file_info_service_error(self):
        """Test service error handling"""
        with patch.object(MediaBrowsingService, 'get_file_info') as mock_get_info:
            from src.lib.exceptions import MediaBrowsingError
            mock_get_info.side_effect = MediaBrowsingError("File not found")

            response = client.get("/api/media/info/invalid.jpg")

            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]