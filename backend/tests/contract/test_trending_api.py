import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import app

client = TestClient(app)

def test_trending_analyze_contract():
    """Contract test for POST /api/trending/analyze"""
    payload = {
        "timeframe": "weekly",
        "api_key": "test-api-key"
    }

    response = client.post("/api/trending/analyze", json=payload)

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 200

    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)

    if data["categories"]:
        category = data["categories"][0]
        assert "id" in category
        assert "name" in category
        assert "themes" in category
        assert isinstance(category["themes"], list)

        if category["themes"]:
            theme = category["themes"][0]
            assert "id" in theme
            assert "name" in theme
            assert "relevance_score" in theme
            assert isinstance(theme["relevance_score"], (int, float))

def test_trending_analyze_invalid_timeframe():
    """Test invalid timeframe enum value"""
    payload = {
        "timeframe": "invalid",
        "api_key": "test-api-key"
    }

    response = client.post("/api/trending/analyze", json=payload)
    assert response.status_code == 422  # Validation error