"""
Video Generation Service - Main orchestrator for the video generation workflow.
Coordinates media asset generation, video composition, and job management.
"""
import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..models.video_generation_job import VideoGenerationJob, JobStatusEnum as JobStatus
from ..models.generated_video import GeneratedVideo
from ..models.media_asset import MediaAsset
from ..lib.database import get_db_session
from .media_asset_generator import MediaAssetGenerator, MediaAssetGeneratorError
from .video_composer import VideoComposer, VideoComposerError
from .storage_manager import StorageManager, StorageManagerError
from ..lib.error_handlers import handle_ffmpeg_error, execute_ffmpeg_with_fallback

logger = logging.getLogger(__name__)


class VideoGenerationServiceError(Exception):
    """Exception raised by video generation service operations."""
    pass


class VideoGenerationService:
    """Main orchestrator service for video generation workflow."""

    def __init__(self):
        self.asset_generator = MediaAssetGenerator()
        self.video_composer = VideoComposer()
        self.storage_manager = StorageManager()

    def create_generation_job(
        self,
        script_id: uuid.UUID,
        session_id: str,
        options: Dict[str, Any]
    ) -> VideoGenerationJob:
        """Create a new video generation job."""
        try:
            # Clean options to make them JSON serializable
            clean_options = self._sanitize_for_json(options)

            job = VideoGenerationJob(
                id=uuid.uuid4(),
                session_id=session_id,
                script_id=script_id,
                status=JobStatus.PENDING,
                started_at=datetime.now(),
                composition_settings=clean_options
            )

            with get_db_session() as db:
                db.add(job)
                db.commit()
                db.refresh(job)

                # Store job ID before session closes
                job_id = job.id

            logger.info(f"Created video generation job {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to create generation job: {e}")
            raise VideoGenerationServiceError(f"Job creation failed: {e}")

    def execute_generation_workflow(
        self,
        job_id: uuid.UUID,
        script_content: str
    ) -> GeneratedVideo:
        """Execute the complete video generation workflow."""
        try:
            with get_db_session() as db:
                job = db.query(VideoGenerationJob).filter(
                    VideoGenerationJob.id == job_id
                ).first()

                if not job:
                    raise VideoGenerationServiceError(f"Job {job_id} not found")

                # Phase 1: Generate media assets with graceful degradation
                job.update_progress(20, JobStatus.MEDIA_GENERATION)
                db.commit()

                assets = self._generate_assets_with_fallback(
                    job_id, script_content, job.composition_settings or {}
                )

                # Phase 2: Compose final video
                job.update_progress(60, JobStatus.VIDEO_COMPOSITION)
                db.commit()

                video = self._compose_video_with_fallback(
                    assets, job.composition_settings or {}, job_id
                )

                # Phase 3: Complete job
                job.update_progress(100, JobStatus.COMPLETED)
                job.completed_at = datetime.now()
                db.add(video)
                db.commit()

                return video

        except (MediaAssetGeneratorError, VideoComposerError) as e:
            self._handle_job_failure(job_id, str(e))
            raise VideoGenerationServiceError(f"Generation workflow failed: {e}")
        except Exception as e:
            self._handle_job_failure(job_id, str(e))
            raise VideoGenerationServiceError(f"Unexpected error: {e}")

    def cancel_job(self, job_id: uuid.UUID) -> bool:
        """Cancel an active video generation job."""
        try:
            with get_db_session() as db:
                job = db.query(VideoGenerationJob).filter(
                    VideoGenerationJob.id == job_id
                ).first()

                if not job:
                    return False

                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    return False

                job.transition_status(JobStatus.FAILED, "Job cancelled by user")
                job.error_message = "Job cancelled by user"
                job.completed_at = datetime.now()
                db.commit()

                # Clean up any temporary files
                self.video_composer.cleanup_temp_files(job_id)
                return True

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False

    def get_job_status(self, job_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get current status of a video generation job."""
        try:
            with get_db_session() as db:
                job = db.query(VideoGenerationJob).filter(
                    VideoGenerationJob.id == job_id
                ).first()

                if not job:
                    return None

                return {
                    "id": str(job.id),
                    "status": job.status.value,
                    "progress_percentage": job.progress_percentage,
                    "started_at": job.started_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error_message": job.error_message,
                    "session_id": job.session_id,
                    "script_id": str(job.script_id)
                }

        except Exception as e:
            logger.error(f"Failed to get job status {job_id}: {e}")
            return None

    def _handle_job_failure(self, job_id: uuid.UUID, error_message: str):
        """Handle job failure by updating status and cleaning up."""
        try:
            with get_db_session() as db:
                job = db.query(VideoGenerationJob).filter(
                    VideoGenerationJob.id == job_id
                ).first()

                if job:
                    job.transition_status(JobStatus.FAILED, error_message)
                    job.error_message = error_message
                    job.completed_at = datetime.now()
                    db.commit()

            # Clean up temporary files
            self.video_composer.cleanup_temp_files(job_id)

        except Exception as e:
            logger.error(f"Failed to handle job failure for {job_id}: {e}")

    def cleanup_expired_jobs(self, max_age_days: int = 7) -> int:
        """Clean up old completed/failed jobs and their assets."""
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            cleaned_count = 0

            with get_db_session() as db:
                expired_jobs = db.query(VideoGenerationJob).filter(
                    VideoGenerationJob.completed_at < cutoff_date,
                    VideoGenerationJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED])
                ).all()

                for job in expired_jobs:
                    # Clean up associated assets
                    assets = db.query(MediaAsset).filter(
                        MediaAsset.generation_job_id == job.id
                    ).all()

                    for asset in assets:
                        try:
                            Path(asset.file_path).unlink(missing_ok=True)
                        except Exception:
                            pass

                    db.delete(job)
                    cleaned_count += 1

                db.commit()

            logger.info(f"Cleaned up {cleaned_count} expired jobs")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired jobs: {e}")
            return 0

    def _generate_assets_with_fallback(
        self, job_id: uuid.UUID, script_content: str, settings: Dict[str, Any]
    ) -> List[MediaAsset]:
        """Generate assets with graceful degradation for missing components."""
        try:
            return self.asset_generator.generate_assets_for_job(job_id, script_content, settings)
        except MediaAssetGeneratorError as e:
            logger.warning(f"Asset generation failed, using fallback: {e}")
            return self._create_fallback_assets(job_id, script_content)

    def _create_fallback_assets(self, job_id: uuid.UUID, script_content: str) -> List[MediaAsset]:
        """Create minimal fallback assets when generation fails."""
        fallback_assets = []

        try:
            # Create simple text-based video asset
            fallback_image = self.asset_generator.create_text_image(
                "Video Generation Error",
                {"background_color": "#000000", "text_color": "#ffffff"}
            )
            fallback_assets.append(fallback_image)

            logger.info("Created fallback assets for failed generation")
        except Exception as e:
            logger.error(f"Fallback asset creation failed: {e}")

        return fallback_assets

    def _compose_video_with_fallback(
        self, assets: List[MediaAsset], settings: Dict[str, Any], job_id: uuid.UUID
    ) -> GeneratedVideo:
        """Compose video with error handling and fallback."""
        def primary_composition():
            return self.video_composer.compose_video(assets, settings, job_id)

        def fallback_composition():
            logger.warning("Using fallback video composition")
            return self.video_composer.create_simple_video(assets[:1], job_id)

        return execute_ffmpeg_with_fallback(primary_composition, fallback_composition)

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._sanitize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # For objects with attributes, convert to dict
            return {key: self._sanitize_for_json(value) for key, value in obj.__dict__.items() if not key.startswith('_')}
        else:
            return obj