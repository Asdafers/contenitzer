import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_manual_script_workflow():
    """Integration test for manual script workflow: Complete script -> media -> video -> upload"""

    # Complete script that should be at least 3 minutes (approximately 450+ words)
    manual_script = """
    Speaker 1: Welcome everyone to today's discussion about the future of artificial intelligence.
    I'm here with my colleague to explore how AI is transforming our world and what we can expect in the coming years.

    Speaker 2: Thank you for having me. It's fascinating to consider how rapidly AI technology has evolved.
    Just in the past few years, we've seen remarkable advances in machine learning, natural language processing,
    and computer vision that were unimaginable a decade ago.

    Speaker 1: Absolutely. Let's start with machine learning. The development of transformer architectures
    has revolutionized how AI systems understand and generate human language. These models can now engage
    in complex conversations, write code, and even create artistic content.

    Speaker 2: That's right. And what's particularly interesting is how these systems learn from vast amounts
    of data to identify patterns and make predictions. However, this also raises important questions about
    data privacy, algorithmic bias, and the ethical implications of AI decision-making.

    Speaker 1: Those are crucial considerations. As AI becomes more integrated into healthcare, finance,
    education, and other critical sectors, we need robust frameworks for ensuring fairness, transparency,
    and accountability in AI systems.

    Speaker 2: Looking ahead, I think we'll see AI becoming even more specialized and efficient.
    We're moving toward AI agents that can perform complex multi-step tasks, collaborate with humans
    more naturally, and adapt to new situations with minimal training.

    Speaker 1: The potential applications are endless - from scientific research and drug discovery
    to climate modeling and space exploration. AI could help us solve some of humanity's greatest challenges.

    Speaker 2: Indeed. But as we embrace these possibilities, we must also prepare for the societal changes
    that AI will bring. This includes rethinking education, job markets, and social structures to ensure
    that the benefits of AI are distributed equitably.

    Speaker 1: Thank you for this enlightening discussion. The future of AI is both exciting and challenging,
    and it will require thoughtful collaboration between technologists, policymakers, and society as a whole.
    """

    # Step 1: Process manual script
    script_payload = {
        "input_type": "manual_script",
        "manual_input": manual_script.strip()
    }

    script_response = client.post("/api/scripts/generate", json=script_payload)
    assert script_response.status_code == 200

    script_data = script_response.json()
    script_id = script_data["script_id"]
    assert script_data["estimated_duration"] >= 180  # At least 3 minutes

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