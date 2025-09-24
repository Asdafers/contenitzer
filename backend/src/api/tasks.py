"""
Task Queue API endpoint implementations.
Handles task submission, status monitoring, and queue management.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging

from ..services.task_queue_service import (
    TaskQueueService,
    get_task_queue_service,
    TaskStatus,
    TaskType,
    TaskPriority
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SubmitTaskRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for task association")
    input_data: Dict[str, Any] = Field(..., description="Task input parameters")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority level")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional task metadata")


class SubmitTaskResponse(BaseModel):
    task_id: str
    message: str = "Task submitted successfully"


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    priority: str
    session_id: str
    input_data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    progress: int
    estimated_duration: Optional[str] = None
    worker_id: Optional[str] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


# Dependencies
def get_task_queue_service_dependency() -> TaskQueueService:
    return get_task_queue_service()


# Task Management Endpoints
@router.get("/api/tasks", response_model=TaskListResponse)
async def list_tasks(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    task_service: TaskQueueService = Depends(get_task_queue_service_dependency)
):
    """
    List tasks with optional filtering
    """
    try:
        # Validate optional parameters
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        task_type_enum = None
        if task_type:
            try:
                task_type_enum = TaskType(task_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid task_type: {task_type}")

        # Validate session_id format if provided
        if session_id:
            try:
                uuid.UUID(session_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")

        tasks = task_service.list_tasks(
            session_id=session_id,
            status=task_status,
            task_type=task_type_enum,
            limit=limit
        )

        task_responses = [TaskResponse(**task) for task in tasks]

        logger.debug(f"Listed {len(task_responses)} tasks")

        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskQueueService = Depends(get_task_queue_service_dependency)
):
    """
    Get task by ID
    """
    try:
        # Validate task_id format
        try:
            uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")

        task_data = task_service.get_task(task_id)

        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")

        logger.debug(f"Retrieved task {task_id}")

        return TaskResponse(**task_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")


@router.delete("/api/tasks/{task_id}", status_code=204)
async def cancel_task(
    task_id: str,
    task_service: TaskQueueService = Depends(get_task_queue_service_dependency)
):
    """
    Cancel a pending or running task
    """
    try:
        # Validate task_id format
        try:
            uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")

        # Check if task exists
        task_data = task_service.get_task(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")

        success = task_service.cancel_task(task_id)

        if not success:
            # Check current status to provide better error message
            current_status = task_data.get("status")
            if current_status in ["completed", "failed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel task in status: {current_status}"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to cancel task")

        logger.info(f"Cancelled task {task_id}")

        # No content returned for 204

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.post("/api/tasks/{task_id}/retry", status_code=200)
async def retry_task(
    task_id: str,
    task_service: TaskQueueService = Depends(get_task_queue_service_dependency)
):
    """
    Retry a failed task
    """
    try:
        # Validate task_id format
        try:
            uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task ID format")

        # Check if task exists
        task_data = task_service.get_task(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")

        success = task_service.retry_task(task_id)

        if not success:
            # Check current status and retry count to provide better error message
            current_status = task_data.get("status")
            retry_count = task_data.get("retry_count", 0)
            max_retries = task_data.get("max_retries", 3)

            if current_status != "failed":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot retry task in status: {current_status}"
                )
            elif retry_count >= max_retries:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task has exceeded maximum retries ({max_retries})"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to retry task")

        logger.info(f"Retrying task {task_id}")

        return {"message": "Task retry initiated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {str(e)}")


@router.post("/api/tasks/submit/{task_type}", response_model=SubmitTaskResponse, status_code=201)
async def submit_task(
    task_type: str,
    request: SubmitTaskRequest,
    task_service: TaskQueueService = Depends(get_task_queue_service_dependency)
):
    """
    Submit a new task to the queue
    """
    try:
        # Validate task_type
        try:
            task_type_enum = TaskType(task_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid task_type: {task_type}")

        # Validate session_id format
        try:
            uuid.UUID(request.session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        task_id = task_service.submit_task(
            task_type=task_type_enum,
            input_data=request.input_data,
            session_id=request.session_id,
            priority=request.priority,
            metadata=request.metadata
        )

        # Actually trigger the Celery task
        from src.tasks.trending_tasks import analyze_trending_content
        from src.tasks.script_tasks import generate_script_from_theme

        if task_type_enum == TaskType.TRENDING_ANALYSIS:
            # Trigger the Celery task with the same task_id
            analyze_trending_content.apply_async(
                args=[
                    request.session_id,
                    "your-youtube-api-key",  # TODO: Get from config
                    "weekly",
                    50
                ],
                task_id=task_id
            )
        elif task_type_enum == TaskType.SCRIPT_GENERATION:
            # Handle script generation task
            generate_script_from_theme.apply_async(
                args=[
                    request.session_id,
                    request.input_data.get("theme", {}),
                    request.input_data.get("target_duration", 300)
                ],
                task_id=task_id
            )

        logger.info(f"Submitted task {task_id} of type {task_type} for session {request.session_id}")

        return SubmitTaskResponse(
            task_id=task_id,
            message="Task submitted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=f"Task submission failed: {str(e)}")