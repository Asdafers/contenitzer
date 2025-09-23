import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_videos_compose_contract():
    """Contract test for POST /api/videos/compose"""
    payload = {
        "project_id": "test-project-id"
    }

    response = client.post("/api/videos/compose", json=payload)

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 202  # Async processing started

    data = response.json()
    # Response may be empty for 202 status, just verify it doesn't crash

def test_videos_compose_missing_project_id():
    """Test video composition with missing project_id"""
    payload = {}

    response = client.post("/api/videos/compose", json=payload)
    assert response.status_code == 422  # Validation error