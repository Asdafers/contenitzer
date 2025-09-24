import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import uuid

# Import FastAPI app and create test client
try:
    from main import app
    client = TestClient(app)
except ImportError as e:
    print(f"Import error: {e}")
    client = None


def test_script_upload_with_file_contract():
    """Contract test for POST /api/v1/scripts/upload with file upload"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Create test file content
    test_content = "Speaker 1: Welcome to our show about AI.\nSpeaker 2: Thanks for having me today."
    test_file = BytesIO(test_content.encode('utf-8'))

    # Test data
    workflow_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/scripts/upload",
        files={"file": ("test_script.txt", test_file, "text/plain")},
        data={"workflow_id": workflow_id}
    )

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 201

    data = response.json()
    assert "script_id" in data
    assert "status" in data
    assert data["status"] in ["PENDING", "VALID", "INVALID"]
    assert "message" in data
    assert "content_length" in data
    assert "upload_timestamp" in data
    assert isinstance(data["content_length"], int)
    assert data["content_length"] > 0


def test_script_upload_with_text_content_contract():
    """Contract test for POST /api/v1/scripts/upload with text content"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test data
    workflow_id = str(uuid.uuid4())
    test_content = "Speaker 1: This is a test script.\nSpeaker 2: Indeed it is."

    response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content,
            "workflow_id": workflow_id
        }
    )

    assert response.status_code == 201

    data = response.json()
    assert "script_id" in data
    assert "status" in data
    assert data["status"] in ["PENDING", "VALID", "INVALID"]
    assert "message" in data
    assert "content_length" in data
    assert data["content_length"] == len(test_content)


def test_script_upload_validation_error_contract():
    """Contract test for POST /api/v1/scripts/upload with validation errors"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test with empty content
    workflow_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": "",
            "workflow_id": workflow_id
        }
    )

    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "details" in data
    assert isinstance(data["details"], list)


def test_script_upload_file_too_large_contract():
    """Contract test for POST /api/v1/scripts/upload with file too large"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Create content larger than 50KB
    large_content = "x" * 60000  # 60KB
    workflow_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": large_content,
            "workflow_id": workflow_id
        }
    )

    assert response.status_code == 413

    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "file too large" in data["message"].lower()


def test_script_upload_missing_workflow_id_contract():
    """Contract test for POST /api/v1/scripts/upload without workflow_id"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    test_content = "Speaker 1: Test content"

    response = client.post(
        "/api/v1/scripts/upload",
        data={"content": test_content}
        # Missing workflow_id
    )

    assert response.status_code == 400

    data = response.json()
    assert "error" in data
    assert "message" in data


def test_script_upload_no_content_or_file_contract():
    """Contract test for POST /api/v1/scripts/upload without content or file"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/scripts/upload",
        data={"workflow_id": workflow_id}
        # Missing both content and file
    )

    assert response.status_code == 400

    data = response.json()
    assert "error" in data
    assert "message" in data