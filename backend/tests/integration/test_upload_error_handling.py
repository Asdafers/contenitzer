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


def test_upload_error_empty_content_handling():
    """Integration test for error handling with empty content"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    # Test empty string content
    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": "",
            "workflow_id": workflow_id
        }
    )

    # This test MUST fail initially - endpoint not implemented yet
    assert upload_response.status_code == 422

    error_data = upload_response.json()
    assert "error" in error_data
    assert "empty" in error_data["message"].lower()
    assert "details" in error_data

    # Test whitespace-only content
    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": "   \n\t  \n  ",
            "workflow_id": workflow_id
        }
    )
    assert upload_response2.status_code == 422

    error_data2 = upload_response2.json()
    assert "empty" in error_data2["message"].lower()


def test_upload_error_file_size_limit():
    """Integration test for error handling with file size limits"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    # Test content exactly at limit (50KB = 51200 characters)
    at_limit_content = "x" * 51200
    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": at_limit_content,
            "workflow_id": workflow_id
        }
    )
    # Should be accepted at exactly the limit
    assert upload_response.status_code == 201

    # Test content over limit (50KB + 1)
    over_limit_content = "x" * 51201
    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": over_limit_content,
            "workflow_id": workflow_id
        }
    )
    assert upload_response2.status_code == 413

    error_data = upload_response2.json()
    assert "error" in error_data
    assert ("too large" in error_data["message"].lower() or
            "exceeds" in error_data["message"].lower())


def test_upload_error_invalid_workflow_id():
    """Integration test for error handling with invalid workflow IDs"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    test_content = "Speaker 1: Test content for invalid workflow ID."

    # Test with malformed UUID
    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content,
            "workflow_id": "not-a-valid-uuid"
        }
    )
    assert upload_response.status_code == 400

    error_data = upload_response.json()
    assert "error" in error_data
    assert ("invalid" in error_data["message"].lower() or
            "uuid" in error_data["message"].lower())

    # Test with missing workflow_id
    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={"content": test_content}
    )
    assert upload_response2.status_code == 400

    error_data2 = upload_response2.json()
    assert "error" in error_data2


def test_upload_error_malicious_content_handling():
    """Integration test for error handling with potentially malicious content"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    # Test content with script tags
    malicious_content1 = """Speaker 1: Welcome to the show.
<script>alert('xss')</script>
Speaker 2: Thanks for having me."""

    upload_response1 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": malicious_content1,
            "workflow_id": workflow_id
        }
    )
    assert upload_response1.status_code == 422

    error_data1 = upload_response1.json()
    assert "error" in error_data1
    assert ("harmful" in error_data1["message"].lower() or
            "invalid" in error_data1["message"].lower())

    # Test content with PHP tags
    malicious_content2 = """Speaker 1: Today we discuss coding.
<?php echo 'dangerous code'; ?>
Speaker 2: Indeed."""

    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": malicious_content2,
            "workflow_id": workflow_id
        }
    )
    assert upload_response2.status_code == 422

    # Test content with shell script indicators
    malicious_content3 = """#!/bin/bash
rm -rf /
Speaker 1: This is not a real script."""

    upload_response3 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": malicious_content3,
            "workflow_id": workflow_id
        }
    )
    assert upload_response3.status_code == 422


def test_upload_error_invalid_file_type():
    """Integration test for error handling with invalid file types"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    # Test with binary file content (simulated)
    binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'  # PNG header
    binary_file = BytesIO(binary_content)

    upload_response = client.post(
        "/api/v1/scripts/upload",
        files={"file": ("image.png", binary_file, "image/png")},
        data={"workflow_id": workflow_id}
    )
    assert upload_response.status_code == 400

    error_data = upload_response.json()
    assert "error" in error_data
    assert ("type" in error_data["message"].lower() or
            "format" in error_data["message"].lower())


def test_upload_error_concurrent_uploads():
    """Integration test for error handling with concurrent uploads to same workflow"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())
    test_content = "Speaker 1: Concurrent upload test.\nSpeaker 2: Testing race conditions."

    # Simulate concurrent uploads (in real scenario, these would be truly concurrent)
    # For now, we test sequential uploads to same workflow
    upload_response1 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content,
            "workflow_id": workflow_id
        }
    )
    assert upload_response1.status_code == 201

    # Second upload to same workflow should either:
    # 1. Replace the first upload, or
    # 2. Be rejected with appropriate error
    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content + " (second upload)",
            "workflow_id": workflow_id
        }
    )

    # Either accept (201) or reject (409 conflict)
    assert upload_response2.status_code in [201, 409]

    if upload_response2.status_code == 409:
        error_data = upload_response2.json()
        assert "error" in error_data
        assert ("conflict" in error_data["message"].lower() or
                "already" in error_data["message"].lower())


def test_upload_error_database_constraint_violations():
    """Integration test for error handling with database constraint violations"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test with extremely long workflow_id that might cause database issues
    # This tests the system's robustness against database constraints
    invalid_workflow_id = "x" * 1000  # Assuming UUID field has length limits

    test_content = "Speaker 1: Testing database constraints."

    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": test_content,
            "workflow_id": invalid_workflow_id
        }
    )

    # Should be rejected due to invalid UUID format before database constraints
    assert upload_response.status_code == 400

    error_data = upload_response.json()
    assert "error" in error_data


def test_upload_error_recovery_and_cleanup():
    """Integration test for error recovery and cleanup after failed uploads"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    workflow_id = str(uuid.uuid4())

    # Attempt invalid upload
    upload_response = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": "",  # Invalid empty content
            "workflow_id": workflow_id
        }
    )
    assert upload_response.status_code == 422

    # Verify no partial data was saved
    with get_db_session() as db:
        uploaded_scripts = db.query(UploadedScript).filter(
            UploadedScript.workflow_id == workflow_id
        ).all()
        assert len(uploaded_scripts) == 0

    # Follow up with valid upload to same workflow
    valid_content = "Speaker 1: This is valid content after cleanup."
    upload_response2 = client.post(
        "/api/v1/scripts/upload",
        data={
            "content": valid_content,
            "workflow_id": workflow_id
        }
    )
    assert upload_response2.status_code == 201

    # Verify valid upload succeeded
    script_id = upload_response2.json()["script_id"]
    get_response = client.get(f"/api/v1/scripts/{script_id}")
    assert get_response.status_code == 200
    assert get_response.json()["content"] == valid_content