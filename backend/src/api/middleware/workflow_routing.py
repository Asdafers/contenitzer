from fastapi import Request, HTTPException
from typing import Dict, Any, Optional
import logging

from ...services.workflow_engine import WorkflowEngine
from ...services.workflow_mode_service import WorkflowModeService
from ...models.workflow import WorkflowModeEnum

logger = logging.getLogger(__name__)


class WorkflowRoutingMiddleware:
    """Middleware for handling workflow-based routing and access control"""

    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.workflow_service = WorkflowModeService()

    async def process_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Process incoming request and apply workflow-based routing logic"""

        # Extract workflow context from request
        workflow_context = self._extract_workflow_context(request)

        if not workflow_context:
            # No workflow context, proceed normally
            return None

        workflow_id = workflow_context.get("workflow_id")
        if not workflow_id:
            return None

        try:
            # Get workflow information
            workflow = self.workflow_service.get_workflow(workflow_id)
            if not workflow:
                logger.warning(f"Workflow not found: {workflow_id}")
                return None

            # Apply routing logic based on workflow mode
            routing_decision = self._apply_routing_logic(request, workflow_context, workflow)

            if routing_decision.get("block_request"):
                raise HTTPException(
                    status_code=routing_decision.get("status_code", 400),
                    detail=routing_decision.get("message", "Request blocked by workflow routing")
                )

            # Add workflow context to request state
            request.state.workflow_context = {
                "workflow_id": workflow_id,
                "mode": workflow.mode.value,
                "status": workflow.status.value,
                "skip_research": workflow.skip_research,
                "skip_generation": workflow.skip_generation,
                "routing_decision": routing_decision
            }

            return routing_decision

        except Exception as e:
            logger.error(f"Error in workflow routing middleware: {e}")
            # Don't block request on middleware errors
            return None

    def _extract_workflow_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """Extract workflow context from request"""

        # Check for workflow_id in query parameters
        workflow_id = request.query_params.get("workflow_id")

        if not workflow_id:
            # Check for workflow_id in path parameters
            if hasattr(request, "path_params"):
                workflow_id = request.path_params.get("workflow_id")

        if not workflow_id:
            # Check for workflow_id in form data (for uploads)
            if request.method == "POST" and "multipart/form-data" in request.headers.get("content-type", ""):
                # Note: In actual middleware, you'd need to parse form data carefully
                # This is a simplified version
                pass

        if workflow_id:
            return {
                "workflow_id": workflow_id,
                "request_path": str(request.url.path),
                "request_method": request.method
            }

        return None

    def _apply_routing_logic(self, request: Request, context: Dict[str, Any], workflow) -> Dict[str, Any]:
        """Apply workflow-specific routing logic"""

        path = context["request_path"]
        method = context["request_method"]
        mode = workflow.mode

        # Default routing decision
        routing_decision = {
            "block_request": False,
            "redirect_path": None,
            "add_headers": {},
            "workflow_mode": mode.value
        }

        # Apply mode-specific routing logic
        if mode == WorkflowModeEnum.UPLOAD:
            routing_decision.update(self._apply_upload_mode_routing(path, method, workflow))
        elif mode == WorkflowModeEnum.GENERATE:
            routing_decision.update(self._apply_generate_mode_routing(path, method, workflow))

        return routing_decision

    def _apply_upload_mode_routing(self, path: str, method: str, workflow) -> Dict[str, Any]:
        """Apply routing logic for upload mode workflows"""

        decisions = {}

        # Block access to research/generation endpoints for upload mode
        if "/research" in path or "/generate" in path:
            if method in ["POST", "PUT", "PATCH"]:
                decisions.update({
                    "block_request": True,
                    "status_code": 403,
                    "message": "Research and generation endpoints are not available in upload mode"
                })

        # Add upload-specific headers
        decisions["add_headers"] = {
            "X-Workflow-Mode": "UPLOAD",
            "X-Skip-Research": "true",
            "X-Skip-Generation": "true"
        }

        # Redirect to upload-specific endpoints if needed
        if path.startswith("/api/scripts/generate") and method == "GET":
            decisions["redirect_path"] = "/api/v1/scripts/upload"

        return decisions

    def _apply_generate_mode_routing(self, path: str, method: str, workflow) -> Dict[str, Any]:
        """Apply routing logic for generate mode workflows"""

        decisions = {}

        # Block direct script upload for generate mode (unless explicitly allowed)
        if "/scripts/upload" in path and method == "POST":
            decisions.update({
                "block_request": True,
                "status_code": 403,
                "message": "Direct script upload is not available in generate mode"
            })

        # Add generation-specific headers
        decisions["add_headers"] = {
            "X-Workflow-Mode": "GENERATE",
            "X-Skip-Research": "false",
            "X-Skip-Generation": "false"
        }

        return decisions

    def get_workflow_navigation(self, workflow_id: str) -> Dict[str, Any]:
        """Get navigation options based on workflow state"""
        try:
            progress = self.workflow_engine.get_workflow_progress(workflow_id)

            if not progress.get("success"):
                return {"error": "Failed to get workflow progress"}

            workflow_progress = progress["progress"]
            mode = workflow_progress.get("mode", "GENERATE")
            status = workflow_progress.get("status", "CREATED")

            # Generate navigation based on workflow state
            if mode == "UPLOAD":
                return self._get_upload_navigation(workflow_progress)
            else:
                return self._get_generate_navigation(workflow_progress)

        except Exception as e:
            logger.error(f"Error getting workflow navigation: {e}")
            return {"error": str(e)}

    def _get_upload_navigation(self, progress: Dict[str, Any]) -> Dict[str, Any]:
        """Get navigation for upload mode workflow"""

        status = progress.get("status")
        next_steps = progress.get("next_steps", [])

        navigation = {
            "mode": "UPLOAD",
            "current_step": self._determine_current_step(progress),
            "available_actions": [],
            "blocked_actions": ["youtube_research", "script_generation"],
            "progress_percentage": self._calculate_progress_percentage(progress)
        }

        # Add available actions based on status
        if status == "CREATED":
            navigation["available_actions"].extend(["select_mode", "upload_script"])
        elif status == "MODE_SELECTED":
            navigation["available_actions"].extend(["upload_script"])
        elif status == "SCRIPT_READY":
            navigation["available_actions"].extend(["content_optimization", "formatting"])
        elif status == "PROCESSING":
            navigation["available_actions"].extend(["view_progress"])

        return navigation

    def _get_generate_navigation(self, progress: Dict[str, Any]) -> Dict[str, Any]:
        """Get navigation for generate mode workflow"""

        status = progress.get("status")

        navigation = {
            "mode": "GENERATE",
            "current_step": self._determine_current_step(progress),
            "available_actions": [],
            "blocked_actions": ["upload_script"],
            "progress_percentage": self._calculate_progress_percentage(progress)
        }

        # Add available actions based on status
        if status == "CREATED":
            navigation["available_actions"].extend(["select_mode"])
        elif status == "MODE_SELECTED":
            navigation["available_actions"].extend(["youtube_research"])
        elif status == "SCRIPT_READY":
            navigation["available_actions"].extend(["content_optimization", "formatting"])

        return navigation

    def _determine_current_step(self, progress: Dict[str, Any]) -> str:
        """Determine current workflow step"""
        status = progress.get("status", "CREATED")
        mode = progress.get("mode", "GENERATE")

        if status == "CREATED":
            return "mode_selection"
        elif status == "MODE_SELECTED":
            return "script_upload" if mode == "UPLOAD" else "youtube_research"
        elif status == "SCRIPT_READY":
            return "content_processing"
        elif status == "PROCESSING":
            return "content_optimization"
        elif status == "COMPLETED":
            return "completed"
        else:
            return "unknown"

    def _calculate_progress_percentage(self, progress: Dict[str, Any]) -> int:
        """Calculate workflow progress percentage"""
        status = progress.get("status", "CREATED")

        status_percentages = {
            "CREATED": 0,
            "MODE_SELECTED": 20,
            "SCRIPT_READY": 40,
            "PROCESSING": 70,
            "COMPLETED": 100,
            "FAILED": 0
        }

        return status_percentages.get(status, 0)