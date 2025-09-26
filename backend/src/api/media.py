from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
from datetime import datetime

from ..services.media_service import MediaService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()


class MediaGenerateRequest(BaseModel):
    script_content: str
    asset_types: List[str]  # ["image", "video_clip"]
    num_assets: Optional[int] = 5
    preferred_model: Optional[str] = "gemini-2.5-flash-image"
    allow_fallback: Optional[bool] = True


class MediaGenerateResponse(BaseModel):
    job_id: str
    status: str
    model_selected: str
    estimated_completion: Optional[str] = None


@router.post("/api/media/generate", response_model=MediaGenerateResponse, status_code=202)
async def generate_media(request: MediaGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate media assets using Gemini 2.5 Flash Image model with fallback
    """
    try:
        if not request.script_content:
            raise HTTPException(status_code=400, detail="script_content is required")
        if not request.asset_types:
            raise HTTPException(status_code=400, detail="asset_types is required")

        # Initialize services
        db = None  # Would be dependency injected
        gemini_service = GeminiService(api_key="demo-key")

        # Set preferred model if specified
        if request.preferred_model:
            gemini_service.set_image_model(request.preferred_model)

        # Check model availability
        model_status = await gemini_service.check_model_availability(request.preferred_model)

        # Determine which model will be used
        if model_status.get('available'):
            selected_model = request.preferred_model
        elif request.allow_fallback:
            # Check fallback model
            fallback_status = await gemini_service.check_model_availability("gemini-pro")
            if fallback_status.get('available'):
                selected_model = "gemini-pro"
            else:
                raise HTTPException(status_code=503, detail="All models temporarily unavailable")
        else:
            raise HTTPException(status_code=503, detail="Preferred model unavailable and fallback disabled")

        # Generate job ID and estimated completion
        job_id = str(uuid.uuid4())
        estimated_seconds = len(request.asset_types) * (request.num_assets or 5) * 30  # 30s per asset
        estimated_completion = datetime.now().isoformat() + "Z"

        # In real implementation, would start background task here
        logger.info(f"Started media generation job {job_id} with model {selected_model}")

        return MediaGenerateResponse(
            job_id=job_id,
            status="pending",
            model_selected=selected_model,
            estimated_completion=estimated_completion
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