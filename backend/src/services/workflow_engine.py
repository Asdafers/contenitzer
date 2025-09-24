from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging
import uuid

from ..models.workflow import Workflow, WorkflowStatusEnum, WorkflowModeEnum
from ..models.uploaded_script import UploadedScript
from .workflow_mode_service import WorkflowModeService
from .script_upload_service import ScriptUploadService
from ..lib.database import get_db_session

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Engine for orchestrating content creation workflows with script upload integration"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.workflow_service = WorkflowModeService(db_session)
        self.script_service = ScriptUploadService(db_session)

    def _get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        return next(get_db_session())

    def process_workflow_step(self, workflow_id: str, step: str) -> Dict[str, Any]:
        """Process a workflow step based on workflow mode and current state"""
        try:
            workflow = self.workflow_service.get_workflow(workflow_id)
            if not workflow:
                return {"success": False, "error": "Workflow not found"}

            logger.info(f"Processing step '{step}' for workflow {workflow_id} (mode: {workflow.mode.value})")

            # Route based on workflow mode and step
            if workflow.mode == WorkflowModeEnum.UPLOAD:
                return self._process_upload_workflow_step(workflow, step)
            elif workflow.mode == WorkflowModeEnum.GENERATE:
                return self._process_generate_workflow_step(workflow, step)
            else:
                return {"success": False, "error": "Unknown workflow mode"}

        except Exception as e:
            logger.error(f"Error processing workflow step {step} for {workflow_id}: {e}")
            return {"success": False, "error": str(e)}

    def _process_upload_workflow_step(self, workflow: Workflow, step: str) -> Dict[str, Any]:
        """Process workflow steps for script upload mode"""

        if step == "mode_selection":
            # Mode already selected, move to script upload
            return {
                "success": True,
                "next_step": "script_upload",
                "message": "Upload mode selected, ready for script upload"
            }

        elif step == "script_upload":
            # Check if script is already uploaded
            if workflow.uploaded_script_id:
                script = self.script_service.get_script(str(workflow.uploaded_script_id))
                if script and script.is_valid():
                    # Script ready, move to processing
                    self.workflow_service.update_workflow_status(
                        str(workflow.id),
                        WorkflowStatusEnum.SCRIPT_READY
                    )
                    return {
                        "success": True,
                        "next_step": "content_processing",
                        "message": "Script uploaded and validated successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Uploaded script is not valid",
                        "next_step": "script_upload"
                    }
            else:
                return {
                    "success": True,
                    "message": "Waiting for script upload",
                    "current_step": "script_upload"
                }

        elif step == "content_processing":
            # Skip research and generation, proceed to optimization
            return {
                "success": True,
                "next_step": "content_optimization",
                "message": "Ready for content optimization",
                "skipped_steps": ["youtube_research", "script_generation"]
            }

        else:
            # Default processing for other steps
            return self._process_standard_step(workflow, step)

    def _process_generate_workflow_step(self, workflow: Workflow, step: str) -> Dict[str, Any]:
        """Process workflow steps for script generation mode"""

        if step == "mode_selection":
            return {
                "success": True,
                "next_step": "youtube_research",
                "message": "Generate mode selected, starting research"
            }

        elif step == "youtube_research":
            # Placeholder for YouTube research integration
            return {
                "success": True,
                "next_step": "script_generation",
                "message": "Research completed, ready for script generation",
                "data": {"research_completed": True}
            }

        elif step == "script_generation":
            # Placeholder for AI script generation
            return {
                "success": True,
                "next_step": "content_processing",
                "message": "Script generated successfully",
                "data": {"script_generated": True}
            }

        else:
            # Default processing for other steps
            return self._process_standard_step(workflow, step)

    def _process_standard_step(self, workflow: Workflow, step: str) -> Dict[str, Any]:
        """Process standard workflow steps that apply to both modes"""

        if step == "content_optimization":
            return {
                "success": True,
                "next_step": "formatting",
                "message": "Content optimization completed"
            }

        elif step == "formatting":
            return {
                "success": True,
                "next_step": "publishing",
                "message": "Content formatting completed"
            }

        elif step == "publishing":
            # Mark workflow as completed
            self.workflow_service.update_workflow_status(
                str(workflow.id),
                WorkflowStatusEnum.COMPLETED
            )
            return {
                "success": True,
                "message": "Workflow completed successfully",
                "completed": True
            }

        else:
            return {
                "success": False,
                "error": f"Unknown workflow step: {step}"
            }

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow progress information"""
        try:
            # Get workflow progress from workflow service
            progress = self.workflow_service.get_workflow_progress(workflow_id)
            if not progress:
                return {"success": False, "error": "Workflow not found"}

            # Add script information if available
            if progress.get("uploaded_script_id"):
                script = self.script_service.get_script(progress["uploaded_script_id"])
                if script:
                    progress["script_info"] = {
                        "content_length": script.content_length,
                        "file_name": script.file_name,
                        "validation_status": script.validation_status.value,
                        "upload_timestamp": script.upload_timestamp.isoformat()
                    }

            # Add step completion status
            progress["step_completion"] = self._get_step_completion_status(progress)

            return {"success": True, "progress": progress}

        except Exception as e:
            logger.error(f"Error getting workflow progress for {workflow_id}: {e}")
            return {"success": False, "error": str(e)}

    def _get_step_completion_status(self, progress: Dict[str, Any]) -> Dict[str, bool]:
        """Get completion status for each workflow step"""
        mode = progress.get("mode", "GENERATE")
        status = progress.get("status", "CREATED")

        if mode == "UPLOAD":
            return {
                "mode_selection": status != "CREATED",
                "script_upload": progress.get("uploaded_script_id") is not None,
                "script_validation": status in ["SCRIPT_READY", "PROCESSING", "COMPLETED"],
                "content_processing": status in ["PROCESSING", "COMPLETED"],
                "content_optimization": status == "COMPLETED",
                "formatting": status == "COMPLETED",
                "publishing": status == "COMPLETED"
            }
        else:  # GENERATE mode
            return {
                "mode_selection": status != "CREATED",
                "youtube_research": status in ["SCRIPT_READY", "PROCESSING", "COMPLETED"],
                "script_generation": status in ["SCRIPT_READY", "PROCESSING", "COMPLETED"],
                "content_processing": status in ["PROCESSING", "COMPLETED"],
                "content_optimization": status == "COMPLETED",
                "formatting": status == "COMPLETED",
                "publishing": status == "COMPLETED"
            }

    def handle_script_upload_completion(self, workflow_id: str, script_id: str) -> Dict[str, Any]:
        """Handle completion of script upload for a workflow"""
        try:
            # Associate script with workflow
            success, message = self.workflow_service.associate_script_with_workflow(
                workflow_id, script_id
            )

            if not success:
                return {"success": False, "error": message}

            # Update workflow status
            self.workflow_service.update_workflow_status(
                workflow_id,
                WorkflowStatusEnum.SCRIPT_READY
            )

            logger.info(f"Script upload completed for workflow {workflow_id}, script {script_id}")

            return {
                "success": True,
                "message": "Script upload completed successfully",
                "next_step": "content_processing"
            }

        except Exception as e:
            logger.error(f"Error handling script upload completion: {e}")
            return {"success": False, "error": str(e)}

    def get_available_workflows(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available workflows for a user"""
        try:
            session = self._get_session()

            query = session.query(Workflow)
            if user_id:
                query = query.filter(Workflow.user_id == uuid.UUID(user_id))

            workflows = query.order_by(Workflow.created_at.desc()).limit(50).all()

            return [
                {
                    "workflow_id": str(workflow.id),
                    "title": workflow.title,
                    "description": workflow.description,
                    "mode": workflow.mode.value,
                    "status": workflow.status.value,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
                }
                for workflow in workflows
            ]

        except Exception as e:
            logger.error(f"Error getting available workflows: {e}")
            return []