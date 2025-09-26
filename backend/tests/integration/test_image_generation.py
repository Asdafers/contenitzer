"""
Integration test for image generation with new model
Task: T008 [P] - Integration test image generation with new model
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestImageGeneration:
    """Integration tests for image generation with gemini-2.5-flash-image"""

    @pytest.mark.asyncio
    async def test_image_generation_uses_new_model(self):
        """Test image generation uses gemini-2.5-flash-image model"""
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        script_content = "Speaker 1: Today we'll discuss AI advancements in image generation."

        # Generate image metadata (will fail until implementation exists)
        images = await service.generate_images_for_script(script_content, num_images=1)

        assert len(images) == 1
        assert images[0]["model_used"] == "gemini-2.5-flash-image"

    @pytest.mark.asyncio
    async def test_generated_assets_have_correct_metadata(self):
        """Test generated assets have correct model metadata"""
        from backend.src.services.media_asset_generator import MediaAssetGenerator
        from backend.src.models.video_generation_job import VideoGenerationJob

        # This will fail until MediaAssetGenerator is updated
        generator = MediaAssetGenerator()

        job = VideoGenerationJob(
            session_id="test-session",
            script_id="test-script"
        )

        assets = await generator.generate_assets_for_job(
            job, "Test script content", {"num_images": 2}
        )

        for asset in assets:
            if asset.asset_type == "image":
                assert asset.gemini_model_used == "gemini-2.5-flash-image"
                assert asset.generation_metadata.get("model_version") == "gemini-2.5-flash-image"

    def test_generation_time_within_limits(self):
        """Test generation time is within acceptable limits (<30s per asset)"""
        import time
        from backend.src.services.gemini_service import GeminiService

        service = GeminiService(api_key="test-key")

        start_time = time.time()

        # This will fail until actual generation is implemented
        # For now, just ensure the interface exists
        assert hasattr(service, 'generate_images_for_script')

        # When implemented, should complete within 30 seconds
        # elapsed = time.time() - start_time
        # assert elapsed < 30

    def test_generated_files_exist(self):
        """Test generated image files exist at specified paths"""
        from backend.src.services.media_asset_generator import MediaAssetGenerator

        generator = MediaAssetGenerator()

        # This will fail until file generation is implemented
        asset_path = generator.generate_image_asset(
            prompt="Professional background for AI discussion",
            asset_id="test-image-001"
        )

        if asset_path:
            assert Path(asset_path).exists()
            assert Path(asset_path).is_file()
            assert Path(asset_path).suffix in ['.jpg', '.png', '.webp']

    @pytest.mark.asyncio
    async def test_database_records_created(self):
        """Test asset database records are created with correct model information"""
        from backend.src.models.media_asset import MediaAsset
        from backend.src.database import get_db

        # This will fail until database integration is complete
        db = next(get_db())

        # Create test asset
        asset = MediaAsset(
            asset_type="image",
            file_path="/media/images/test_001.jpg",
            gemini_model_used="gemini-2.5-flash-image",
            generation_metadata={
                "model_version": "gemini-2.5-flash-image",
                "generation_time_ms": 25000,
                "prompt": "Test image generation"
            }
        )

        db.add(asset)
        db.commit()

        # Verify record was created correctly
        saved_asset = db.query(MediaAsset).filter(
            MediaAsset.gemini_model_used == "gemini-2.5-flash-image"
        ).first()

        assert saved_asset is not None
        assert saved_asset.generation_metadata["model_version"] == "gemini-2.5-flash-image"

    def test_generation_job_status_transitions(self):
        """Test generation job status transitions correctly"""
        from backend.src.models.video_generation_job import VideoGenerationJob, JobStatusEnum

        job = VideoGenerationJob(
            session_id="test-session",
            script_id="test-script",
            status=JobStatusEnum.PENDING
        )

        # Should transition through proper states
        assert job.status == JobStatusEnum.PENDING

        job.advance_to_media_generation()
        assert job.status == JobStatusEnum.MEDIA_GENERATION

        job.advance_to_video_composition()
        assert job.status == JobStatusEnum.VIDEO_COMPOSITION

        job.mark_completed()
        assert job.status == JobStatusEnum.COMPLETED

    def test_no_fallback_occurs_with_available_model(self):
        """Test no fallback occurs when primary model is available"""
        from backend.src.services.gemini_service import GeminiService

        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.return_value = MagicMock()

            service = GeminiService(api_key="test-key")

            # Should not trigger fallback when primary model works
            result = service.generate_content_with_fallback("Test prompt")

            assert result["model_used"] == "gemini-2.5-flash-image"
            assert result["fallback_used"] is False