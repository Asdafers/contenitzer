"""
Integration test for fallback mechanism
Task: T009 [P] - Integration test fallback mechanism
"""

import pytest
from unittest.mock import patch, MagicMock, side_effect


class TestModelFallback:
    """Integration tests for model fallback mechanism"""

    @pytest.mark.asyncio
    async def test_fallback_when_primary_model_fails(self):
        """Test system falls back to gemini-pro when primary model fails"""
        from backend.src.services.gemini_service import GeminiService

        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            # Primary model fails, fallback succeeds
            mock_primary = MagicMock()
            mock_primary.generate_content.side_effect = Exception("Model unavailable")

            mock_fallback = MagicMock()
            mock_fallback.generate_content.return_value = MagicMock(text="Generated content")

            def model_side_effect(model_name):
                if model_name == "gemini-2.5-flash-image":
                    return mock_primary
                elif model_name == "gemini-pro":
                    return mock_fallback

            mock_model_class.side_effect = model_side_effect

            service = GeminiService(api_key="test-key")
            result = await service.generate_images_for_script("Test content")

            assert result["model_used"] == "gemini-pro"
            assert result["fallback_used"] is True

    def test_model_fallback_used_flag_set(self):
        """Test model_fallback_used flag is set to true in asset metadata"""
        from backend.src.models.media_asset import MediaAsset

        # Create asset that used fallback
        asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/fallback_001.jpg",
            gemini_model_used="gemini-pro",  # Used fallback model
            generation_metadata={
                "model_version": "gemini-pro",
                "fallback_used": True,
                "primary_model_attempted": "gemini-2.5-flash-image"
            }
        )

        assert asset.gemini_model_used == "gemini-pro"
        assert asset.generation_metadata.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_generation_completes_with_fallback(self):
        """Test generation still completes successfully with fallback model"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        with patch.object(service, 'check_model_availability') as mock_check:
            # Primary unavailable, fallback available
            mock_check.side_effect = lambda model: model == "gemini-pro"

            result = await service.generate_images_for_script(
                "Test script content", num_images=1
            )

            assert len(result["images"]) == 1
            assert result["model_used"] == "gemini-pro"
            assert result["fallback_used"] is True

    def test_error_when_both_models_unavailable(self):
        """Test error handling when both models are unavailable"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        with patch.object(service, 'check_model_availability', return_value=False):
            with pytest.raises(Exception) as exc_info:
                asyncio.run(service.generate_images_for_script("Test content"))

            assert "unavailable" in str(exc_info.value).lower()

    def test_fallback_logging(self):
        """Test proper logging of fallback events"""
        import logging
        from backend.src.services.gemini_service import GeminiService

        with patch('backend.src.services.gemini_service.logger') as mock_logger:
            service = GeminiService(api_key="test-key")

            # Simulate fallback scenario
            service._log_fallback_event("gemini-2.5-flash-image", "gemini-pro")

            # Should log the fallback event
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "fallback" in call_args.lower()
            assert "gemini-2.5-flash-image" in call_args
            assert "gemini-pro" in call_args

    def test_fallback_disabled_when_allow_fallback_false(self):
        """Test configuration allows disabling fallback (allow_fallback=false)"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        with patch.object(service, 'check_model_availability') as mock_check:
            # Primary unavailable
            mock_check.side_effect = lambda model: model != "gemini-2.5-flash-image"

            with pytest.raises(Exception) as exc_info:
                asyncio.run(service.generate_images_for_script(
                    "Test content", allow_fallback=False
                ))

            assert "unavailable" in str(exc_info.value).lower()

    def test_fallback_metrics_tracked(self):
        """Test fallback events are tracked in metrics"""
        from backend.src.services.model_health_service import ModelHealthService

        health_service = ModelHealthService()

        # Record fallback event
        health_service.record_fallback_event(
            primary_model="gemini-2.5-flash-image",
            fallback_model="gemini-pro",
            reason="rate_limit_exceeded"
        )

        # Should track fallback in metrics
        metrics = health_service.get_model_metrics("gemini-2.5-flash-image")
        assert metrics["fallback_count"] > 0
        assert "rate_limit_exceeded" in metrics["fallback_reasons"]

    @pytest.mark.asyncio
    async def test_retry_logic_before_fallback(self):
        """Test retry logic attempts multiple times before falling back"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            # Fail 3 times, then use fallback
            mock_model.generate_content.side_effect = [
                Exception("Temporary error"),
                Exception("Temporary error"),
                Exception("Temporary error"),
            ]
            mock_model_class.return_value = mock_model

            # Should retry 3 times before fallback
            result = await service.generate_content_with_retry_and_fallback("Test")

            assert mock_model.generate_content.call_count == 3
            assert result["fallback_used"] is True