import pytest
from fastapi.testclient import TestClient
import uuid

# Import will fail initially - this is expected for TDD
try:
    from backend.main import app
    client = TestClient(app)
except ImportError:
    # For TDD - these tests MUST fail initially
    client = None


def test_delete_script_by_id_contract():
    """Contract test for DELETE /api/v1/scripts/{script_id}"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test with a valid script ID (will need to exist in test data)
    script_id = str(uuid.uuid4())

    response = client.delete(f"/api/v1/scripts/{script_id}")

    # This test MUST fail initially - endpoint not implemented yet
    assert response.status_code == 204

    # 204 No Content should have empty response body
    assert response.content == b""


def test_delete_script_not_found_contract():
    """Contract test for DELETE /api/v1/scripts/{script_id} with non-existent ID"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test with non-existent script ID
    non_existent_id = str(uuid.uuid4())

    response = client.delete(f"/api/v1/scripts/{non_existent_id}")

    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "timestamp" in data


def test_delete_script_invalid_uuid_contract():
    """Contract test for DELETE /api/v1/scripts/{script_id} with invalid UUID format"""
    if client is None:
        pytest.fail("API not implemented yet - TDD requirement")

    # Test with invalid UUID format
    invalid_id = "not-a-valid-uuid"

    response = client.delete(f"/api/v1/scripts/{invalid_id}")

    assert response.status_code == 400

    data = response.json()
    assert "error" in data
    assert "message" in data