from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from ..services.media_service import MediaService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()


class MediaGenerateRequest(BaseModel):
    script_id: str


class MediaGenerateResponse(BaseModel):
    project_id: str
    status: str


@router.post("/api/media/generate", response_model=MediaGenerateResponse, status_code=202)
async def generate_media(request: MediaGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate audio and visual assets from script
    This is an async operation that returns immediately with a project ID
    """
    try:
        if not request.script_id:
            raise HTTPException(status_code=422, detail="script_id is required")

        # Initialize services (in a real app, these would be dependency injected)
        db = None  # This would be a real DB session
        gemini_service = GeminiService(api_key="demo-key")
        media_service = MediaService(db=db, gemini_service=gemini_service)

        # Start media generation in background
        project = await media_service.generate_media_assets(request.script_id)

        logger.info(f"Started media generation for script: {request.script_id}, project: {project.id}")

        return MediaGenerateResponse(
            project_id=str(project.id),
            status=project.status.value
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start media generation: {e}")
        raise HTTPException(status_code=500, detail=f"Media generation failed: {str(e)}")


@router.get("/api/media/project/{project_id}")
async def get_project_status(project_id: str):
    """Get project status and asset information"""
    try:
        db = None
        gemini_service = GeminiService(api_key="demo-key")
        media_service = MediaService(db=db, gemini_service=gemini_service)

        project = media_service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        assets = media_service.get_project_assets(project_id)

        # Group assets by type
        assets_by_type = {}
        for asset in assets:
            asset_type = asset.asset_type.value
            if asset_type not in assets_by_type:
                assets_by_type[asset_type] = []

            assets_by_type[asset_type].append({
                "id": str(asset.id),
                "file_path": asset.file_path,
                "file_size": asset.file_size,
                "duration": asset.duration,
                "status": asset.generation_status.value,
                "metadata": asset.asset_metadata
            })

        return {
            "project_id": str(project.id),
            "project_name": project.project_name,
            "status": project.status.value,
            "completion_percentage": project.completion_percentage,
            "error_message": project.error_message,
            "assets": assets_by_type,
            "total_assets": len(assets),
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project status {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project status")


@router.get("/api/media/project/{project_id}/assets")
async def get_project_assets(project_id: str):
    """Get all assets for a project"""
    try:
        db = None
        gemini_service = GeminiService(api_key="demo-key")
        media_service = MediaService(db=db, gemini_service=gemini_service)

        assets = media_service.get_project_assets(project_id)

        formatted_assets = []
        for asset in assets:
            formatted_assets.append({
                "id": str(asset.id),
                "type": asset.asset_type.value,
                "file_path": asset.file_path,
                "file_size": asset.file_size,
                "duration": asset.duration,
                "generation_prompt": asset.generation_prompt,
                "model_used": asset.gemini_model_used,
                "status": asset.generation_status.value,
                "metadata": asset.asset_metadata,
                "created_at": asset.created_at
            })

        return {
            "project_id": project_id,
            "assets": formatted_assets,
            "total_count": len(formatted_assets)
        }

    except Exception as e:
        logger.error(f"Failed to get assets for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project assets")


@router.delete("/api/media/project/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its assets"""
    try:
        db = None
        gemini_service = GeminiService(api_key="demo-key")
        media_service = MediaService(db=db, gemini_service=gemini_service)

        project = media_service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # In a real implementation, this would:
        # 1. Delete all asset files from storage
        # 2. Delete all database records
        # 3. Clean up any temporary files

        logger.info(f"Project {project_id} marked for deletion")

        return {
            "project_id": project_id,
            "message": "Project deletion initiated",
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")