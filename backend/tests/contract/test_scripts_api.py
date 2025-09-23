import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_scripts_generate_from_theme_contract():
    """Contract test for POST /api/scripts/generate with theme input"""
    payload = {
        "input_type": "theme",
        "theme_id": "test-theme-id"
    }

    response = client.post("/api/scripts/generate", json=payload)

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 200

    data = response.json()
    assert "script_id" in data
    assert "content" in data
    assert "estimated_duration" in data
    assert isinstance(data["estimated_duration"], int)
    assert data["estimated_duration"] >= 180  # Minimum 3 minutes

def test_scripts_generate_from_manual_subject_contract():
    """Contract test for POST /api/scripts/generate with manual subject"""
    payload = {
        "input_type": "manual_subject",
        "manual_input": "The future of artificial intelligence"
    }

    response = client.post("/api/scripts/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "script_id" in data
    assert "content" in data
    assert "estimated_duration" in data

def test_scripts_generate_from_manual_script_contract():
    """Contract test for POST /api/scripts/generate with complete script"""
    payload = {
        "input_type": "manual_script",
        "manual_input": "Speaker 1: Welcome to our show. Speaker 2: Thanks for having me..."
    }

    response = client.post("/api/scripts/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "script_id" in data
    assert "content" in data
    assert "estimated_duration" in data