"""
Integration tests for AI script analysis workflow.
Tests the complete workflow from script input to AI-powered scene analysis.
"""
import pytest
from unittest.mock import Mock, patch
import json
from uuid import uuid4

from src.services.script_analysis_service import ScriptAnalysisService
from src.lib.exceptions import (
    ScriptAnalysisError,
    GeminiAPIError,
    NoFallbackError,
    AIProcessingTimeoutError
)


class TestAIScriptAnalysisIntegration:
    """Integration tests for AI-powered script analysis workflow."""

    def test_complete_script_analysis_workflow(self, mock_gemini_client, sample_script_content):
        """Test complete workflow from script to AI-analyzed scenes."""
        # This test will fail until ScriptAnalysisService is implemented
        service = ScriptAnalysisService()

        script_data = {
            "content": sample_script_content,
            "title": "Test Content Creation Script",
            "duration_target": 180
        }

        # Should analyze script using Gemini and return structured scene data
        result = service.analyze_script(script_data)

        # Verify AI-powered analysis results
        assert "scenes" in result
        assert "overall_theme" in result
        assert "estimated_scenes" in result
        assert isinstance(result["scenes"], list)
        assert len(result["scenes"]) > 0

        # Verify each scene has AI-generated content
        for scene in result["scenes"]:
            assert "index" in scene
            assert "text" in scene
            assert "visual_themes" in scene
            assert "image_prompt" in scene
            assert isinstance(scene["visual_themes"], list)

    def test_script_analysis_with_gemini_model_selection(self, mock_gemini_client):
        """Test script analysis respects AI model parameter."""
        service = ScriptAnalysisService()

        script_data = {
            "content": "Brief test script for analysis",
            "model": "gemini-2.5-flash",
            "analysis_depth": "detailed"
        }

        # Should use specified Gemini model
        result = service.analyze_script(script_data)

        # Verify model was used (through mock verification)
        assert result["model_used"] == "gemini-2.5-flash"
        assert "analysis_metadata" in result
        assert result["analysis_metadata"]["model"] == "gemini-2.5-flash"

    def test_script_analysis_generates_contextual_prompts(self, mock_gemini_client, sample_script_content):
        """Test AI generates contextually relevant image prompts per FR-009."""
        service = ScriptAnalysisService()

        script_data = {
            "content": sample_script_content,
            "context_requirements": {
                "brand_style": "modern tech",
                "target_audience": "professionals",
                "visual_style": "clean minimalist"
            }
        }

        result = service.analyze_script(script_data)

        # Verify AI considers context in prompt generation
        for scene in result["scenes"]:
            image_prompt = scene["image_prompt"]
            # AI should incorporate context requirements
            assert len(image_prompt) > 20  # Substantial prompt
            # Context should influence generated prompts
            assert any(keyword in image_prompt.lower() for keyword in
                      ["modern", "tech", "professional", "clean", "minimal"])

    def test_script_analysis_realistic_processing_time(self, mock_gemini_client):
        """Test AI processing takes realistic time per FR-004."""
        service = ScriptAnalysisService()

        script_data = {
            "content": "Test script content for timing analysis",
            "complexity": "high"
        }

        import time
        start_time = time.time()
        result = service.analyze_script(script_data)
        processing_time = time.time() - start_time

        # Should take realistic AI processing time (not subseconds)
        assert processing_time >= 1.0  # At least 1 second for real AI processing
        assert "processing_time" in result
        assert result["processing_time"] >= 1.0

    def test_script_analysis_progress_tracking(self, mock_gemini_client):
        """Test progress tracking during AI analysis per FR-007."""
        service = ScriptAnalysisService()

        script_data = {
            "content": "Test script for progress tracking",
            "session_id": str(uuid4()),
            "track_progress": True
        }

        # Mock progress callback to capture events
        progress_events = []
        def progress_callback(event):
            progress_events.append(event)

        result = service.analyze_script(script_data, progress_callback=progress_callback)

        # Verify detailed progress tracking
        assert len(progress_events) >= 3  # Multiple stages tracked

        expected_stages = ["analyzing_content", "extracting_themes", "generating_prompts"]
        captured_stages = [event["stage"] for event in progress_events]

        for stage in expected_stages:
            assert stage in captured_stages

        # Each event should have debugging details
        for event in progress_events:
            assert "stage" in event
            assert "timestamp" in event
            assert "details" in event

    def test_script_analysis_error_without_fallback(self, mock_gemini_error_response):
        """Test no fallback behavior on AI errors per FR-006."""
        service = ScriptAnalysisService()

        # Mock Gemini API error
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.side_effect = GeminiAPIError("API temporarily unavailable")

            script_data = {
                "content": "Test script content",
                "allow_fallback": False  # Explicitly no fallback
            }

            # Should raise NoFallbackError, not fall back to placeholder analysis
            with pytest.raises(NoFallbackError) as exc_info:
                service.analyze_script(script_data)

            assert "no fallback behavior allowed" in str(exc_info.value)
            assert exc_info.value.processing_stage == "script_analysis"
            assert isinstance(exc_info.value.original_error, GeminiAPIError)

    def test_script_analysis_detailed_error_reporting(self, mock_gemini_client):
        """Test detailed error reporting for debugging per FR-007."""
        service = ScriptAnalysisService()

        # Test with invalid script content
        script_data = {
            "content": "",  # Empty content should trigger validation error
            "model": "gemini-2.5-flash"
        }

        with pytest.raises(ScriptAnalysisError) as exc_info:
            service.analyze_script(script_data)

        # Error should include debugging details
        error = exc_info.value
        assert hasattr(error, 'script_content')
        assert hasattr(error, 'analysis_error')
        assert error.script_content == ""
        assert "empty" in error.analysis_error.lower()

    def test_script_analysis_handles_content_filtering(self, mock_gemini_client):
        """Test handling of Gemini content filter responses."""
        service = ScriptAnalysisService()

        # Mock content filter error
        with patch.object(service, '_call_gemini_api') as mock_call:
            from src.lib.exceptions import GeminiContentFilterError
            mock_call.side_effect = GeminiContentFilterError(
                "Content filtered by safety policy",
                filtered_content="problematic content"
            )

            script_data = {
                "content": "Script with potentially problematic content",
                "model": "gemini-2.5-flash"
            }

            # Should raise NoFallbackError (no fallback behavior)
            with pytest.raises(NoFallbackError) as exc_info:
                service.analyze_script(script_data)

            assert isinstance(exc_info.value.original_error, GeminiContentFilterError)

    def test_script_analysis_timeout_handling(self, mock_gemini_client):
        """Test timeout handling in AI processing."""
        service = ScriptAnalysisService()

        # Mock timeout scenario
        with patch.object(service, '_call_gemini_api') as mock_call:
            mock_call.side_effect = AIProcessingTimeoutError(
                "AI processing timed out",
                processing_stage="script_analysis",
                timeout_seconds=30
            )

            script_data = {
                "content": "Long script content that would timeout",
                "timeout": 30
            }

            # Should raise NoFallbackError (no fallback for timeouts)
            with pytest.raises(NoFallbackError):
                service.analyze_script(script_data)

    def test_script_analysis_validates_ai_model_parameter(self, mock_gemini_client):
        """Test validation of AI model parameter per FR-005."""
        service = ScriptAnalysisService()

        script_data = {
            "content": "Test script content",
            "model": "invalid-gemini-model"  # Invalid model name
        }

        # Should validate model before processing
        with pytest.raises(ScriptAnalysisError) as exc_info:
            service.analyze_script(script_data)

        assert "invalid" in str(exc_info.value).lower()
        assert "model" in str(exc_info.value).lower()