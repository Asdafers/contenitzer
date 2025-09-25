"""
Video Generation API endpoints.
Handles video generation requests and status queries.
"""
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.video_generation_service import VideoGenerationService, VideoGenerationServiceError
from ..lib.database import get_db_session
from ..models.generated_video import GeneratedVideo
from ..models.video_generation_job import VideoGenerationJob
from ..tasks.media_tasks import generate_media_from_script, compose_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["video-generation"])


class VideoGenerationRequest(BaseModel):
    """Request model for video generation."""
    script_id: str = Field(..., description="UUID of the script to generate video from")
    session_id: str = Field(..., description="User session ID for progress tracking")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Video generation options"
    )

    class Config:
        schema_extra = {
            "example": {
                "script_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "user-session-123",
                "options": {
                    "resolution": "1920x1080",
                    "duration": 180,
                    "quality": "high",
                    "include_audio": True
                }
            }
        }


class VideoGenerationResponse(BaseModel):
    """Response model for video generation job creation."""
    id: str = Field(..., description="Job ID")
    session_id: str = Field(..., description="Session ID")
    script_id: str = Field(..., description="Script ID")
    status: str = Field(..., description="Job status")
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    started_at: str = Field(..., description="Job start timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class GeneratedVideoResponse(BaseModel):
    """Response model for completed video information."""
    id: str = Field(..., description="Video ID")
    title: str = Field(..., description="Video title")
    url: str = Field(..., description="Video URL path")
    duration: int = Field(..., description="Duration in seconds")
    resolution: str = Field(..., description="Video resolution")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: str = Field(..., description="Video format")
    creation_timestamp: str = Field(..., description="Creation timestamp")
    completion_timestamp: Optional[str] = Field(None, description="Completion timestamp")
    status: str = Field(..., description="Video status")
    script_id: str = Field(..., description="Source script ID")


def get_video_service() -> VideoGenerationService:
    """Dependency to get video generation service."""
    return VideoGenerationService()


@router.post("/generate", response_model=VideoGenerationResponse, status_code=202)
async def generate_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    video_service: VideoGenerationService = Depends(get_video_service)
):
    """
    Generate actual video from script.

    Creates a video generation job and triggers the workflow to create real video files.
    """
    try:
        # Validate script exists
        with get_db_session() as db:
            from ..models.uploaded_script import UploadedScript
            from ..models.video_script import VideoScript

            script_uuid = uuid.UUID(request.script_id)

            # Check if script exists
            uploaded_script = db.query(UploadedScript).filter(
                UploadedScript.id == script_uuid
            ).first()

            video_script = db.query(VideoScript).filter(
                VideoScript.id == script_uuid
            ).first()

            if not uploaded_script and not video_script:
                raise HTTPException(
                    status_code=404,
                    detail=f"Script {request.script_id} not found"
                )

        # Validate options
        options = request.options or {}
        _validate_generation_options(options)

        # Create generation job
        job = video_service.create_generation_job(
            script_id=script_uuid,
            session_id=request.session_id,
            options=options
        )

        # Trigger background workflow
        background_tasks.add_task(
            _execute_video_generation_workflow,
            str(job.id),
            request.script_id,
            request.session_id,
            options
        )

        # Return job information
        return VideoGenerationResponse(
            id=str(job.id),
            session_id=job.session_id,
            script_id=str(job.script_id),
            status=job.status.value,
            progress_percentage=job.progress_percentage,
            started_at=job.started_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error_message=job.error_message
        )

    except ValueError as e:
        logger.error(f"Invalid request parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except VideoGenerationServiceError as e:
        logger.error(f"Video generation service error: {e}")
        raise HTTPException(status_code=500, detail="Video generation failed")
    except Exception as e:
        logger.error(f"Unexpected error in generate_video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{video_id}", response_model=GeneratedVideoResponse)
async def get_video(
    video_id: str,
    video_service: VideoGenerationService = Depends(get_video_service)
):
    """
    Get generated video information.

    Returns video metadata if completed, or job status if still generating.
    """
    try:
        video_uuid = uuid.UUID(video_id)

        with get_db_session() as db:
            # First check if this is a completed video
            video = db.query(GeneratedVideo).filter(
                GeneratedVideo.id == video_uuid
            ).first()

            if video:
                # Return completed video information
                return GeneratedVideoResponse(
                    id=str(video.id),
                    title=video.title,
                    url=video.url_path,
                    duration=video.duration,
                    resolution=video.resolution,
                    file_size=video.file_size,
                    format=video.format,
                    creation_timestamp=video.creation_timestamp.isoformat(),
                    completion_timestamp=video.completion_timestamp.isoformat() if video.completion_timestamp else None,
                    status=video.generation_status.value,
                    script_id=str(video.script_id)
                )

            # Check if this might be a job ID instead
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == video_uuid
            ).first()

            if job:
                if job.status.value == "COMPLETED":
                    # Job is completed, look for the generated video
                    generated_video = db.query(GeneratedVideo).filter(
                        GeneratedVideo.generation_job_id == job.id
                    ).first()

                    if generated_video:
                        return GeneratedVideoResponse(
                            id=str(generated_video.id),
                            title=generated_video.title,
                            url=generated_video.url_path,
                            duration=generated_video.duration,
                            resolution=generated_video.resolution,
                            file_size=generated_video.file_size,
                            format=generated_video.format,
                            creation_timestamp=generated_video.creation_timestamp.isoformat(),
                            completion_timestamp=generated_video.completion_timestamp.isoformat() if generated_video.completion_timestamp else None,
                            status=generated_video.generation_status.value,
                            script_id=str(generated_video.script_id)
                        )

                # Job still in progress, return 202 with job status
                raise HTTPException(
                    status_code=202,
                    detail={
                        "message": "Video still being generated",
                        "job_id": str(job.id),
                        "status": job.status.value,
                        "progress_percentage": job.progress_percentage,
                        "started_at": job.started_at.isoformat()
                    }
                )

        # Video/job not found
        raise HTTPException(
            status_code=404,
            detail=f"Video {video_id} not found"
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _validate_generation_options(options: Dict[str, Any]):
    """Validate video generation options."""
    if "resolution" in options:
        valid_resolutions = ["1920x1080", "1280x720", "3840x2160"]
        if options["resolution"] not in valid_resolutions:
            raise ValueError(f"Invalid resolution. Must be one of: {valid_resolutions}")

    if "duration" in options:
        duration = options["duration"]
        if not isinstance(duration, int) or duration < 30 or duration > 600:
            raise ValueError("Duration must be between 30 and 600 seconds")

    if "quality" in options:
        valid_qualities = ["high", "medium", "low"]
        if options["quality"] not in valid_qualities:
            raise ValueError(f"Invalid quality. Must be one of: {valid_qualities}")


async def _execute_video_generation_workflow(
    job_id: str,
    script_id: str,
    session_id: str,
    options: Dict[str, Any]
):
    """Execute the video generation workflow in background."""
    try:
        # Step 1: Generate media assets
        media_result = generate_media_from_script.delay(
            session_id=session_id,
            script_id=script_id,
            media_options=options
        )

        # Wait for media generation to complete
        media_assets = media_result.get()

        if media_assets["status"] != "success":
            raise Exception(f"Media generation failed: {media_assets}")

        # Step 2: Compose video
        video_result = compose_video.delay(
            session_id=session_id,
            job_id=job_id,
            composition_options=options
        )

        # Video composition will complete in background
        logger.info(f"Video generation workflow initiated for job {job_id}")

    except Exception as e:
        logger.error(f"Video generation workflow failed for job {job_id}: {e}")
        # Update job status to failed
        try:
            video_service = VideoGenerationService()
            video_service._handle_job_failure(uuid.UUID(job_id), str(e))
        except Exception as cleanup_error:
            logger.error(f"Failed to handle job failure cleanup: {cleanup_error}")