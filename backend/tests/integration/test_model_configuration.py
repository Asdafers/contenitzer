"""
Integration test for model configuration verification
Task: T007 [P] - Integration test model configuration verification
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestModelConfiguration:
    """Integration tests for model configuration verification"""

    def test_environment_variable_loaded(self):
        """Test GEMINI_IMAGE_MODEL environment variable is properly loaded"""
        with patch.dict(os.environ, {"GEMINI_IMAGE_MODEL": "gemini-2.5-flash-image"}):
            # This will fail until GeminiService is updated to use env vars
            from backend.src.services.gemini_service import GeminiService

            # Should read from environment variable
            service = GeminiService(api_key="test-key")
            assert hasattr(service, 'image_model')
            assert service.image_model == "gemini-2.5-flash-image"

    def test_default_model_configuration(self):
        """Test default model is gemini-2.5-flash-image"""
        # This will fail until implementation exists
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")
        # Should default to gemini-2.5-flash-image
        assert service.image_model == "gemini-2.5-flash-image"

    def test_configuration_profile_validation(self):
        """Test ConfigurationProfile validates Gemini model"""
        from backend.src.models.configuration_profile import ConfigurationProfile

        # Valid configuration should pass
        config = ConfigurationProfile(
            redis_url="redis://localhost:6379/0",
            youtube_api_key="AIzaSyExample123456789",
            gemini_api_key="AIzaSyGeminiExample123456789",
            gemini_image_model="gemini-2.5-flash-image"
        )
        assert config.gemini_image_model == "gemini-2.5-flash-image"

        # Invalid model should raise error
        with pytest.raises(ValueError):
            ConfigurationProfile(
                redis_url="redis://localhost:6379/0",
                youtube_api_key="AIzaSyExample123456789",
                gemini_api_key="AIzaSyGeminiExample123456789",
                gemini_image_model="invalid-model"
            )

    def test_fallback_model_configuration(self):
        """Test configuration can be changed to fallback model"""
        with patch.dict(os.environ, {"GEMINI_IMAGE_MODEL": "gemini-pro"}):
            from backend.src.services.gemini_service import GeminiService

            service = GeminiService(api_key="test-key")
            assert service.image_model == "gemini-pro"

    def test_model_availability_checking(self):
        """Test model availability checking works"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        # Should have method to check model availability
        assert hasattr(service, 'check_model_availability')

        # Should be able to check primary model
        availability = service.check_model_availability("gemini-2.5-flash-image")
        assert isinstance(availability, bool)

    def test_invalid_model_name_rejected(self):
        """Test invalid model names are rejected with proper error messages"""
        from backend.src.services.gemini_service import GeminiService

        with pytest.raises(ValueError) as exc_info:
            service = GeminiService(api_key="test-key")
            service.set_image_model("openai-gpt-4")  # Invalid model

        assert "gemini" in str(exc_info.value).lower()

    def test_configuration_change_runtime(self):
        """Test model configuration can be changed at runtime"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        # Should be able to change model at runtime
        service.set_image_model("gemini-pro")
        assert service.image_model == "gemini-pro"

        service.set_image_model("gemini-2.5-flash-image")
        assert service.image_model == "gemini-2.5-flash-image"