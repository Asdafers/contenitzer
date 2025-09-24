"""
Celery tasks for media generation and video composition.
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from datetime import datetime
import uuid
import time

from celery_worker import celery_app
from ..services.progress_service import get_progress_service, ProgressEventType
from ..services.task_queue_service import get_task_queue_service, TaskStatus
from ..lib.database import get_db_session
from ..models.uploaded_script import UploadedScript
from ..models.video_script import VideoScript

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="media_tasks.generate_media_from_script")
def generate_media_from_script(
    self,
    session_id: str,
    script_id: str,
    media_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate media assets (images, audio, video clips) from a script.

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

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        # Publish start progress
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message=f"Starting media generation for script {script_id}",
            percentage=0,
            task_id=task_id
        )

        with get_db_session() as db:
            # Get the script (either uploaded or generated)
            script = None

            # Try to find in uploaded scripts first
            uploaded_script = db.query(UploadedScript).filter(
                UploadedScript.id == uuid.UUID(script_id)
            ).first()

            if uploaded_script:
                script_content = uploaded_script.content
                script_title = uploaded_script.filename or "Uploaded Script"
                logger.info(f"Found uploaded script {script_id}")
            else:
                # Try to find in generated scripts
                video_script = db.query(VideoScript).filter(
                    VideoScript.id == uuid.UUID(script_id)
                ).first()

                if video_script:
                    script_content = video_script.content
                    script_title = video_script.title
                    logger.info(f"Found generated script {script_id}")
                else:
                    raise ValueError(f"Script {script_id} not found")

            # Progress: Analyzing script content
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Analyzing script content for media requirements",
                percentage=15,
                task_id=task_id
            )

            # Simulate script analysis
            time.sleep(1)

            # Progress: Generating background images
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Generating background images and visual assets",
                percentage=35,
                task_id=task_id
            )

            # Simulate image generation
            time.sleep(2)

            # Progress: Creating audio tracks
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Creating audio tracks and voiceovers",
                percentage=60,
                task_id=task_id
            )

            # Simulate audio generation
            time.sleep(2)

            # Progress: Generating video clips
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Generating video clips and transitions",
                percentage=80,
                task_id=task_id
            )

            # Simulate video generation
            time.sleep(1.5)

            # Create mock media assets result
            media_assets = {
                "background_images": [
                    {"id": "bg_001", "url": "/media/backgrounds/scene_001.jpg", "duration": 30},
                    {"id": "bg_002", "url": "/media/backgrounds/scene_002.jpg", "duration": 45},
                    {"id": "bg_003", "url": "/media/backgrounds/scene_003.jpg", "duration": 25}
                ],
                "audio_tracks": [
                    {"id": "voice_001", "url": "/media/audio/voiceover_main.mp3", "duration": 180},
                    {"id": "music_001", "url": "/media/audio/background_music.mp3", "duration": 180}
                ],
                "video_clips": [
                    {"id": "clip_001", "url": "/media/clips/intro.mp4", "duration": 10},
                    {"id": "clip_002", "url": "/media/clips/main_content.mp4", "duration": 160},
                    {"id": "clip_003", "url": "/media/clips/outro.mp4", "duration": 10}
                ],
                "metadata": {
                    "total_duration": 180,
                    "resolution": "1920x1080",
                    "fps": 30,
                    "format": "mp4"
                }
            }

            # Complete task
            result = {
                "status": "success",
                "script_id": script_id,
                "script_title": script_title,
                "media_assets": media_assets,
                "total_assets": len(media_assets["background_images"]) + len(media_assets["audio_tracks"]) + len(media_assets["video_clips"]),
                "estimated_duration": media_assets["metadata"]["total_duration"],
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

            logger.info(f"Media generation task {task_id} completed for script {script_id}")
            return result

    except Exception as e:
        error_msg = f"Media generation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        # Publish error
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )

        task_queue.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
        raise


@celery_app.task(bind=True, name="media_tasks.compose_video")
def compose_video(
    self,
    session_id: str,
    media_assets: Dict[str, Any],
    composition_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compose final video from generated media assets.

    Args:
        session_id: User session ID for progress tracking
        media_assets: Dictionary containing all media assets to compose
        composition_options: Video composition settings

    Returns:
        Dictionary with final video information
    """
    task_id = self.request.id
    progress_service = get_progress_service()
    task_queue = get_task_queue_service()

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message="Starting video composition",
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
        time.sleep(1)

        # Progress: Compositing layers
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_PROGRESS,
            message="Compositing video layers and effects",
            percentage=50,
            task_id=task_id
        )
        time.sleep(2)

        # Progress: Rendering video
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_PROGRESS,
            message="Rendering final video file",
            percentage=80,
            task_id=task_id
        )
        time.sleep(2)

        # Create final video result
        video_result = {
            "video_id": str(uuid.uuid4()),
            "title": "Generated Video Content",
            "url": "/media/videos/final_video.mp4",
            "duration": media_assets.get("metadata", {}).get("total_duration", 180),
            "resolution": "1920x1080",
            "file_size": "245MB",
            "format": "mp4"
        }

        result = {
            "status": "success",
            "video": video_result,
            "composition_time": "6.5 seconds",
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

        logger.info(f"Video composition task {task_id} completed")
        return result

    except Exception as e:
        error_msg = f"Video composition failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )

        task_queue.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
        raise