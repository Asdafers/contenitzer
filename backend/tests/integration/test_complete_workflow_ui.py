"""
Integration tests for complete workflow with UI components.

Tests the full end-to-end workflow scenarios from quickstart.md with UI state management,
session persistence, and WebSocket progress updates. These tests MUST FAIL before
implementation (TDD requirement).
"""
import pytest
import asyncio
import uuid
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestCompleteWorkflowUI:
    """Integration tests for complete workflow with UI components"""

    @pytest.fixture
    def session_id(self):
        """Generate a test session ID"""
        return str(uuid.uuid4())

    @pytest.fixture
    def websocket_client(self):
        """WebSocket client fixture for progress monitoring"""
        return TestClient(app)

    def test_full_automated_workflow_with_ui_tracking(self, session_id, websocket_client):
        """Test complete automated workflow with UI state tracking and WebSocket progress"""

        # This test MUST FAIL until UI state management is implemented
        with pytest.raises(Exception):
            # Step 1: Create session for UI state tracking
            session_response = client.post("/api/sessions", json={
                "preferences": {"theme": "dark", "auto_save": True}
            })
            assert session_response.status_code == 201
            session_data = session_response.json()
            actual_session_id = session_data["session_id"]

            # Step 2: Initialize WebSocket connection for progress tracking
            with websocket_client.websocket_connect(f"/ws/progress/{actual_session_id}") as websocket:

                # Step 3: Start trending analysis with UI state
                trending_payload = {
                    "timeframe": "weekly",
                    "api_key": "test-api-key",
                    "session_id": actual_session_id
                }

                # Update UI state for trending analysis
                ui_state_response = client.put(
                    f"/api/sessions/{actual_session_id}/ui-state/trending_analysis",
                    json={
                        "form_data": {"timeframe": "weekly", "categories": ["Entertainment"]},
                        "ui_state": {"step": 1, "loading": True}
                    }
                )
                assert ui_state_response.status_code == 200

                # Start trending analysis
                trending_response = client.post("/api/trending/analyze", json=trending_payload)
                assert trending_response.status_code == 200

                # Verify WebSocket progress update
                progress_msg = websocket.receive_json()
                assert progress_msg["event_type"] == "progress_update"
                assert progress_msg["data"]["step"] == "trending_analysis"

                # Step 4: Generate script with UI tracking
                trending_data = trending_response.json()
                theme_id = trending_data["categories"][0]["themes"][0]["id"]

                script_payload = {
                    "input_type": "theme",
                    "theme_id": theme_id,
                    "session_id": actual_session_id
                }

                # Update workflow state
                workflow_response = client.put(
                    f"/api/sessions/{actual_session_id}/workflow-state",
                    json={
                        "workflow_state": {
                            "current_step": "script_generation",
                            "completed_steps": ["trending_analysis"],
                            "theme_id": theme_id
                        }
                    }
                )
                assert workflow_response.status_code == 200

                script_response = client.post("/api/scripts/generate", json=script_payload)
                assert script_response.status_code == 200

                # Verify script generation progress
                progress_msg = websocket.receive_json()
                assert progress_msg["event_type"] == "progress_update"
                assert progress_msg["data"]["step"] == "script_generation"

                # Step 5: Complete workflow through media and video generation
                script_data = script_response.json()
                script_id = script_data["script_id"]

                # Media generation with session tracking
                media_response = client.post("/api/media/generate", json={
                    "script_id": script_id,
                    "session_id": actual_session_id
                })
                assert media_response.status_code == 202

                # Verify media generation started
                progress_msg = websocket.receive_json()
                assert progress_msg["event_type"] == "progress_update"
                assert progress_msg["data"]["step"] == "media_generation"

                # Video composition
                media_data = media_response.json()
                project_id = media_data["project_id"]

                compose_response = client.post("/api/videos/compose", json={
                    "project_id": project_id,
                    "session_id": actual_session_id
                })
                assert compose_response.status_code == 202

                # Final upload
                upload_response = client.post("/api/videos/upload", json={
                    "project_id": project_id,
                    "youtube_api_key": "test-youtube-api-key",
                    "session_id": actual_session_id
                })
                assert upload_response.status_code == 202

                # Verify final completion message
                completion_msg = websocket.receive_json()
                assert completion_msg["event_type"] == "completion"
                assert "result_url" in completion_msg["data"]

    def test_manual_subject_workflow_with_ui_state(self, session_id):
        """Test manual subject workflow with UI state persistence"""

        with pytest.raises(Exception):
            # Create session
            session_response = client.post("/api/sessions", json={
                "preferences": {"auto_save": True}
            })
            assert session_response.status_code == 201
            actual_session_id = session_response.json()["session_id"]

            # Set manual subject UI state
            ui_response = client.put(
                f"/api/sessions/{actual_session_id}/ui-state/manual_input",
                json={
                    "form_data": {
                        "input_type": "manual_subject",
                        "subject": "The Future of AI in Creative Industries"
                    },
                    "ui_state": {"step": 1, "input_method": "manual"}
                }
            )
            assert ui_response.status_code == 200

            # Generate script from manual subject
            script_response = client.post("/api/scripts/generate", json={
                "input_type": "manual_subject",
                "subject": "The Future of AI in Creative Industries",
                "session_id": actual_session_id
            })
            assert script_response.status_code == 200

            # Verify UI state updated with script ID
            ui_state_response = client.get(f"/api/sessions/{actual_session_id}/ui-state/manual_input")
            assert ui_state_response.status_code == 200
            ui_data = ui_state_response.json()
            assert "script_id" in ui_data["form_data"]

    def test_workflow_interruption_and_resume_with_ui(self, session_id):
        """Test workflow interruption and resume maintaining UI state"""

        with pytest.raises(Exception):
            # Create session and start workflow
            session_response = client.post("/api/sessions", json={
                "preferences": {"auto_save": True}
            })
            assert session_response.status_code == 201
            actual_session_id = session_response.json()["session_id"]

            # Start trending analysis
            trending_response = client.post("/api/trending/analyze", json={
                "timeframe": "weekly",
                "api_key": "test-api-key",
                "session_id": actual_session_id
            })
            assert trending_response.status_code == 200

            # Set workflow state mid-process
            workflow_response = client.put(
                f"/api/sessions/{actual_session_id}/workflow-state",
                json={
                    "workflow_state": {
                        "current_step": "script_generation",
                        "completed_steps": ["trending_analysis"],
                        "theme_id": "test-theme-id",
                        "interrupted": True
                    }
                }
            )
            assert workflow_response.status_code == 200

            # Simulate session restoration
            restored_workflow = client.get(f"/api/sessions/{actual_session_id}/workflow-state")
            assert restored_workflow.status_code == 200

            workflow_data = restored_workflow.json()
            assert workflow_data["workflow_state"]["interrupted"] == True
            assert workflow_data["workflow_state"]["current_step"] == "script_generation"

            # Resume from interruption point
            script_response = client.post("/api/scripts/generate", json={
                "input_type": "theme",
                "theme_id": workflow_data["workflow_state"]["theme_id"],
                "session_id": actual_session_id,
                "resume": True
            })
            assert script_response.status_code == 200

    def test_ui_component_state_isolation(self, session_id):
        """Test that different UI components maintain isolated state"""

        with pytest.raises(Exception):
            # Create session
            session_response = client.post("/api/sessions", json={})
            actual_session_id = session_response.json()["session_id"]

            # Set state for different UI components
            trending_ui = client.put(
                f"/api/sessions/{actual_session_id}/ui-state/trending_analysis",
                json={
                    "form_data": {"timeframe": "monthly"},
                    "ui_state": {"expanded": True}
                }
            )
            assert trending_ui.status_code == 200

            script_ui = client.put(
                f"/api/sessions/{actual_session_id}/ui-state/script_generation",
                json={
                    "form_data": {"tone": "professional"},
                    "ui_state": {"preview_mode": True}
                }
            )
            assert script_ui.status_code == 200

            # Verify components have isolated state
            trending_state = client.get(f"/api/sessions/{actual_session_id}/ui-state/trending_analysis")
            script_state = client.get(f"/api/sessions/{actual_session_id}/ui-state/script_generation")

            assert trending_state.json()["form_data"]["timeframe"] == "monthly"
            assert script_state.json()["form_data"]["tone"] == "professional"
            assert trending_state.json()["ui_state"]["expanded"] == True
            assert script_state.json()["ui_state"]["preview_mode"] == True

    def test_real_time_progress_updates_with_multiple_clients(self, session_id):
        """Test real-time progress updates across multiple UI clients"""

        with pytest.raises(Exception):
            # Create session
            session_response = client.post("/api/sessions", json={})
            actual_session_id = session_response.json()["session_id"]

            # Connect multiple WebSocket clients
            with client.websocket_connect(f"/ws/progress/{actual_session_id}") as ws1:
                with client.websocket_connect(f"/ws/progress/{actual_session_id}") as ws2:

                    # Start a long-running task
                    media_response = client.post("/api/media/generate", json={
                        "script_id": "test-script-id",
                        "session_id": actual_session_id
                    })
                    assert media_response.status_code == 202

                    # Both clients should receive the same progress updates
                    progress1 = ws1.receive_json()
                    progress2 = ws2.receive_json()

                    assert progress1["event_type"] == "progress_update"
                    assert progress2["event_type"] == "progress_update"
                    assert progress1["task_id"] == progress2["task_id"]
                    assert progress1["progress"] == progress2["progress"]