from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from ..services.workflow_mode_service import WorkflowModeService
from ..models.workflow import WorkflowModeEnum
from ..lib.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class WorkflowCreateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class WorkflowCreateResponse(BaseModel):
    workflow_id: str
    status: str
    created_at: str


class WorkflowModeRequest(BaseModel):
    mode: str  # GENERATE or UPLOAD


class WorkflowModeResponse(BaseModel):
    workflow_id: str
    mode: str
    updated_at: str


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    mode: str
    status: str
    script_source: Optional[str] = None
    skip_research: bool
    skip_generation: bool
    uploaded_script_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str


def get_workflow_service(db: Session = Depends(get_db)) -> WorkflowModeService:
    """Dependency to get WorkflowModeService"""
    return WorkflowModeService(db_session=db)


@router.post("/api/v1/workflows", response_model=WorkflowCreateResponse, status_code=201)
async def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowModeService = Depends(get_workflow_service)
):
    """Create a new workflow"""
    try:
        success, result = workflow_service.create_workflow(
            title=request.title,
            description=request.description
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "workflow_creation_failed",
                    "message": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        workflow = result
        return WorkflowCreateResponse(
            workflow_id=str(workflow.id),
            status=workflow.status.value,
            created_at=workflow.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred during workflow creation",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/api/v1/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow(
    workflow_id: str,
    workflow_service: WorkflowModeService = Depends(get_workflow_service)
):
    """Get workflow status and details"""
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_workflow_id",
                    "message": "Invalid workflow ID format",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        workflow = workflow_service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "workflow_not_found",
                    "message": "Workflow not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return WorkflowStatusResponse(
            workflow_id=str(workflow.id),
            mode=workflow.mode.value,
            status=workflow.status.value,
            script_source=workflow.script_source.value if workflow.script_source else None,
            skip_research=workflow.skip_research,
            skip_generation=workflow.skip_generation,
            uploaded_script_id=str(workflow.uploaded_script_id) if workflow.uploaded_script_id else None,
            created_at=workflow.created_at.isoformat(),
            updated_at=workflow.updated_at.isoformat() if workflow.updated_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Error retrieving workflow",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.put("/api/v1/workflows/{workflow_id}/mode", response_model=WorkflowModeResponse)
async def set_workflow_mode(
    workflow_id: str,
    request: WorkflowModeRequest,
    workflow_service: WorkflowModeService = Depends(get_workflow_service)
):
    """Set workflow mode (GENERATE or UPLOAD)"""
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(workflow_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_workflow_id",
                    "message": "Invalid workflow ID format",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Validate mode
        try:
            mode = WorkflowModeEnum(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_mode",
                    "message": f"Invalid mode: {request.mode}. Must be 'GENERATE' or 'UPLOAD'",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Check if request body is provided
        if not request.mode:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "missing_mode",
                    "message": "Mode field is required",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        success, result = workflow_service.set_workflow_mode(
            workflow_id=workflow_id,
            mode=mode
        )

        if not success:
            error_message = str(result)

            if "not found" in error_message.lower():
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "workflow_not_found",
                        "message": error_message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "mode_setting_failed",
                        "message": error_message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

        workflow = result
        return WorkflowModeResponse(
            workflow_id=str(workflow.id),
            mode=workflow.mode.value,
            updated_at=workflow.updated_at.isoformat() if workflow.updated_at else datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting workflow mode for {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Error setting workflow mode",
                "timestamp": datetime.utcnow().isoformat()
            }
        )