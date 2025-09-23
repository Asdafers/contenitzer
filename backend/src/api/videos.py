from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

from ..services.video_service import VideoService
from ..services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter()


class VideoComposeRequest(BaseModel):
    project_id: str


class VideoUploadRequest(BaseModel):
    project_id: str
    youtube_api_key: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list] = None


@router.post("/api/videos/compose", status_code=202)
async def compose_video(request: VideoComposeRequest, background_tasks: BackgroundTasks):
    """
    Compose final video from project assets
    This is an async operation that returns immediately
    """
    try:
        if not request.project_id:
            raise HTTPException(status_code=422, detail="project_id is required")

        # Initialize services
        db = None  # This would be a real DB session
        video_service = VideoService(db=db)

        # Validate that project exists and is ready for composition
        if not video_service.validate_assets_for_composition(request.project_id):
            raise HTTPException(
                status_code=400,
                detail="Project not ready for composition - missing required assets"
            )

        # Start video composition in background
        composed_video = await video_service.compose_video(request.project_id)

        logger.info(f"Started video composition for project: {request.project_id}")

        return {
            "project_id": request.project_id,
            "composed_video_id": str(composed_video.id),
            "status": "composition_started",
            "message": "Video composition started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start video composition: {e}")
        raise HTTPException(status_code=500, detail=f"Video composition failed: {str(e)}")


@router.get("/api/videos/compose/{project_id}/status")
async def get_composition_status(project_id: str):
    """Get video composition status"""
    try:
        db = None
        video_service = VideoService(db=db)

        composed_video = video_service.get_composed_video_by_project(project_id)
        if not composed_video:
            raise HTTPException(status_code=404, detail="Composed video not found")

        return {
            "project_id": project_id,
            "composed_video_id": str(composed_video.id),
            "file_path": composed_video.file_path,
            "file_size": composed_video.file_size,
            "duration": composed_video.duration,
            "resolution": composed_video.resolution,
            "format": composed_video.format,
            "upload_status": composed_video.upload_status.value,
            "youtube_video_id": composed_video.youtube_video_id,
            "created_at": composed_video.created_at,
            "uploaded_at": composed_video.uploaded_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get composition status for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get composition status")


@router.post("/api/videos/upload", status_code=202)
async def upload_video(request: VideoUploadRequest, background_tasks: BackgroundTasks):
    """
    Upload composed video to YouTube
    This is an async operation that returns immediately
    """
    try:
        if not request.project_id:
            raise HTTPException(status_code=422, detail="project_id is required")
        if not request.youtube_api_key:
            raise HTTPException(status_code=422, detail="youtube_api_key is required")

        # Initialize services
        db = None  # This would be a real DB session
        upload_service = UploadService(db=db)

        # Validate YouTube API key
        if not upload_service.validate_youtube_api_key(request.youtube_api_key):
            raise HTTPException(status_code=401, detail="Invalid YouTube API key")

        # Start upload in background
        composed_video = await upload_service.upload_to_youtube(
            project_id=request.project_id,
            youtube_api_key=request.youtube_api_key,
            title=request.title,
            description=request.description,
            tags=request.tags
        )

        logger.info(f"Started YouTube upload for project: {request.project_id}")

        return {
            "project_id": request.project_id,
            "upload_status": composed_video.upload_status.value,
            "youtube_video_id": composed_video.youtube_video_id,
            "message": "YouTube upload started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start YouTube upload: {e}")
        raise HTTPException(status_code=500, detail=f"YouTube upload failed: {str(e)}")


@router.get("/api/videos/upload/{project_id}/status")
async def get_upload_status(project_id: str):
    """Get YouTube upload status"""
    try:
        db = None
        upload_service = UploadService(db=db)

        upload_status = upload_service.get_upload_status(project_id)
        if not upload_status:
            raise HTTPException(status_code=404, detail="Upload status not found")

        return upload_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upload status")


@router.get("/api/videos/project/{project_id}")
async def get_video_project_details(project_id: str):
    """Get complete video project details including composition and upload status"""
    try:
        db = None
        video_service = VideoService(db=db)
        upload_service = UploadService(db=db)

        # Get composition details
        composed_video = video_service.get_composed_video_by_project(project_id)
        if not composed_video:
            raise HTTPException(status_code=404, detail="Video project not found")

        # Get upload status
        upload_status = upload_service.get_upload_status(project_id)

        return {
            "project_id": project_id,
            "composition": {
                "composed_video_id": str(composed_video.id),
                "file_path": composed_video.file_path,
                "file_size": composed_video.file_size,
                "duration": composed_video.duration,
                "resolution": composed_video.resolution,
                "format": composed_video.format,
                "composition_settings": composed_video.composition_settings,
                "created_at": composed_video.created_at
            },
            "upload": upload_status,
            "youtube_url": f"https://youtube.com/watch?v={composed_video.youtube_video_id}" if composed_video.youtube_video_id else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video project details for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video project details")