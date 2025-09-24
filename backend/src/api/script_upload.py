from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile, Request
from pydantic import BaseModel
from typing import Optional, Union
import logging
from datetime import datetime

from ..services.script_upload_service import ScriptUploadService
from ..services.script_validation_service import ScriptValidationService
from ..lib.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class UploadResponse(BaseModel):
    script_id: str
    status: str  # PENDING, VALID, INVALID
    message: str
    file_name: Optional[str] = None
    content_length: int
    upload_timestamp: str


class ScriptResponse(BaseModel):
    script_id: str
    content: str
    file_name: Optional[str] = None
    validation_status: str
    upload_timestamp: str
    workflow_id: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: str


class ValidationErrorResponse(BaseModel):
    error: str
    message: str
    details: list[dict]
    timestamp: str


def get_script_upload_service(db: Session = Depends(get_db)) -> ScriptUploadService:
    """Dependency to get ScriptUploadService"""
    return ScriptUploadService(db_session=db)


def get_script_validation_service(db: Session = Depends(get_db)) -> ScriptValidationService:
    """Dependency to get ScriptValidationService"""
    return ScriptValidationService(db_session=db)


@router.post("/api/v1/scripts/upload", response_model=UploadResponse, status_code=201)
async def upload_script(
    workflow_id: str = Form(...),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    upload_service: ScriptUploadService = Depends(get_script_upload_service)
):
    """
    Upload script content via file or direct text input
    Either 'content' or 'file' must be provided, but not both
    """
    try:
        # Validate input parameters
        if not content and not file:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "missing_content",
                    "message": "Either 'content' or 'file' must be provided",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        if content and file:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "conflicting_input",
                    "message": "Provide either 'content' or 'file', not both",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Process file upload
        if file:
            # Validate file type
            if file.content_type not in ['text/plain', 'text/markdown', 'application/octet-stream']:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_file_type",
                        "message": f"Invalid file type: {file.content_type}. Only text files are supported.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            # Read file content
            file_content = await file.read()

            # Check file size (50KB limit)
            if len(file_content) > 51200:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": "file_too_large",
                        "message": "File size exceeds 50KB limit",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "encoding_error",
                        "message": "File must be UTF-8 encoded text",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            file_name = file.filename
            content_type = 'text/plain'
        else:
            # Process direct text content
            file_name = None
            content_type = 'text/plain'

        # Check content size limit
        if len(content) > 51200:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "content_too_large",
                    "message": "Content exceeds 50KB limit",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Upload script
        success, result = upload_service.upload_script(
            content=content,
            workflow_id=workflow_id,
            file_name=file_name,
            content_type=content_type
        )

        if not success:
            # Determine appropriate status code based on error
            if "validation failed" in str(result).lower():
                status_code = 422
                error_type = "validation_error"
            elif "invalid" in str(result).lower() and "uuid" in str(result).lower():
                status_code = 400
                error_type = "invalid_workflow_id"
            else:
                status_code = 500
                error_type = "upload_error"

            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": error_type,
                    "message": str(result),
                    "details": [{"field": "content", "issue": str(result)}],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        # Success - return upload response
        uploaded_script = result
        return UploadResponse(
            script_id=str(uploaded_script.id),
            status=uploaded_script.validation_status.value,
            message="Script uploaded successfully",
            file_name=uploaded_script.file_name,
            content_length=uploaded_script.content_length,
            upload_timestamp=uploaded_script.upload_timestamp.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in script upload: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred during upload",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/api/v1/scripts/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str,
    upload_service: ScriptUploadService = Depends(get_script_upload_service)
):
    """Get uploaded script by ID"""
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(script_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_script_id",
                    "message": "Invalid script ID format",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        script = upload_service.get_script(script_id)

        if not script:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "script_not_found",
                    "message": "Script not found",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return ScriptResponse(
            script_id=str(script.id),
            content=script.content,
            file_name=script.file_name,
            validation_status=script.validation_status.value,
            upload_timestamp=script.upload_timestamp.isoformat(),
            workflow_id=str(script.workflow_id)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving script {script_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Error retrieving script",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.delete("/api/v1/scripts/{script_id}", status_code=204)
async def delete_script(
    script_id: str,
    upload_service: ScriptUploadService = Depends(get_script_upload_service)
):
    """Delete uploaded script by ID"""
    try:
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(script_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_script_id",
                    "message": "Invalid script ID format",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        success, message = upload_service.delete_script(script_id)

        if not success:
            if "not found" in message.lower():
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "script_not_found",
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "deletion_error",
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

        # Return 204 No Content (no response body)
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting script {script_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Error deleting script",
                "timestamp": datetime.utcnow().isoformat()
            }
        )