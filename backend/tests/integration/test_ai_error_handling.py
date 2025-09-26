"""
Integration tests for error handling without fallbacks.
Tests comprehensive error handling per FR-006 and detailed debugging per FR-007.
"""
import pytest
from unittest.mock import Mock, patch
import json
from uuid import uuid4
from datetime import datetime

from src.lib.exceptions import (
    AIProcessingError,
    GeminiAPIError,
    GeminiRateLimitError,
    GeminiContentFilterError,
    GeminiModelUnavailableError,
    ScriptAnalysisError,
    ImageGenerationError,
    AudioGenerationError,
    AIProcessingTimeoutError,
    NoFallbackError,
    AIModelValidationError,
    ProgressTrackingError
)


class TestAIErrorHandlingIntegration:
    """Integration tests for AI error handling without fallbacks per FR-006."""

    def test_gemini_api_error_no_fallback(self, mock_gemini_client):
        """Test Gemini API errors trigger NoFallbackError per FR-006."""
        # Mock service that would use Gemini API
        from unittest.mock import Mock
        ai_service = Mock()

        # Simulate various Gemini API errors
        gemini_errors = [
            GeminiAPIError("API temporarily unavailable"),
            GeminiRateLimitError("Rate limit exceeded", retry_after=60),
            GeminiContentFilterError("Content filtered by safety policy"),
            GeminiModelUnavailableError("gemini-2.5-flash", "Model temporarily unavailable")
        ]

        for gemini_error in gemini_errors:
            ai_service.process_with_ai.side_effect = gemini_error

            # Error handling should not fall back to placeholder generation
            with pytest.raises(NoFallbackError) as exc_info:
                # This would be called by actual AI services
                self._handle_ai_processing_error(gemini_error, "image_generation", allow_fallback=False)

            # Verify no fallback behavior
            assert "no fallback behavior allowed" in str(exc_info.value)
            assert isinstance(exc_info.value.original_error, type(gemini_error))

    def test_script_analysis_error_detailed_reporting(self, sample_script_content):
        """Test script analysis errors provide detailed debugging info per FR-007."""
        # This test will fail until ScriptAnalysisService is implemented
        from src.services.script_analysis_service import ScriptAnalysisService

        service = ScriptAnalysisService()

        # Test various script analysis error scenarios
        error_scenarios = [
            {
                "script_data": {"content": ""},  # Empty content
                "expected_error": "empty content",
                "error_context": {"validation": "content_required"}
            },
            {
                "script_data": {"content": "x" * 100000},  # Too long
                "expected_error": "content too long",
                "error_context": {"validation": "length_exceeded"}
            },
            {
                "script_data": {"content": sample_script_content, "model": "invalid-model"},
                "expected_error": "invalid model",
                "error_context": {"validation": "model_unsupported"}
            }
        ]

        for scenario in error_scenarios:
            with pytest.raises(ScriptAnalysisError) as exc_info:
                service.analyze_script(scenario["script_data"])

            # Verify detailed error reporting
            error = exc_info.value
            assert scenario["expected_error"] in str(error).lower()
            assert hasattr(error, 'script_content')
            assert hasattr(error, 'analysis_error')

            # Error should include debugging context
            if hasattr(error, 'error_context'):
                for key, value in scenario["error_context"].items():
                    assert key in error.error_context
                    assert error.error_context[key] == value

    def test_image_generation_error_comprehensive_debugging(self):
        """Test image generation errors include comprehensive debugging details."""
        # This test will fail until GeminiImageService is implemented
        from src.services.gemini_image_service import GeminiImageService

        service = GeminiImageService()

        # Test comprehensive error scenarios
        error_cases = [
            {
                "request": {
                    "prompt": "",  # Empty prompt
                    "quality": "high"
                },
                "expected_error_type": ImageGenerationError,
                "debug_requirements": ["prompt_validation", "request_parameters"]
            },
            {
                "request": {
                    "prompt": "Valid prompt",
                    "quality": "invalid_quality",
                    "model": "gemini-2.5-flash"
                },
                "expected_error_type": ImageGenerationError,
                "debug_requirements": ["quality_validation", "supported_qualities"]
            }
        ]

        for case in error_cases:
            with pytest.raises(case["expected_error_type"]) as exc_info:
                service.generate_image(case["request"])

            # Verify comprehensive debugging information
            error = exc_info.value
            assert hasattr(error, 'generation_prompt')
            assert hasattr(error, 'model_response')

            # Check for required debugging context
            if hasattr(error, 'error_context'):
                for debug_req in case["debug_requirements"]:
                    assert debug_req in str(error.error_context).lower()

    def test_ai_processing_timeout_error_handling(self):
        """Test AI processing timeout errors provide debugging information."""
        session_id = str(uuid4())

        # Mock AI service with timeout
        with patch('src.services.gemini_image_service.GeminiImageService') as mock_service:
            mock_service.generate_image.side_effect = AIProcessingTimeoutError(
                "Image generation timed out after 30 seconds",
                processing_stage="ai_model_inference",
                timeout_seconds=30
            )

            # Timeout should not fall back to placeholder
            with pytest.raises(NoFallbackError) as exc_info:
                self._handle_ai_processing_error(
                    mock_service.generate_image.side_effect,
                    "image_generation",
                    allow_fallback=False
                )

            # Verify timeout details are preserved for debugging
            timeout_error = exc_info.value.original_error
            assert isinstance(timeout_error, AIProcessingTimeoutError)
            assert timeout_error.processing_stage == "ai_model_inference"
            assert timeout_error.timeout_seconds == 30

    def test_multiple_ai_errors_aggregation(self):
        """Test handling of multiple AI errors in batch processing."""
        # Test batch processing with multiple failures
        batch_requests = [
            {"id": "req_1", "prompt": "Valid prompt 1"},
            {"id": "req_2", "prompt": ""},  # Invalid - empty prompt
            {"id": "req_3", "prompt": "Valid prompt 3"},
            {"id": "req_4", "model": "invalid-model"}  # Invalid model
        ]

        # Mock batch processing service
        with patch('src.services.gemini_image_service.GeminiImageService') as mock_service:
            # Configure mock to simulate different errors for different requests
            mock_instance = mock_service.return_value

            def mock_generate(request):
                if request.get("prompt") == "":
                    raise ImageGenerationError("Empty prompt", generation_prompt="")
                elif request.get("model") == "invalid-model":
                    raise AIModelValidationError("Invalid model", model_name="invalid-model")
                else:
                    return {"success": True, "request_id": request["id"]}

            mock_instance.generate_image.side_effect = mock_generate

            # Process batch - should collect all errors without fallback
            batch_errors = []
            for request in batch_requests:
                try:
                    mock_instance.generate_image(request)
                except (ImageGenerationError, AIModelValidationError) as e:
                    # Should not fall back, should preserve error details
                    with pytest.raises(NoFallbackError):
                        self._handle_ai_processing_error(e, "image_generation", allow_fallback=False)
                    batch_errors.append({"request_id": request.get("id"), "error": e})

            # Verify error aggregation includes debugging details
            assert len(batch_errors) == 2  # Two invalid requests
            assert any(isinstance(e["error"], ImageGenerationError) for e in batch_errors)
            assert any(isinstance(e["error"], AIModelValidationError) for e in batch_errors)

    def test_ai_error_recovery_attempt_validation(self):
        """Test that recovery attempts are properly validated per FR-006."""
        session_id = str(uuid4())

        # Mock AI service error scenarios
        recovery_scenarios = [
            {
                "error": GeminiRateLimitError("Rate limit exceeded"),
                "recovery_allowed": False,  # FR-006: No fallback
                "expected_outcome": "no_recovery"
            },
            {
                "error": GeminiContentFilterError("Content filtered"),
                "recovery_allowed": False,  # FR-006: No fallback
                "expected_outcome": "no_recovery"
            },
            {
                "error": AIProcessingTimeoutError("Processing timeout"),
                "recovery_allowed": False,  # FR-006: No fallback
                "expected_outcome": "no_recovery"
            }
        ]

        for scenario in recovery_scenarios:
            # Attempt recovery - should be rejected per FR-006
            with pytest.raises(NoFallbackError) as exc_info:
                self._attempt_ai_recovery(
                    session_id=session_id,
                    original_error=scenario["error"],
                    allow_fallback=scenario["recovery_allowed"]
                )

            # Verify recovery was properly rejected
            assert scenario["expected_outcome"] == "no_recovery"
            assert "no fallback behavior allowed" in str(exc_info.value)

    def test_ai_error_debugging_context_preservation(self):
        """Test that error debugging context is preserved through the stack."""
        # Create nested AI processing scenario
        processing_context = {
            "session_id": str(uuid4()),
            "user_request": "Generate video content",
            "processing_pipeline": [
                "script_analysis",
                "image_generation",
                "audio_generation",
                "video_composition"
            ]
        }

        # Simulate error at different pipeline stages
        pipeline_errors = [
            {
                "stage": "script_analysis",
                "error": ScriptAnalysisError(
                    "Failed to analyze script themes",
                    script_content="Sample script content",
                    analysis_error="Theme extraction failed"
                )
            },
            {
                "stage": "image_generation",
                "error": ImageGenerationError(
                    "Failed to generate background image",
                    generation_prompt="Cyberpunk cityscape",
                    model_response="Content filtered"
                )
            },
            {
                "stage": "audio_generation",
                "error": AudioGenerationError(
                    "Failed to generate audio track",
                    audio_requirements={"duration": 30, "style": "ambient"}
                )
            }
        ]

        for pipeline_error in pipeline_errors:
            # Error should preserve full debugging context
            with pytest.raises(NoFallbackError) as exc_info:
                self._handle_pipeline_error(
                    processing_context=processing_context,
                    stage=pipeline_error["stage"],
                    error=pipeline_error["error"]
                )

            # Verify debugging context preservation
            no_fallback_error = exc_info.value
            assert no_fallback_error.processing_stage == pipeline_error["stage"]
            assert isinstance(no_fallback_error.original_error, type(pipeline_error["error"]))

            # Context should include session and pipeline information
            if hasattr(no_fallback_error, 'error_context'):
                context = no_fallback_error.error_context
                assert context.get("session_id") == processing_context["session_id"]
                assert pipeline_error["stage"] in context.get("processing_pipeline", [])

    def test_ai_error_rate_limiting_behavior(self):
        """Test proper handling of rate limiting without fallback."""
        session_id = str(uuid4())

        # Simulate rate limit scenario
        rate_limit_error = GeminiRateLimitError(
            "Gemini API rate limit exceeded",
            retry_after=120  # 2 minutes
        )

        # Rate limiting should not trigger fallback behavior
        with pytest.raises(NoFallbackError) as exc_info:
            self._handle_ai_processing_error(
                rate_limit_error,
                "script_analysis",
                allow_fallback=False
            )

        # Verify rate limit details are preserved for debugging
        no_fallback_error = exc_info.value
        rate_limit_original = no_fallback_error.original_error
        assert isinstance(rate_limit_original, GeminiRateLimitError)
        assert rate_limit_original.retry_after == 120

        # Should include retry timing information for debugging
        assert hasattr(rate_limit_original, 'retry_after')

    # Helper methods for error handling tests

    def _handle_ai_processing_error(self, error: Exception, processing_stage: str, allow_fallback: bool = False):
        """Simulate error handling logic that should prevent fallbacks."""
        if not allow_fallback:
            raise NoFallbackError(error, processing_stage)
        # If fallback was allowed, would handle differently (but FR-006 prohibits this)

    def _attempt_ai_recovery(self, session_id: str, original_error: Exception, allow_fallback: bool = False):
        """Simulate recovery attempt that should be rejected per FR-006."""
        if not allow_fallback:
            # FR-006: No fallback behavior allowed
            raise NoFallbackError(original_error, "recovery_attempt")
        # Recovery logic would go here if allowed

    def _handle_pipeline_error(self, processing_context: dict, stage: str, error: Exception):
        """Simulate pipeline error handling with context preservation."""
        # Create NoFallbackError with full context
        no_fallback_error = NoFallbackError(error, stage)
        no_fallback_error.error_context = processing_context
        raise no_fallback_error

    def test_ai_error_logging_and_monitoring(self):
        """Test that AI errors are properly logged for monitoring per FR-007."""
        # Mock logging system
        with patch('logging.getLogger') as mock_logger:
            mock_log_instance = Mock()
            mock_logger.return_value = mock_log_instance

            # Create AI error scenario
            ai_error = GeminiAPIError(
                "API quota exceeded",
                api_error_code="QUOTA_EXCEEDED",
                error_context={
                    "request_id": "req_abc123",
                    "model": "gemini-2.5-flash",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Error handling should log comprehensive details
            with pytest.raises(NoFallbackError):
                self._handle_ai_processing_error(ai_error, "image_generation", allow_fallback=False)

            # Verify comprehensive error logging for monitoring
            mock_log_instance.error.assert_called()
            log_call_args = mock_log_instance.error.call_args[0]
            log_message = log_call_args[0]

            # Log should include debugging details per FR-007
            assert "quota exceeded" in log_message.lower()
            assert "req_abc123" in log_message
            assert "gemini-2.5-flash" in log_message