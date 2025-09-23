import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_media_generate_contract():
    """Contract test for POST /api/media/generate"""
    payload = {
        "script_id": "test-script-id"
    }

    response = client.post("/api/media/generate", json=payload)

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 202  # Async processing started

    data = response.json()
    assert "project_id" in data
    assert "status" in data
    assert isinstance(data["project_id"], str)
    assert isinstance(data["status"], str)

def test_media_generate_missing_script_id():
    """Test media generation with missing script_id"""
    payload = {}

    response = client.post("/api/media/generate", json=payload)
    assert response.status_code == 422  # Validation error