"""
Integration tests for Gemini image generation.
Tests the complete workflow from prompt to AI-generated image descriptions.
"""
import pytest
from unittest.mock import Mock, patch
import json
from uuid import uuid4

from src.services.gemini_image_service import GeminiImageService
from src.lib.exceptions import (
    ImageGenerationError,
    GeminiAPIError,
    GeminiRateLimitError,
    GeminiContentFilterError,
    NoFallbackError,
    AIProcessingTimeoutError
)


class TestGeminiImageGenerationIntegration:
    """Integration tests for AI-powered image generation workflow."""

    def test_complete_image_generation_workflow(self, mock_gemini_client):
        """Test complete workflow from prompt to AI-generated image description."""
        # This test will fail until GeminiImageService is implemented
        service = GeminiImageService()

        generation_request = {
            "prompt": "Cyberpunk cityscape with neon lights reflecting off glass towers",
            "style": "digital art",
            "quality": "high",
            "aspect_ratio": "16:9"
        }

        # Should generate image using Gemini and return structured data
        result = service.generate_image(generation_request)

        # Verify AI-powered generation results
        assert "image_description" in result
        assert "generation_prompt" in result
        assert "ai_model_used" in result
        assert "generation_metadata" in result
        assert result["ai_model_used"] == "gemini-2.5-flash"

        # Verify realistic processing time per FR-004
        assert "processing_time" in result
        assert result["processing_time"] >= 1.0  # Real AI takes time

    def test_image_generation_with_model_selection(self, mock_gemini_client):
        """Test image generation respects AI model parameter per FR-005."""
        service = GeminiImageService()

        generation_request = {
            "prompt": "Modern tech workspace with holographic displays",
            "model": "gemini-2.5-flash",
            "style_parameters": {
                "temperature": 0.8,
                "creativity": "high"
            }
        }

        result = service.generate_image(generation_request)

        # Verify specified model was used
        assert result["ai_model_used"] == "gemini-2.5-flash"
        assert result["generation_metadata"]["model"] == "gemini-2.5-flash"
        assert result["generation_metadata"]["temperature"] == 0.8

    def test_image_generation_contextual_relevance(self, mock_gemini_client):
        """Test AI generates contextually relevant images per FR-009."""
        service = GeminiImageService()

        generation_request = {
            "prompt": "Professional workspace for content creation",
            "context": {
                "script_theme": "technological future",
                "target_audience": "tech professionals",
                "brand_style": "modern minimalist"
            },
            "relevance_requirements": [
                "technology focused",
                "professional setting",
                "modern aesthetic"
            ]
        }

        result = service.generate_image(generation_request)

        # Verify context influences generation
        image_description = result["image_description"].lower()
        assert any(keyword in image_description for keyword in
                  ["technology", "professional", "modern", "workspace"])

        # Context should be reflected in metadata
        assert "context_analysis" in result["generation_metadata"]
        assert result["generation_metadata"]["context_analysis"]["theme"] == "technological future"

    def test_image_generation_realistic_processing_time(self, mock_gemini_client):
        """Test realistic processing time per FR-004."""
        service = GeminiImageService()

        generation_request = {
            "prompt": "Complex futuristic cityscape with detailed architecture",
            "quality": "high",
            "complexity": "detailed"
        }

        import time
        start_time = time.time()
        result = service.generate_image(generation_request)
        actual_time = time.time() - start_time

        # Should take realistic AI processing time (not subseconds)
        assert actual_time >= 1.0  # At least 1 second for real AI
        assert result["processing_time"] >= 1.0

        # Complex requests should take longer
        assert result["processing_time"] >= 2.0  # More complex = more time

    def test_image_generation_progress_tracking(self, mock_gemini_client):
        """Test detailed progress tracking per FR-007."""
        service = GeminiImageService()

        generation_request = {
            "prompt": "Vibrant digital art landscape",
            "session_id": str(uuid4()),
            "track_progress": True
        }

        # Capture progress events
        progress_events = []
        def progress_callback(event):
            progress_events.append(event)

        result = service.generate_image(generation_request, progress_callback=progress_callback)

        # Verify detailed progress tracking
        assert len(progress_events) >= 3  # Multiple stages

        expected_stages = ["initializing_generation", "processing_prompt", "generating_image"]
        captured_stages = [event["stage"] for event in progress_events]

        for stage in expected_stages:
            assert stage in captured_stages

        # Each event should have debugging details per FR-007
        for event in progress_events:
            assert "stage" in event
            assert "timestamp" in event
            assert "details" in event
            assert "processing_info" in event["details"]

    def test_image_generation_no_fallback_on_error(self, mock_gemini_error_response):
        """Test no fallback behavior on AI errors per FR-006."""
        service = GeminiImageService()

        # Mock Gemini API rate limit error
        with patch.object(service, '_call_gemini_api') as mock_call:
            mock_call.side_effect = GeminiRateLimitError("Rate limit exceeded", retry_after=60)

            generation_request = {
                "prompt": "Test image generation",
                "allow_fallback": False  # Explicitly no fallback
            }

            # Should raise NoFallbackError, not fall back to placeholder
            with pytest.raises(NoFallbackError) as exc_info:
                service.generate_image(generation_request)

            assert "no fallback behavior allowed" in str(exc_info.value)
            assert exc_info.value.processing_stage == "image_generation"
            assert isinstance(exc_info.value.original_error, GeminiRateLimitError)

    def test_image_generation_content_filter_handling(self, mock_gemini_client):
        """Test handling of Gemini content filter responses."""
        service = GeminiImageService()

        # Mock content filter error
        with patch.object(service, '_call_gemini_api') as mock_call:
            mock_call.side_effect = GeminiContentFilterError(
                "Content filtered by safety policy",
                filtered_content="inappropriate image prompt"
            )

            generation_request = {
                "prompt": "Potentially problematic image content",
                "model": "gemini-2.5-flash"
            }

            # Should raise NoFallbackError (no fallback behavior)
            with pytest.raises(NoFallbackError) as exc_info:
                service.generate_image(generation_request)

            # Verify original error is preserved for debugging
            original_error = exc_info.value.original_error
            assert isinstance(original_error, GeminiContentFilterError)
            assert original_error.filtered_content == "inappropriate image prompt"

    def test_image_generation_detailed_error_reporting(self, mock_gemini_client):
        """Test detailed error reporting for debugging per FR-007."""
        service = GeminiImageService()

        # Test with invalid generation parameters
        generation_request = {
            "prompt": "",  # Empty prompt should trigger validation error
            "quality": "invalid_quality",
            "model": "gemini-2.5-flash"
        }

        with pytest.raises(ImageGenerationError) as exc_info:
            service.generate_image(generation_request)

        # Error should include debugging details
        error = exc_info.value
        assert hasattr(error, 'generation_prompt')
        assert hasattr(error, 'model_response')
        assert error.generation_prompt == ""
        assert "validation" in str(error).lower()

    def test_image_generation_timeout_handling(self, mock_gemini_client):
        """Test timeout handling in AI image generation."""
        service = GeminiImageService()

        # Mock timeout scenario
        with patch.object(service, '_call_gemini_api') as mock_call:
            mock_call.side_effect = AIProcessingTimeoutError(
                "Image generation timed out",
                processing_stage="image_generation",
                timeout_seconds=45
            )

            generation_request = {
                "prompt": "Very complex image that would timeout",
                "timeout": 45,
                "quality": "ultra_high"
            }

            # Should raise NoFallbackError (no fallback for timeouts)
            with pytest.raises(NoFallbackError) as exc_info:
                service.generate_image(generation_request)

            # Verify timeout information is preserved
            timeout_error = exc_info.value.original_error
            assert isinstance(timeout_error, AIProcessingTimeoutError)
            assert timeout_error.timeout_seconds == 45

    def test_image_generation_validates_parameters(self, mock_gemini_client):
        """Test validation of generation parameters."""
        service = GeminiImageService()

        # Test invalid quality parameter
        generation_request = {
            "prompt": "Test image",
            "quality": "invalid_quality",
            "model": "gemini-2.5-flash"
        }

        with pytest.raises(ImageGenerationError) as exc_info:
            service.generate_image(generation_request)

        assert "quality" in str(exc_info.value).lower()

        # Test invalid aspect ratio
        generation_request = {
            "prompt": "Test image",
            "aspect_ratio": "invalid_ratio",
            "model": "gemini-2.5-flash"
        }

        with pytest.raises(ImageGenerationError):
            service.generate_image(generation_request)

    def test_image_generation_batch_processing(self, mock_gemini_client):
        """Test batch processing of multiple image generation requests."""
        service = GeminiImageService()

        batch_requests = [
            {
                "prompt": "Modern office workspace",
                "style": "photography",
                "id": "img_1"
            },
            {
                "prompt": "Futuristic technology lab",
                "style": "digital art",
                "id": "img_2"
            },
            {
                "prompt": "Creative collaboration space",
                "style": "illustration",
                "id": "img_3"
            }
        ]

        # Should process batch efficiently
        results = service.generate_image_batch(batch_requests)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["request_id"] == batch_requests[i]["id"]
            assert "image_description" in result
            assert "processing_time" in result
            assert result["processing_time"] >= 1.0  # Realistic time per image

    def test_image_generation_quality_settings(self, mock_gemini_client):
        """Test different quality settings affect generation."""
        service = GeminiImageService()

        qualities = ["low", "medium", "high"]
        results = []

        for quality in qualities:
            generation_request = {
                "prompt": "Professional workspace environment",
                "quality": quality,
                "model": "gemini-2.5-flash"
            }

            result = service.generate_image(generation_request)
            results.append(result)

            # Verify quality setting is respected
            assert result["generation_metadata"]["quality"] == quality

        # Higher quality should generally take longer
        low_time = results[0]["processing_time"]
        high_time = results[2]["processing_time"]
        assert high_time >= low_time  # Higher quality = more processing time