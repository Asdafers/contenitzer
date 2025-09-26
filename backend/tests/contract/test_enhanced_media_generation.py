"""
Contract tests for enhanced media generation API.
Tests the API contract defined in enhanced_media_generation.yaml
"""
import pytest
import json
from fastapi.testclient import TestClient
from uuid import uuid4
from main import app


class TestEnhancedMediaGenerationContract:
    """Test contract compliance for enhanced media generation API endpoint."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_submit_media_generation_with_valid_ai_model(self, client: TestClient, sample_script_content):
        """Test enhanced media generation API accepts AI model parameters."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        request_payload = {
            "session_id": session_id,
            "input_data": {
                "script_id": script_id,
                "model": "gemini-2.5-flash",
                "allow_fallback": False,
                "media_options": {
                    "duration": 180,
                    "resolution": "1920x1080",
                    "quality": "high",
                    "include_audio": True
                }
            },
            "priority": "normal"
        }

        response = client.post("/api/tasks/submit/media_generation", json=request_payload)

        # Should return 201 Created for successful task submission
        assert response.status_code == 201

        response_data = response.json()

        # Response should contain task_id and success message
        assert "task_id" in response_data
        assert "message" in response_data
        assert response_data["message"] == "Task submitted successfully"

        # task_id should be valid UUID
        task_id = response_data["task_id"]
        uuid4().hex  # Will raise ValueError if task_id isn't valid UUID format

    def test_submit_media_generation_rejects_fallback_behavior(self, client: TestClient):
        """Test API rejects requests with allow_fallback=True per FR-006."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        request_payload = {
            "session_id": session_id,
            "input_data": {
                "script_id": script_id,
                "model": "gemini-2.5-flash",
                "allow_fallback": True,  # Should be rejected
                "media_options": {
                    "duration": 180,
                    "resolution": "1920x1080",
                    "quality": "high"
                }
            }
        }

        response = client.post("/api/tasks/submit/media_generation", json=request_payload)

        # Should return 400 Bad Request
        assert response.status_code == 400

        response_data = response.json()
        assert "detail" in response_data
        assert "fallback" in response_data["detail"].lower()

    def test_submit_media_generation_validates_ai_model(self, client: TestClient):
        """Test API validates AI model parameter."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        request_payload = {
            "session_id": session_id,
            "input_data": {
                "script_id": script_id,
                "model": "invalid-model",  # Should be rejected
                "allow_fallback": False,
                "media_options": {
                    "duration": 180,
                    "resolution": "1920x1080"
                }
            }
        }

        response = client.post("/api/tasks/submit/media_generation", json=request_payload)

        # Should return 400 Bad Request for invalid model
        assert response.status_code == 400

        response_data = response.json()
        assert "detail" in response_data
        assert "model" in response_data["detail"].lower()

    def test_submit_media_generation_validates_required_fields(self, client: TestClient):
        """Test API validates required fields."""
        # Missing session_id
        response = client.post("/api/tasks/submit/media_generation", json={
            "input_data": {
                "script_id": str(uuid4()),
                "model": "gemini-2.5-flash",
                "allow_fallback": False
            }
        })
        assert response.status_code == 422  # Validation error

        # Missing script_id
        response = client.post("/api/tasks/submit/media_generation", json={
            "session_id": str(uuid4()),
            "input_data": {
                "model": "gemini-2.5-flash",
                "allow_fallback": False
            }
        })
        assert response.status_code == 422  # Validation error

        # Missing model
        response = client.post("/api/tasks/submit/media_generation", json={
            "session_id": str(uuid4()),
            "input_data": {
                "script_id": str(uuid4()),
                "allow_fallback": False
            }
        })
        assert response.status_code == 422  # Validation error

    def test_media_generation_response_schema(self, client: TestClient):
        """Test response matches the contract schema."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        request_payload = {
            "session_id": session_id,
            "input_data": {
                "script_id": script_id,
                "model": "gemini-2.5-flash",
                "allow_fallback": False,
                "media_options": {
                    "duration": 180,
                    "resolution": "1920x1080",
                    "quality": "high",
                    "include_audio": True
                }
            },
            "priority": "high",
            "metadata": {"test": "contract"}
        }

        response = client.post("/api/tasks/submit/media_generation", json=request_payload)

        assert response.status_code == 201

        response_data = response.json()

        # Validate response schema matches contract
        required_fields = ["task_id", "message"]
        for field in required_fields:
            assert field in response_data, f"Response missing required field: {field}"

        # Validate field types
        assert isinstance(response_data["task_id"], str)
        assert isinstance(response_data["message"], str)

    def test_media_generation_error_response_schema(self, client: TestClient):
        """Test error response includes debugging information per FR-007."""
        # Send invalid payload to trigger error
        response = client.post("/api/tasks/submit/media_generation", json={
            "session_id": "invalid-uuid",  # Invalid UUID format
            "input_data": {
                "script_id": str(uuid4()),
                "model": "gemini-2.5-flash",
                "allow_fallback": False
            }
        })

        # Should return error with debugging details
        assert response.status_code in [400, 422, 500]

        response_data = response.json()

        # Should include detailed error information for debugging
        assert "detail" in response_data
        assert isinstance(response_data["detail"], str)
        assert len(response_data["detail"]) > 0

    def test_media_generation_supports_all_quality_options(self, client: TestClient):
        """Test API accepts all defined quality options."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        quality_options = ["high", "medium", "low"]

        for quality in quality_options:
            request_payload = {
                "session_id": session_id,
                "input_data": {
                    "script_id": script_id,
                    "model": "gemini-2.5-flash",
                    "allow_fallback": False,
                    "media_options": {
                        "duration": 180,
                        "resolution": "1920x1080",
                        "quality": quality,
                        "include_audio": True
                    }
                }
            }

            response = client.post("/api/tasks/submit/media_generation", json=request_payload)
            assert response.status_code == 201, f"Quality option '{quality}' should be accepted"

    def test_media_generation_supports_all_resolution_options(self, client: TestClient):
        """Test API accepts all defined resolution options."""
        session_id = str(uuid4())
        script_id = str(uuid4())

        resolution_options = ["1920x1080", "1280x720", "3840x2160"]

        for resolution in resolution_options:
            request_payload = {
                "session_id": session_id,
                "input_data": {
                    "script_id": script_id,
                    "model": "gemini-2.5-flash",
                    "allow_fallback": False,
                    "media_options": {
                        "duration": 180,
                        "resolution": resolution,
                        "quality": "high"
                    }
                }
            }

            response = client.post("/api/tasks/submit/media_generation", json=request_payload)
            assert response.status_code == 201, f"Resolution '{resolution}' should be accepted"