import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_videos_upload_contract():
    """Contract test for POST /api/videos/upload"""
    payload = {
        "project_id": "test-project-id",
        "youtube_api_key": "test-youtube-api-key"
    }

    response = client.post("/api/videos/upload", json=payload)

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 202  # Async processing started

def test_videos_upload_missing_fields():
    """Test video upload with missing required fields"""
    payload = {
        "project_id": "test-project-id"
        # Missing youtube_api_key
    }

    response = client.post("/api/videos/upload", json=payload)
    assert response.status_code == 422  # Validation error