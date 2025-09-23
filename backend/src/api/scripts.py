from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from ..services.script_service import ScriptService
from ..services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptGenerateRequest(BaseModel):
    input_type: str  # 'theme', 'manual_subject', 'manual_script'
    theme_id: Optional[str] = None
    manual_input: Optional[str] = None


class ScriptGenerateResponse(BaseModel):
    script_id: str
    content: str
    estimated_duration: int


@router.post("/api/scripts/generate", response_model=ScriptGenerateResponse)
async def generate_script(request: ScriptGenerateRequest):
    """
    Generate script from theme or manual input
    Supports three input types:
    - theme: Generate from trending theme ID
    - manual_subject: Generate from user-provided topic
    - manual_script: Process user-provided complete script
    """
    try:
        # Validate input type
        if request.input_type not in ['theme', 'manual_subject', 'manual_script']:
            raise HTTPException(
                status_code=422,
                detail="input_type must be 'theme', 'manual_subject', or 'manual_script'"
            )

        # Initialize services (in a real app, these would be dependency injected)
        # For now, we'll simulate the database connection
        db = None  # This would be a real DB session
        gemini_service = GeminiService(api_key="demo-key")  # This would be from config
        script_service = ScriptService(db=db, gemini_service=gemini_service)

        script = None

        if request.input_type == 'theme':
            if not request.theme_id:
                raise HTTPException(status_code=422, detail="theme_id required for theme input type")

            # In a real implementation, we'd fetch theme details from DB
            theme_name = f"Theme_{request.theme_id}"
            theme_description = "Sample theme description"

            script = await script_service.generate_from_theme(
                theme_id=request.theme_id,
                theme_name=theme_name,
                theme_description=theme_description
            )

        elif request.input_type == 'manual_subject':
            if not request.manual_input:
                raise HTTPException(status_code=422, detail="manual_input required for manual_subject input type")

            script = await script_service.generate_from_manual_subject(
                subject=request.manual_input
            )

        elif request.input_type == 'manual_script':
            if not request.manual_input:
                raise HTTPException(status_code=422, detail="manual_input required for manual_script input type")

            script = await script_service.process_manual_script(
                script_content=request.manual_input
            )

        logger.info(f"Generated script: {script.id} using {request.input_type}")

        return ScriptGenerateResponse(
            script_id=str(script.id),
            content=script.content,
            estimated_duration=script.estimated_duration
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@router.get("/api/scripts/{script_id}")
async def get_script(script_id: str):
    """Get script by ID"""
    try:
        # In a real implementation, we'd use dependency injection for the service
        db = None
        gemini_service = GeminiService(api_key="demo-key")
        script_service = ScriptService(db=db, gemini_service=gemini_service)

        script = script_service.get_script_by_id(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        return {
            "script_id": str(script.id),
            "title": script.title,
            "content": script.content,
            "estimated_duration": script.estimated_duration,
            "input_source": script.input_source.value,
            "created_at": script.created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get script {script_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get script")


@router.post("/api/scripts/{script_id}/validate")
async def validate_script(script_id: str):
    """Validate script meets requirements"""
    try:
        db = None
        gemini_service = GeminiService(api_key="demo-key")
        script_service = ScriptService(db=db, gemini_service=gemini_service)

        script = script_service.get_script_by_id(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        is_valid = script_service.validate_script_duration(script)

        return {
            "script_id": script_id,
            "is_valid": is_valid,
            "estimated_duration": script.estimated_duration,
            "minimum_required": 180,
            "validation_message": "Script meets minimum duration requirement" if is_valid else "Script too short - minimum 3 minutes required"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate script {script_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate script")