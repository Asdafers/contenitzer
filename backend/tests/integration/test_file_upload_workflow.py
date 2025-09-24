import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import uuid

# Import will fail initially - this is expected for TDD
try:
    from backend.main import app
    from backend.src.lib.database import get_db_session
    from backend.src.models import Workflow, UploadedScript
    client = TestClient(app)
except ImportError:
    # For TDD - these tests MUST fail initially
    client = None


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing"""
    content = """Speaker 1: Welcome to our show about artificial intelligence and its impact on content creation.

Speaker 2: Thank you for having me. I'm excited to discuss how AI is revolutionizing the way we create and consume content.

Speaker 1: Let's start with the basics. How do you see AI changing the content creation landscape?

Speaker 2: AI is making content creation more accessible and efficient. Tools like GPT models can help writers overcome writer's block, generate ideas, and even create entire articles or scripts.

Speaker 1: That's fascinating. What about the quality of AI-generated content?

Speaker 2: The quality has improved dramatically in recent years. While AI can't replace human creativity entirely, it's becoming an excellent collaborative tool."""

    return BytesIO(content.encode('utf-8'))


def test_complete_file_upload_workflow():
    """Integration test for complete file upload workflow from start to finish"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Step 1: Create a new workflow
    workflow_response = client.post("/api/v1/workflows", json={
        "title": "Test Upload Workflow",
        "description": "Testing file upload workflow"
    })

    # This test MUST fail initially - endpoints not implemented yet
    assert workflow_response.status_code == 201
    workflow_data = workflow_response.json()
    workflow_id = workflow_data["workflow_id"]

    # Step 2: Set workflow mode to UPLOAD
    mode_response = client.put(f"/api/v1/workflows/{workflow_id}/mode", json={
        "mode": "UPLOAD"
    })
    assert mode_response.status_code == 200
    mode_data = mode_response.json()
    assert mode_data["mode"] == "UPLOAD"

    # Step 3: Upload script file
    test_content = "Speaker 1: This is a test script.\nSpeaker 2: Indeed it is."
    test_file = BytesIO(test_content.encode('utf-8'))

    upload_response = client.post(
        "/api/v1/scripts/upload",
        files={"file": ("test_script.txt", test_file, "text/plain")},
        data={"workflow_id": workflow_id}
    )
    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    script_id = upload_data["script_id"]

    # Step 4: Verify script was uploaded and validated
    assert upload_data["status"] in ["PENDING", "VALID"]
    assert upload_data["content_length"] == len(test_content)

    # Step 5: Retrieve uploaded script
    get_response = client.get(f"/api/v1/scripts/{script_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["content"] == test_content
    assert get_data["workflow_id"] == workflow_id

    # Step 6: Verify workflow is ready for next steps
    workflow_status_response = client.get(f"/api/v1/workflows/{workflow_id}")
    assert workflow_status_response.status_code == 200
    status_data = workflow_status_response.json()
    assert status_data["mode"] == "UPLOAD"
    assert status_data["script_source"] == "UPLOADED"
    assert status_data["skip_research"] == True
    assert status_data["skip_generation"] == True


def test_file_upload_workflow_with_large_file():
    """Integration test for file upload workflow with near-limit file size"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Create workflow
    workflow_response = client.post("/api/v1/workflows", json={
        "title": "Large File Test Workflow"
    })
    assert workflow_response.status_code == 201
    workflow_id = workflow_response.json()["workflow_id"]

    # Set to upload mode
    mode_response = client.put(f"/api/v1/workflows/{workflow_id}/mode", json={
        "mode": "UPLOAD"
    })
    assert mode_response.status_code == 200

    # Create large content (49KB - just under limit)
    large_content = "Speaker 1: This is a large script. " * 1400  # ~49KB
    test_file = BytesIO(large_content.encode('utf-8'))

    # Upload large file
    upload_response = client.post(
        "/api/v1/scripts/upload",
        files={"file": ("large_script.txt", test_file, "text/plain")},
        data={"workflow_id": workflow_id}
    )
    assert upload_response.status_code == 201

    upload_data = upload_response.json()
    assert upload_data["status"] in ["PENDING", "VALID"]
    assert upload_data["content_length"] < 51200  # Under 50KB limit


def test_file_upload_workflow_validation_failure():
    """Integration test for file upload workflow with validation failures"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Create workflow
    workflow_response = client.post("/api/v1/workflows", json={
        "title": "Validation Failure Test"
    })
    assert workflow_response.status_code == 201
    workflow_id = workflow_response.json()["workflow_id"]

    # Set to upload mode
    mode_response = client.put(f"/api/v1/workflows/{workflow_id}/mode", json={
        "mode": "UPLOAD"
    })
    assert mode_response.status_code == 200

    # Try to upload empty file
    empty_file = BytesIO(b"")
    upload_response = client.post(
        "/api/v1/scripts/upload",
        files={"file": ("empty.txt", empty_file, "text/plain")},
        data={"workflow_id": workflow_id}
    )
    assert upload_response.status_code == 422

    error_data = upload_response.json()
    assert "error" in error_data
    assert "empty" in error_data["message"].lower()


def test_file_upload_workflow_database_consistency():
    """Integration test verifying database consistency during file upload workflow"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # This test will verify that database state remains consistent
    # throughout the upload workflow process

    workflow_id = str(uuid.uuid4())
    test_content = "Speaker 1: Database consistency test.\nSpeaker 2: Checking data integrity."

    # Upload script
    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content,
            "workflow_id": workflow_id
        }
    )
    assert upload_response.status_code == 201
    script_id = upload_response.json()["script_id"]

    # Verify database state directly
    with get_db_session() as db:
        # Check uploaded script exists
        uploaded_script = db.query(UploadedScript).filter(
            UploadedScript.id == script_id
        ).first()
        assert uploaded_script is not None
        assert uploaded_script.content == test_content
        assert uploaded_script.workflow_id == workflow_id

        # Check workflow state if workflow was created
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id
        ).first()
        if workflow:
            assert workflow.mode == "UPLOAD"
            assert workflow.uploaded_script_id == script_id