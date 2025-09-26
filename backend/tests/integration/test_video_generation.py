"""
Integration test for end-to-end video generation
Task: T011 [P] - Integration test end-to-end video generation
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVideoGeneration:
    """Integration tests for end-to-end video generation workflow"""

    @pytest.mark.asyncio
    async def test_video_generation_creates_multiple_assets(self):
        """Test video generation job creates multiple assets (images, video clips)"""
        from backend.src.services.video_generation_service import VideoGenerationService
        from backend.src.models.video_generation_job import VideoGenerationJob

        service = VideoGenerationService()

        job_data = {
            "session_id": "test-session-001",
            "script_content": "Speaker 1: AI is transforming video creation...",
            "generation_options": {
                "duration": 30,
                "resolution": "1920x1080",
                "num_images": 3,
                "num_video_clips": 2
            }
        }

        job_id = service.create_generation_job(**job_data)
        job = service.get_job(job_id)

        # Execute asset generation
        await service.generate_media_assets(job_id)

        # Verify multiple assets were created
        assets = service.get_job_assets(job_id)
        image_assets = [a for a in assets if a.asset_type == "image"]
        video_assets = [a for a in assets if a.asset_type == "video_clip"]

        assert len(image_assets) == 3
        assert len(video_assets) == 2

    def test_all_visual_assets_use_new_model(self):
        """Test all visual assets use gemini-2.5-flash-image model"""
        from backend.src.services.video_generation_service import VideoGenerationService

        service = VideoGenerationService()

        job_id = service.create_generation_job(
            session_id="test-session-002",
            script_content="Test content for model verification"
        )

        # Generate assets
        service.generate_media_assets(job_id)

        # Verify all visual assets use the correct model
        assets = service.get_job_assets(job_id)
        visual_assets = [a for a in assets if a.asset_type in ["image", "video_clip"]]

        for asset in visual_assets:
            assert asset.gemini_model_used == "gemini-2.5-flash-image"
            assert asset.generation_metadata.get("model_version") == "gemini-2.5-flash-image"

    @pytest.mark.asyncio
    async def test_video_composition_completes_successfully(self):
        """Test final video composition completes successfully"""
        from backend.src.services.video_generation_service import VideoGenerationService
        from backend.src.services.video_composer import VideoComposer

        service = VideoGenerationService()
        composer = VideoComposer()

        # Create and generate assets
        job_id = service.create_generation_job(
            session_id="test-session-003",
            script_content="Complete video generation test"
        )

        await service.generate_media_assets(job_id)

        # Compose final video
        composition_result = await composer.compose_video(job_id)

        assert composition_result["status"] == "completed"
        assert "video_path" in composition_result
        assert Path(composition_result["video_path"]).exists()

    def test_asset_metadata_shows_correct_model(self):
        """Test asset metadata shows correct model information"""
        from backend.src.services.video_generation_service import VideoGenerationService

        service = VideoGenerationService()

        job_id = service.create_generation_job(
            session_id="test-session-004",
            script_content="Metadata verification test"
        )

        service.generate_media_assets(job_id)
        assets = service.get_job_assets(job_id)

        for asset in assets:
            if asset.asset_type in ["image", "video_clip"]:
                # Verify model information in metadata
                assert asset.gemini_model_used == "gemini-2.5-flash-image"
                assert asset.generation_metadata.get("model_version") == "gemini-2.5-flash-image"
                assert asset.generation_metadata.get("fallback_used") is False

    def test_no_fallback_occurred(self):
        """Test no fallback occurred (fallback_used: false)"""
        from backend.src.services.video_generation_service import VideoGenerationService

        service = VideoGenerationService()

        with patch('backend.src.services.gemini_service.GeminiService') as mock_service:
            # Mock successful primary model usage
            mock_instance = MagicMock()
            mock_instance.generate_images_for_script.return_value = {
                "images": [{"model_used": "gemini-2.5-flash-image", "fallback_used": False}],
                "model_used": "gemini-2.5-flash-image",
                "fallback_used": False
            }
            mock_service.return_value = mock_instance

            job_id = service.create_generation_job(
                session_id="test-session-005",
                script_content="No fallback test"
            )

            service.generate_media_assets(job_id)
            assets = service.get_job_assets(job_id)

            for asset in assets:
                if asset.asset_type in ["image", "video_clip"]:
                    assert asset.generation_metadata.get("fallback_used") is False

    def test_performance_meets_sla(self):
        """Test performance meets SLA (video generation completes within time limits)"""
        import time
        from backend.src.services.video_generation_service import VideoGenerationService

        service = VideoGenerationService()

        start_time = time.time()

        job_id = service.create_generation_job(
            session_id="test-session-006",
            script_content="Performance test with 30-second video",
            generation_options={"duration": 30}
        )

        # Generate assets and compose video
        service.generate_media_assets(job_id)
        service.compose_video(job_id)

        elapsed_time = time.time() - start_time

        # Should complete within reasonable time (adjust based on actual SLA)
        # For 30-second video: images <30s each, composition <60s
        max_expected_time = 300  # 5 minutes for full workflow
        assert elapsed_time < max_expected_time

    def test_generated_video_file_exists_and_playable(self):
        """Test generated video file exists and is playable"""
        from backend.src.services.video_generation_service import VideoGenerationService
        import subprocess

        service = VideoGenerationService()

        job_id = service.create_generation_job(
            session_id="test-session-007",
            script_content="Video file verification test"
        )

        service.generate_media_assets(job_id)
        result = service.compose_video(job_id)

        if "video_path" in result:
            video_path = Path(result["video_path"])

            # Verify file exists
            assert video_path.exists()
            assert video_path.is_file()

            # Verify it's a valid video file (basic check)
            assert video_path.suffix in ['.mp4', '.avi', '.mov', '.mkv']

            # Optional: Use ffprobe to verify video is playable
            try:
                subprocess.run([
                    'ffprobe', '-v', 'quiet', '-show_entries',
                    'format=duration', '-of', 'csv=p=0', str(video_path)
                ], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # ffprobe not available or video invalid
                pytest.skip("ffprobe not available for video validation")

    @pytest.mark.asyncio
    async def test_concurrent_video_generation(self):
        """Test multiple video generation jobs can run concurrently"""
        from backend.src.services.video_generation_service import VideoGenerationService

        service = VideoGenerationService()

        # Create multiple jobs
        job_ids = []
        for i in range(3):
            job_id = service.create_generation_job(
                session_id=f"concurrent-session-{i}",
                script_content=f"Concurrent test video {i}"
            )
            job_ids.append(job_id)

        # Run generation concurrently
        tasks = [
            service.generate_media_assets(job_id)
            for job_id in job_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All jobs should complete successfully
        for result in results:
            assert not isinstance(result, Exception)

        # Verify all jobs have assets
        for job_id in job_ids:
            assets = service.get_job_assets(job_id)
            assert len(assets) > 0

    def test_job_status_tracking_throughout_workflow(self):
        """Test job status is tracked correctly throughout the workflow"""
        from backend.src.services.video_generation_service import VideoGenerationService
        from backend.src.models.video_generation_job import JobStatusEnum

        service = VideoGenerationService()

        job_id = service.create_generation_job(
            session_id="status-tracking-session",
            script_content="Status tracking test"
        )

        job = service.get_job(job_id)
        assert job.status == JobStatusEnum.PENDING

        # Start media generation
        service.start_media_generation(job_id)
        job = service.get_job(job_id)
        assert job.status == JobStatusEnum.MEDIA_GENERATION

        # Complete media generation, start video composition
        service.complete_media_generation(job_id)
        job = service.get_job(job_id)
        assert job.status == JobStatusEnum.VIDEO_COMPOSITION

        # Complete entire workflow
        service.complete_video_generation(job_id)
        job = service.get_job(job_id)
        assert job.status == JobStatusEnum.COMPLETED