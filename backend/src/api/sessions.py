from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import logging

from ..services.session_service import SessionService, get_session_service
from ..services.ui_state_service import UIStateService, get_ui_state_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CreateSessionRequest(BaseModel):
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CreateSessionResponse(BaseModel):
    session_id: str
    message: str = "Session created successfully"


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: str
    preferences: Dict[str, Any]
    workflow_state: Dict[str, Any]
    active: bool


class UpdateSessionRequest(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    workflow_state: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class WorkflowStateResponse(BaseModel):
    workflow_state: Dict[str, Any]


class UpdateWorkflowStateRequest(BaseModel):
    workflow_state: Dict[str, Any]


class UIStateResponse(BaseModel):
    session_id: str
    component_name: str
    state_data: Dict[str, Any]
    form_data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class UpdateUIStateRequest(BaseModel):
    ui_state: Optional[Dict[str, Any]] = None
    form_data: Optional[Dict[str, Any]] = None


# Dependencies
def get_session_service_dependency() -> SessionService:
    return get_session_service()


def get_ui_state_service_dependency() -> UIStateService:
    return get_ui_state_service()


# Session Management Endpoints
@router.post("/api/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service_dependency)
):
    """
    Create a new user session with optional preferences
    """
    try:
        session_id = session_service.create_session(request.preferences)

        logger.info(f"Created session {session_id}")

        return CreateSessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service_dependency)
):
    """
    Retrieve session data by ID
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        session_data = session_service.get_session(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.debug(f"Retrieved session {session_id}")

        return SessionResponse(**session_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")


@router.put("/api/sessions/{session_id}", status_code=200)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    session_service: SessionService = Depends(get_session_service_dependency)
):
    """
    Update session preferences and settings
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Check if session exists
        existing_session = session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Build updates dictionary
        updates = {}
        if request.preferences is not None:
            updates["preferences"] = request.preferences
        if request.workflow_state is not None:
            updates["workflow_state"] = request.workflow_state
        if request.active is not None:
            updates["active"] = request.active

        success = session_service.update_session(session_id, updates)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session")

        logger.info(f"Updated session {session_id}")

        return {"message": "Session updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.delete("/api/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service_dependency),
    ui_state_service: UIStateService = Depends(get_ui_state_service_dependency)
):
    """
    Delete session and all associated data
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Check if session exists
        existing_session = session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete UI states first
        ui_state_service.clear_session_ui_states(session_id)

        # Delete session
        success = session_service.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete session")

        logger.info(f"Deleted session {session_id}")

        # No content returned for 204

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


# Workflow State Endpoints
@router.get("/api/sessions/{session_id}/workflow-state", response_model=WorkflowStateResponse)
async def get_workflow_state(
    session_id: str,
    session_service: SessionService = Depends(get_session_service_dependency)
):
    """
    Get workflow state for session
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        workflow_state = session_service.get_workflow_state(session_id)

        if workflow_state is None:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.debug(f"Retrieved workflow state for session {session_id}")

        return WorkflowStateResponse(workflow_state=workflow_state)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow state for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow state: {str(e)}")


@router.put("/api/sessions/{session_id}/workflow-state", status_code=200)
async def update_workflow_state(
    session_id: str,
    request: UpdateWorkflowStateRequest,
    session_service: SessionService = Depends(get_session_service_dependency)
):
    """
    Update workflow state for session
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Check if session exists
        existing_session = session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")

        success = session_service.update_workflow_state(session_id, request.workflow_state)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update workflow state")

        logger.info(f"Updated workflow state for session {session_id}")

        return {"message": "Workflow state updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow state for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow state: {str(e)}")


# UI State Endpoints
@router.get("/api/sessions/{session_id}/ui-state/{component_name}", response_model=UIStateResponse)
async def get_ui_state(
    session_id: str,
    component_name: str,
    ui_state_service: UIStateService = Depends(get_ui_state_service_dependency)
):
    """
    Get UI state for a specific component in session
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        ui_state = ui_state_service.get_component_state(session_id, component_name)

        if not ui_state:
            raise HTTPException(status_code=404, detail="UI state not found")

        logger.debug(f"Retrieved UI state for component {component_name} in session {session_id}")

        return UIStateResponse(**ui_state)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get UI state for component {component_name} in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve UI state: {str(e)}")


@router.put("/api/sessions/{session_id}/ui-state/{component_name}", status_code=200)
async def update_ui_state(
    session_id: str,
    component_name: str,
    request: UpdateUIStateRequest,
    ui_state_service: UIStateService = Depends(get_ui_state_service_dependency)
):
    """
    Update UI state for a specific component in session
    """
    try:
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Check if UI state exists, if not create it
        existing_state = ui_state_service.get_component_state(session_id, component_name)

        if existing_state:
            # Update existing state
            success = ui_state_service.update_component_state(
                session_id,
                component_name,
                state_updates=request.ui_state,
                form_updates=request.form_data
            )
        else:
            # Create new state
            success = ui_state_service.save_component_state(
                session_id,
                component_name,
                state_data=request.ui_state or {},
                form_data=request.form_data or {}
            )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update UI state")

        logger.info(f"Updated UI state for component {component_name} in session {session_id}")

        return {"message": "UI state updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update UI state for component {component_name} in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update UI state: {str(e)}")