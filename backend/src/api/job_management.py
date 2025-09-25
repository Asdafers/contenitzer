"""
Job Management API endpoints.
Handles video generation job status and control operations.
"""
import logging
import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..services.video_generation_service import VideoGenerationService
from ..lib.database import get_db_session
from ..models.video_generation_job import VideoGenerationJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos/jobs", tags=["job-management"])


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    id: str = Field(..., description="Job ID")
    session_id: str = Field(..., description="Session ID")
    script_id: str = Field(..., description="Script ID")
    status: str = Field(..., description="Job status")
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    started_at: str = Field(..., description="Job start timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="Resource usage metrics")


class JobCancelResponse(BaseModel):
    """Response model for job cancellation."""
    id: str = Field(..., description="Job ID")
    status: str = Field(..., description="New job status")
    message: str = Field(..., description="Cancellation result message")
    cancelled_at: str = Field(..., description="Cancellation timestamp")


def get_video_service() -> VideoGenerationService:
    """Dependency to get video generation service."""
    return VideoGenerationService()


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    video_service: VideoGenerationService = Depends(get_video_service)
):
    """
    Get video generation job status.

    Returns current status, progress, and metadata for a video generation job.
    """
    try:
        job_uuid = uuid.UUID(job_id)

        # Use service method to get job status
        job_status = video_service.get_job_status(job_uuid)

        if not job_status:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        # Get additional details from database
        with get_db_session() as db:
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == job_uuid
            ).first()

            if job:
                # Calculate estimated completion if job is active
                estimated_completion = None
                if job.status.value in ["PENDING", "MEDIA_GENERATION", "VIDEO_COMPOSITION"]:
                    # Simple estimation based on progress (could be enhanced)
                    if job.progress_percentage > 0:
                        import datetime
                        elapsed = datetime.datetime.now() - job.started_at
                        total_estimated = elapsed / (job.progress_percentage / 100)
                        estimated_completion = (job.started_at + total_estimated).isoformat()

                return JobStatusResponse(
                    id=str(job.id),
                    session_id=job.session_id,
                    script_id=str(job.script_id),
                    status=job.status.value,
                    progress_percentage=job.progress_percentage,
                    started_at=job.started_at.isoformat(),
                    completed_at=job.completed_at.isoformat() if job.completed_at else None,
                    error_message=job.error_message,
                    estimated_completion=estimated_completion,
                    resource_usage=job.resource_usage
                )

        # Fallback to service response if database query fails
        return JobStatusResponse(**job_status)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Unexpected error in get_job_status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_job(
    job_id: str,
    video_service: VideoGenerationService = Depends(get_video_service)
):
    """
    Cancel active video generation job.

    Stops an in-progress video generation job and cleans up associated resources.
    """
    try:
        job_uuid = uuid.UUID(job_id)

        # Check job exists and get current status
        with get_db_session() as db:
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == job_uuid
            ).first()

            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job {job_id} not found"
                )

            # Check if job can be cancelled
            if job.status.value in ["COMPLETED", "FAILED"]:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "Job cannot be cancelled",
                        "reason": f"Job is already {job.status.value.lower()}",
                        "current_status": job.status.value,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None
                    }
                )

        # Attempt to cancel the job
        cancellation_successful = video_service.cancel_job(job_uuid)

        if cancellation_successful:
            from datetime import datetime
            return JobCancelResponse(
                id=job_id,
                status="FAILED",
                message="Job cancelled successfully",
                cancelled_at=datetime.now().isoformat()
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel job"
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cancel_job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    video_service: VideoGenerationService = Depends(get_video_service)
):
    """
    Get detailed progress information for a video generation job.

    Returns detailed progress including current operation and time estimates.
    """
    try:
        job_uuid = uuid.UUID(job_id)

        with get_db_session() as db:
            job = db.query(VideoGenerationJob).filter(
                VideoGenerationJob.id == job_uuid
            ).first()

            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job {job_id} not found"
                )

            # Get progress from video composer if job is in composition phase
            detailed_progress = {}
            if job.status.value == "VIDEO_COMPOSITION":
                try:
                    detailed_progress = video_service.video_composer.get_composition_progress(job_uuid)
                except Exception as e:
                    logger.warning(f"Failed to get detailed progress: {e}")

            # Create progress response
            progress_response = {
                "job_id": str(job.id),
                "status": job.status.value,
                "progress_percentage": job.progress_percentage,
                "started_at": job.started_at.isoformat(),
                "current_stage": _get_stage_description(job.status.value),
                "detailed_progress": detailed_progress
            }

            # Add timing estimates
            if job.status.value not in ["COMPLETED", "FAILED"]:
                import datetime
                elapsed = datetime.datetime.now() - job.started_at
                if job.progress_percentage > 0:
                    total_estimated = elapsed / (job.progress_percentage / 100)
                    remaining = total_estimated - elapsed
                    progress_response["estimated_remaining_seconds"] = int(remaining.total_seconds())

            return progress_response

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Unexpected error in get_job_progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _get_stage_description(status: str) -> str:
    """Get human-readable description of job stage."""
    stage_descriptions = {
        "PENDING": "Initializing video generation",
        "MEDIA_GENERATION": "Creating media assets from script",
        "VIDEO_COMPOSITION": "Composing final video",
        "COMPLETED": "Video generation complete",
        "FAILED": "Video generation failed"
    }
    return stage_descriptions.get(status, "Unknown stage")