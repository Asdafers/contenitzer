import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_full_automated_workflow():
    """Integration test for complete automated workflow: API -> theme -> script -> media -> video -> upload"""

    # Step 1: Analyze trending content
    trending_payload = {
        "timeframe": "weekly",
        "api_key": "test-api-key"
    }

    trending_response = client.post("/api/trending/analyze", json=trending_payload)
    assert trending_response.status_code == 200

    trending_data = trending_response.json()
    assert len(trending_data["categories"]) > 0

    # Get first theme from first category
    first_category = trending_data["categories"][0]
    assert len(first_category["themes"]) > 0
    theme_id = first_category["themes"][0]["id"]

    # Step 2: Generate script from theme
    script_payload = {
        "input_type": "theme",
        "theme_id": theme_id
    }

    script_response = client.post("/api/scripts/generate", json=script_payload)
    assert script_response.status_code == 200

    script_data = script_response.json()
    script_id = script_data["script_id"]
    assert script_data["estimated_duration"] >= 180  # At least 3 minutes

    # Step 3: Generate media assets
    media_payload = {
        "script_id": script_id
    }

    media_response = client.post("/api/media/generate", json=media_payload)
    assert media_response.status_code == 202

    media_data = media_response.json()
    project_id = media_data["project_id"]

    # Step 4: Compose video
    compose_payload = {
        "project_id": project_id
    }

    compose_response = client.post("/api/videos/compose", json=compose_payload)
    assert compose_response.status_code == 202

    # Step 5: Upload to YouTube
    upload_payload = {
        "project_id": project_id,
        "youtube_api_key": "test-youtube-api-key"
    }

    upload_response = client.post("/api/videos/upload", json=upload_payload)
    assert upload_response.status_code == 202