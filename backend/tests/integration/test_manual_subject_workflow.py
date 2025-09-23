import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_manual_subject_workflow():
    """Integration test for manual subject workflow: Manual topic -> script -> media -> video -> upload"""

    # Step 1: Generate script from manual subject
    script_payload = {
        "input_type": "manual_subject",
        "manual_input": "The environmental impact of renewable energy technologies"
    }

    script_response = client.post("/api/scripts/generate", json=script_payload)
    assert script_response.status_code == 200

    script_data = script_response.json()
    script_id = script_data["script_id"]
    assert script_data["estimated_duration"] >= 180  # At least 3 minutes
    assert len(script_data["content"]) > 0

    # Step 2: Generate media assets
    media_payload = {
        "script_id": script_id
    }

    media_response = client.post("/api/media/generate", json=media_payload)
    assert media_response.status_code == 202

    media_data = media_response.json()
    project_id = media_data["project_id"]

    # Step 3: Compose video
    compose_payload = {
        "project_id": project_id
    }

    compose_response = client.post("/api/videos/compose", json=compose_payload)
    assert compose_response.status_code == 202

    # Step 4: Upload to YouTube
    upload_payload = {
        "project_id": project_id,
        "youtube_api_key": "test-youtube-api-key"
    }

    upload_response = client.post("/api/videos/upload", json=upload_payload)
    assert upload_response.status_code == 202