"""
Integration tests for real AI processing progress tracking.
Tests detailed progress tracking with realistic timing per FR-004 and FR-007.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
import asyncio
from uuid import uuid4
from datetime import datetime

from src.services.progress_service import ProgressService
from src.lib.exceptions import (
    ProgressTrackingError,
    AIProcessingError,
    NoFallbackError
)


class TestAIProgressTrackingIntegration:
    """Integration tests for AI-powered progress tracking workflow."""

    def test_complete_ai_progress_workflow(self, ai_processing_stages):
        """Test complete AI progress tracking from start to completion."""
        # This test will fail until enhanced ProgressService is implemented
        progress_service = ProgressService()
        session_id = str(uuid4())

        # Start AI processing session
        progress_service.start_ai_session(
            session_id=session_id,
            processing_type="media_generation",
            expected_stages=ai_processing_stages
        )

        # Track progress through each AI stage
        stage_updates = []
        for stage in ai_processing_stages:
            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={
                    "stage_info": f"Processing {stage}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_details": {
                        "model_used": "gemini-2.5-flash",
                        "estimated_time": "2-5 seconds"
                    }
                }
            )
            stage_updates.append(update)

        # Verify detailed progress tracking per FR-007
        assert len(stage_updates) == len(ai_processing_stages)

        for i, update in enumerate(stage_updates):
            assert update["session_id"] == session_id
            assert update["stage"] == ai_processing_stages[i]
            assert "timestamp" in update
            assert "details" in update
            assert "processing_details" in update["details"]
            assert update["details"]["processing_details"]["model_used"] == "gemini-2.5-flash"

    def test_ai_progress_realistic_timing(self, ai_processing_stages):
        """Test progress tracking reflects realistic AI processing time per FR-004."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "script_analysis", ai_processing_stages)

        # Track realistic timing between stages
        stage_timings = []
        import time

        for stage in ai_processing_stages:
            start_time = time.time()

            # Simulate AI processing delay (realistic timing)
            time.sleep(1.5)  # Minimum realistic AI processing time

            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={
                    "processing_time": time.time() - start_time,
                    "ai_model": "gemini-2.5-flash"
                }
            )
            stage_timings.append(update["details"]["processing_time"])

        # Verify realistic timing (not subseconds)
        for timing in stage_timings:
            assert timing >= 1.0  # Each AI stage takes at least 1 second

        # Total processing should be realistic
        total_time = sum(stage_timings)
        assert total_time >= len(ai_processing_stages) * 1.0  # Minimum realistic time

    def test_ai_progress_detailed_debugging_info(self, ai_processing_stages):
        """Test detailed debugging information per FR-007."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "image_generation", ai_processing_stages)

        # Update with detailed debugging information
        detailed_update = progress_service.update_ai_progress(
            session_id=session_id,
            stage="generating_images",
            details={
                "ai_processing": {
                    "model": "gemini-2.5-flash",
                    "prompt": "Cyberpunk cityscape with neon lights",
                    "generation_config": {
                        "temperature": 0.7,
                        "top_p": 0.8,
                        "max_tokens": 1024
                    },
                    "api_call_duration": 3.2,
                    "token_usage": {
                        "input_tokens": 45,
                        "output_tokens": 120
                    }
                },
                "processing_stage": "ai_model_inference",
                "debug_info": {
                    "request_id": "req_123456",
                    "model_version": "2.5-flash-001",
                    "safety_ratings": [
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "probability": "NEGLIGIBLE"}
                    ]
                }
            }
        )

        # Verify comprehensive debugging details
        ai_details = detailed_update["details"]["ai_processing"]
        assert ai_details["model"] == "gemini-2.5-flash"
        assert ai_details["api_call_duration"] == 3.2
        assert "token_usage" in ai_details
        assert "debug_info" in detailed_update["details"]
        assert detailed_update["details"]["debug_info"]["request_id"] == "req_123456"

    def test_ai_progress_websocket_broadcasting(self, ai_processing_stages):
        """Test real-time WebSocket broadcasting of AI progress."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        # Mock WebSocket manager
        with patch.object(progress_service, 'websocket_manager') as mock_ws:
            mock_ws.broadcast_to_session = AsyncMock()

            progress_service.start_ai_session(session_id, "media_generation", ai_processing_stages)

            # Update progress - should broadcast via WebSocket
            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage="analyzing_script",
                details={
                    "ai_model": "gemini-2.5-flash",
                    "progress_percentage": 25,
                    "estimated_remaining": "8-12 seconds"
                }
            )

            # Verify WebSocket broadcast was called
            mock_ws.broadcast_to_session.assert_called_once()
            broadcast_call = mock_ws.broadcast_to_session.call_args[1]
            assert broadcast_call["session_id"] == session_id
            assert broadcast_call["message"]["type"] == "ai_progress_update"
            assert broadcast_call["message"]["data"]["stage"] == "analyzing_script"

    def test_ai_progress_error_handling_no_fallback(self, ai_processing_stages):
        """Test progress tracking during AI errors with no fallback per FR-006."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "script_analysis", ai_processing_stages)

        # Simulate AI processing error
        ai_error = AIProcessingError(
            "Gemini API temporarily unavailable",
            error_context={
                "api_error": "SERVICE_UNAVAILABLE",
                "retry_after": 30,
                "request_id": "req_789"
            }
        )

        # Update progress with error - should not fall back
        with pytest.raises(NoFallbackError) as exc_info:
            progress_service.update_ai_progress_with_error(
                session_id=session_id,
                stage="analyzing_script",
                error=ai_error,
                allow_fallback=False
            )

        # Verify no fallback behavior
        assert "no fallback behavior allowed" in str(exc_info.value)
        assert exc_info.value.processing_stage == "analyzing_script"
        assert isinstance(exc_info.value.original_error, AIProcessingError)

    def test_ai_progress_stage_transitions(self, ai_processing_stages):
        """Test proper stage transitions during AI processing."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "media_generation", ai_processing_stages)

        # Track stage transitions
        transitions = []
        for i, stage in enumerate(ai_processing_stages):
            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={
                    "stage_index": i,
                    "previous_stage": ai_processing_stages[i-1] if i > 0 else None,
                    "next_stage": ai_processing_stages[i+1] if i < len(ai_processing_stages)-1 else None
                }
            )
            transitions.append(update)

        # Verify proper stage sequencing
        for i, transition in enumerate(transitions):
            assert transition["stage"] == ai_processing_stages[i]
            if i > 0:
                assert transition["details"]["previous_stage"] == ai_processing_stages[i-1]
            if i < len(transitions) - 1:
                assert transition["details"]["next_stage"] == ai_processing_stages[i+1]

    def test_ai_progress_concurrent_sessions(self, ai_processing_stages):
        """Test progress tracking for multiple concurrent AI sessions."""
        progress_service = ProgressService()

        # Create multiple concurrent sessions
        session_ids = [str(uuid4()) for _ in range(3)]
        processing_types = ["script_analysis", "image_generation", "audio_generation"]

        # Start all sessions
        for session_id, proc_type in zip(session_ids, processing_types):
            progress_service.start_ai_session(session_id, proc_type, ai_processing_stages)

        # Update progress for all sessions concurrently
        concurrent_updates = []
        for session_id, proc_type in zip(session_ids, processing_types):
            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage="analyzing_script",
                details={
                    "processing_type": proc_type,
                    "model": "gemini-2.5-flash",
                    "concurrent_session": True
                }
            )
            concurrent_updates.append(update)

        # Verify each session maintains independent progress
        assert len(concurrent_updates) == 3
        for i, update in enumerate(concurrent_updates):
            assert update["session_id"] == session_ids[i]
            assert update["details"]["processing_type"] == processing_types[i]

    def test_ai_progress_session_cleanup(self, ai_processing_stages):
        """Test proper cleanup of completed AI sessions."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "media_generation", ai_processing_stages)

        # Complete all stages
        for stage in ai_processing_stages:
            progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={"stage_completed": True}
            )

        # Complete session
        completion_result = progress_service.complete_ai_session(
            session_id=session_id,
            final_result={
                "status": "completed",
                "total_processing_time": 15.7,
                "stages_completed": len(ai_processing_stages)
            }
        )

        # Verify session cleanup
        assert completion_result["session_id"] == session_id
        assert completion_result["status"] == "completed"
        assert completion_result["total_processing_time"] == 15.7

        # Session should be cleaned up from active sessions
        active_sessions = progress_service.get_active_ai_sessions()
        assert session_id not in [s["session_id"] for s in active_sessions]

    def test_ai_progress_recovery_after_interruption(self, ai_processing_stages):
        """Test progress recovery after AI processing interruption."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "script_analysis", ai_processing_stages)

        # Process some stages
        for stage in ai_processing_stages[:2]:
            progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={"completed": True}
            )

        # Simulate interruption and recovery
        recovery_result = progress_service.recover_ai_session(
            session_id=session_id,
            last_completed_stage="generating_prompts",
            recovery_context={
                "interruption_reason": "system_restart",
                "partial_results": {"scenes_analyzed": 2}
            }
        )

        # Verify recovery maintains context
        assert recovery_result["session_id"] == session_id
        assert recovery_result["last_completed_stage"] == "generating_prompts"
        assert recovery_result["recovery_context"]["partial_results"]["scenes_analyzed"] == 2

    def test_ai_progress_performance_metrics(self, ai_processing_stages):
        """Test collection of AI processing performance metrics."""
        progress_service = ProgressService()
        session_id = str(uuid4())

        progress_service.start_ai_session(session_id, "media_generation", ai_processing_stages)

        # Track performance metrics during processing
        import time
        performance_data = []

        for stage in ai_processing_stages:
            start_time = time.time()
            time.sleep(1.2)  # Simulate AI processing

            update = progress_service.update_ai_progress(
                session_id=session_id,
                stage=stage,
                details={
                    "performance_metrics": {
                        "stage_duration": time.time() - start_time,
                        "memory_usage": 245.6,  # MB
                        "api_calls": 1,
                        "tokens_processed": 150
                    }
                }
            )
            performance_data.append(update["details"]["performance_metrics"])

        # Verify performance metrics collection
        assert len(performance_data) == len(ai_processing_stages)
        for metrics in performance_data:
            assert metrics["stage_duration"] >= 1.0  # Realistic timing
            assert "memory_usage" in metrics
            assert "api_calls" in metrics
            assert "tokens_processed" in metrics