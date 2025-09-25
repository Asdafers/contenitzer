"""
Celery tasks for media generation and video composition.
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from datetime import datetime
import uuid

from celery_worker import celery_app
from ..services.progress_service import get_progress_service, ProgressEventType
from ..services.task_queue_service import get_task_queue_service, TaskStatus
from ..lib.database import get_db_session
from ..models.uploaded_script import UploadedScript
from ..models.video_script import VideoScript
from ..services.video_generation_service import VideoGenerationService, VideoGenerationServiceError

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="media_tasks.generate_media_from_script")
def generate_media_from_script(
    self,
    session_id: str,
    script_id: str,
    media_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate media assets (images, audio, video clips) from a script using real video generation.

    Args:
        session_id: User session ID for progress tracking
        script_id: UUID of the script to generate media for
        media_options: Options for media generation (resolution, style, etc.)

    Returns:
        Dictionary with generated media assets and metadata
    """
    task_id = self.request.id
    progress_service = get_progress_service()
    task_queue = get_task_queue_service()
    video_service = VideoGenerationService()

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        # Publish start progress
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message=f"Starting real media generation for script {script_id}",
            percentage=0,
            task_id=task_id
        )

        with get_db_session() as db:
            # Get the script content
            script_content, script_title = _get_script_content(db, script_id)

            # Create generation job
            generation_options = media_options or {}
            generation_options.update({
                "script_id": uuid.UUID(script_id),
                "session_id": session_id,
                "duration": generation_options.get("duration", 180),
                "resolution": generation_options.get("resolution", "1920x1080"),
                "quality": generation_options.get("quality", "high"),
                "include_audio": generation_options.get("include_audio", True)
            })

            job_id = video_service.create_generation_job(
                script_id=uuid.UUID(script_id),
                session_id=session_id,
                options=generation_options
            )

            # Progress: Analyzing script content
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Analyzing script content for media requirements",
                percentage=15,
                task_id=task_id
            )

            # Generate real media assets
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Generating background images and visual assets",
                percentage=35,
                task_id=task_id
            )

            assets = video_service.asset_generator.generate_assets_for_job(
                job_id, script_content, generation_options
            )

            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Creating audio tracks and voiceovers",
                percentage=60,
                task_id=task_id
            )

            # Organize assets by type for result
            assets_by_type = {
                "background_images": [],
                "audio_tracks": [],
                "video_clips": [],
                "text_overlays": []
            }

            for asset in assets:
                # Assets are already dictionaries, just use them directly
                asset_data = asset

                if asset_data["asset_type"] == "IMAGE":
                    assets_by_type["background_images"].append(asset_data)
                elif asset_data["asset_type"] == "AUDIO":
                    assets_by_type["audio_tracks"].append(asset_data)
                elif asset_data["asset_type"] == "VIDEO_CLIP":
                    assets_by_type["video_clips"].append(asset_data)
                elif asset_data["asset_type"] == "TEXT_OVERLAY":
                    assets_by_type["text_overlays"].append(asset_data)

            # Complete task
            result = {
                "status": "success",
                "script_id": script_id,
                "script_title": script_title,
                "job_id": str(job_id),
                "media_assets": assets_by_type,
                "total_assets": len(assets),
                "estimated_duration": generation_options["duration"],
                "generated_at": datetime.now().isoformat()
            }

            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_COMPLETED,
                message=f"Media generation completed successfully - {result['total_assets']} assets created",
                percentage=100,
                task_id=task_id
            )

            task_queue.update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)

            logger.info(f"Real media generation task {task_id} completed for script {script_id}")
            return result

    except VideoGenerationServiceError as e:
        error_msg = f"Video generation service failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        _handle_task_failure(task_id, session_id, error_msg, progress_service, task_queue)
        raise
    except Exception as e:
        error_msg = f"Media generation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        _handle_task_failure(task_id, session_id, error_msg, progress_service, task_queue)
        raise


@celery_app.task(bind=True, name="media_tasks.compose_video")
def compose_video(
    self,
    session_id: str,
    job_id: str,
    composition_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compose final video from generated media assets using real video composition.

    Args:
        session_id: User session ID for progress tracking
        job_id: Video generation job ID containing the assets
        composition_options: Video composition settings

    Returns:
        Dictionary with final video information
    """
    task_id = self.request.id
    progress_service = get_progress_service()
    task_queue = get_task_queue_service()
    video_service = VideoGenerationService()

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message="Starting real video composition",
            percentage=0,
            task_id=task_id
        )

        # Progress: Preparing timeline
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_PROGRESS,
            message="Preparing video timeline and sequencing",
            percentage=20,
            task_id=task_id
        )

        # Get media assets from job and perform video composition within the same session
        with get_db_session() as db:
            from ..models.media_asset import MediaAsset
            assets = db.query(MediaAsset).filter(
                MediaAsset.generation_job_id == uuid.UUID(job_id)
            ).all()

            if not assets:
                raise ValueError(f"No media assets found for job {job_id}")

            # Progress: Compositing layers
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Compositing video layers and effects",
                percentage=50,
                task_id=task_id
            )

            # Get job information to extract required options
            from ..models.video_generation_job import VideoGenerationJob
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == uuid.UUID(job_id)
            ).first()

            if not job:
                raise ValueError(f"Video generation job {job_id} not found")

            # Use real video composer
            options = composition_options or {}

            # Get composition settings with safe null checking
            settings = job.composition_settings if job.composition_settings else {}

            options.update({
                "session_id": session_id,
                "title": options.get("title", "Generated Video Content"),
                "duration": settings.get("duration", 180),  # Get duration from job settings
                "resolution": settings.get("resolution", "1920x1080"),  # Get resolution from job settings
                "script_id": job.script_id
            })

            # Progress: Rendering video
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Rendering final video file using FFmpeg",
                percentage=80,
                task_id=task_id
            )

            # Create the GeneratedVideo record within this session
            from ..models.generated_video import GeneratedVideo, GenerationStatusEnum as VideoStatus
            import uuid as uuid_module
            from pathlib import Path

            video_id = uuid_module.uuid4()
            filename = f"video_{video_id}.mp4"

            # Create video record in the session
            generated_video = GeneratedVideo(
                id=video_id,
                file_path=f"/code/contentizer/backend/media/videos/{filename}",
                url_path=f"/media/videos/{filename}",
                title=options.get("title", "Generated Video Content"),
                duration=options["duration"],
                resolution=options["resolution"],
                format="mp4",
                generation_status=VideoStatus.GENERATING,
                script_id=options["script_id"],
                session_id=options["session_id"],
                generation_job_id=uuid.UUID(job_id),
                creation_timestamp=datetime.now()
            )

            db.add(generated_video)
            db.flush()  # Get the ID assigned but don't commit yet

            # Now compose the actual video file (without creating DB record)
            video_info = video_service.video_composer.compose_video_file_only(
                assets, options, generated_video.file_path
            )

            # Update video record with actual file properties
            generated_video.file_size = video_info.get("file_size", 0)
            generated_video.duration = video_info.get("duration", options["duration"])
            generated_video.generation_status = VideoStatus.COMPLETED
            generated_video.completion_timestamp = datetime.now()

            db.commit()
            # No need to refresh since we're still in the same session

            # Create result inside the session while generated_video is still attached
            result = {
                "status": "success",
                "video": {
                    "video_id": str(generated_video.id),
                    "title": generated_video.title,
                    "url": generated_video.url_path,
                    "duration": generated_video.duration,
                    "resolution": generated_video.resolution,
                    "file_size": generated_video.file_size,
                    "format": generated_video.format,
                    "file_path": generated_video.file_path
                },
                "job_id": job_id,
                "composed_at": datetime.now().isoformat()
            }

        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_COMPLETED,
            message="Video composition completed successfully",
            percentage=100,
            task_id=task_id
        )

        task_queue.update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)

        logger.info(f"Real video composition task {task_id} completed")
        return result

    except VideoGenerationServiceError as e:
        error_msg = f"Video composition service failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        _handle_task_failure(task_id, session_id, error_msg, progress_service, task_queue)
        raise
    except Exception as e:
        error_msg = f"Video composition failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        _handle_task_failure(task_id, session_id, error_msg, progress_service, task_queue)
        raise


def _get_script_content(db, script_id: str) -> tuple[str, str]:
    """Helper function to get script content and title."""
    # Try to find in uploaded scripts first
    uploaded_script = db.query(UploadedScript).filter(
        UploadedScript.id == uuid.UUID(script_id)
    ).first()

    if uploaded_script:
        return uploaded_script.content, uploaded_script.file_name or "Uploaded Script"

    # Try to find in generated scripts
    video_script = db.query(VideoScript).filter(
        VideoScript.id == uuid.UUID(script_id)
    ).first()

    if video_script:
        return video_script.content, video_script.title

    raise ValueError(f"Script {script_id} not found")


def _handle_task_failure(task_id, session_id, error_msg, progress_service, task_queue):
    """Helper function to handle task failures."""
    try:
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )
        task_queue.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
    except Exception as cleanup_error:
        logger.error(f"Failed to cleanup task {task_id}: {cleanup_error}")