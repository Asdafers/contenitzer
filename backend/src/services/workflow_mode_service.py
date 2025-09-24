from typing import Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging
from datetime import datetime

from ..models.workflow import Workflow, WorkflowModeEnum, WorkflowStatusEnum
from ..models.uploaded_script import UploadedScript
from ..lib.database import SessionLocal

logger = logging.getLogger(__name__)


class WorkflowModeService:
    """Service for managing workflow modes and state transitions"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        # Create a new session for standalone use
        return SessionLocal()

    def create_workflow(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Union[Workflow, str]]:
        """Create a new workflow"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)  # We created the session

            workflow = Workflow(
                title=title,
                description=description,
                user_id=uuid.UUID(user_id) if user_id else None,
                status=WorkflowStatusEnum.CREATED
            )

            session.add(workflow)
            session.commit()

            logger.info(f"Created new workflow: {workflow.id}")
            return True, workflow

        except ValueError as e:
            logger.error(f"Invalid UUID format for user_id {user_id}: {e}")
            if session:
                session.rollback()
            return False, f"Invalid user ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error creating workflow: {e}")
            if session:
                session.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error creating workflow: {e}")
            if session:
                session.rollback()
            return False, f"Workflow creation failed: {str(e)}"
        finally:
            if created_session and session:
                session.close()

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)

            workflow = session.query(Workflow).filter(
                Workflow.id == uuid.UUID(workflow_id)
            ).first()

            if workflow:
                logger.info(f"Retrieved workflow: {workflow_id}")
            else:
                logger.warning(f"Workflow not found: {workflow_id}")

            return workflow

        except ValueError as e:
            logger.error(f"Invalid UUID format for workflow_id {workflow_id}: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving workflow {workflow_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving workflow {workflow_id}: {e}")
            return None
        finally:
            if created_session and session:
                session.close()

    def set_workflow_mode(
        self,
        workflow_id: str,
        mode: WorkflowModeEnum,
        uploaded_script_id: Optional[str] = None
    ) -> Tuple[bool, Union[Workflow, str]]:
        """Set workflow mode and configure accordingly"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)

            workflow = session.query(Workflow).filter(
                Workflow.id == uuid.UUID(workflow_id)
            ).first()

            if not workflow:
                logger.warning(f"Workflow not found: {workflow_id}")
                return False, "Workflow not found"

            # Validate mode transition
            if not self._can_change_mode(workflow, mode):
                return False, f"Cannot change mode from {workflow.mode.value} to {mode.value}"

            # Configure workflow based on mode
            if mode == WorkflowModeEnum.UPLOAD:
                if uploaded_script_id:
                    # Verify uploaded script exists
                    uploaded_script = session.query(UploadedScript).filter(
                        UploadedScript.id == uuid.UUID(uploaded_script_id)
                    ).first()

                    if not uploaded_script:
                        return False, "Uploaded script not found"

                    workflow.set_upload_mode(uuid.UUID(uploaded_script_id))
                else:
                    # Set upload mode without script (script will be uploaded later)
                    workflow.mode = WorkflowModeEnum.UPLOAD
                    workflow.skip_research = True
                    workflow.skip_generation = True
                    workflow.status = WorkflowStatusEnum.MODE_SELECTED

            elif mode == WorkflowModeEnum.GENERATE:
                workflow.set_generate_mode()

            workflow.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Set workflow {workflow_id} mode to {mode.value}")
            return True, workflow

        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            if session:
                session.rollback()
            return False, f"Invalid ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error setting workflow mode: {e}")
            if session:
                session.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error setting workflow mode: {e}")
            if session:
                session.rollback()
            return False, f"Mode setting failed: {str(e)}"
        finally:
            if created_session and session:
                session.close()

    def _can_change_mode(self, workflow: Workflow, new_mode: WorkflowModeEnum) -> bool:
        """Check if workflow mode can be changed"""
        # Allow mode changes for created workflows
        if workflow.status == WorkflowStatusEnum.CREATED:
            return True

        # Allow changing from mode selected state
        if workflow.status == WorkflowStatusEnum.MODE_SELECTED:
            return True

        # Don't allow mode changes once processing has started
        if workflow.status in [WorkflowStatusEnum.PROCESSING, WorkflowStatusEnum.COMPLETED]:
            return False

        return True

    def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatusEnum
    ) -> Tuple[bool, str]:
        """Update workflow status"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)

            workflow = session.query(Workflow).filter(
                Workflow.id == uuid.UUID(workflow_id)
            ).first()

            if not workflow:
                return False, "Workflow not found"

            # Validate status transition
            if not self._can_transition_to_status(workflow, status):
                return False, f"Invalid status transition from {workflow.status.value} to {status.value}"

            workflow.status = status
            workflow.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Updated workflow {workflow_id} status to {status.value}")
            return True, f"Status updated to {status.value}"

        except ValueError as e:
            logger.error(f"Invalid UUID format for workflow_id {workflow_id}: {e}")
            if session:
                session.rollback()
            return False, f"Invalid workflow ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error updating workflow status: {e}")
            if session:
                session.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error updating workflow status: {e}")
            if session:
                session.rollback()
            return False, f"Status update failed: {str(e)}"
        finally:
            if created_session and session:
                session.close()

    def _can_transition_to_status(self, workflow: Workflow, new_status: WorkflowStatusEnum) -> bool:
        """Check if workflow can transition to new status"""
        current = workflow.status

        # Define valid transitions
        valid_transitions = {
            WorkflowStatusEnum.CREATED: [WorkflowStatusEnum.MODE_SELECTED, WorkflowStatusEnum.FAILED],
            WorkflowStatusEnum.MODE_SELECTED: [WorkflowStatusEnum.SCRIPT_READY, WorkflowStatusEnum.FAILED],
            WorkflowStatusEnum.SCRIPT_READY: [WorkflowStatusEnum.PROCESSING, WorkflowStatusEnum.FAILED],
            WorkflowStatusEnum.PROCESSING: [WorkflowStatusEnum.COMPLETED, WorkflowStatusEnum.FAILED],
            WorkflowStatusEnum.COMPLETED: [],  # Terminal state
            WorkflowStatusEnum.FAILED: [WorkflowStatusEnum.CREATED]  # Can restart
        }

        return new_status in valid_transitions.get(current, [])

    def get_workflow_progress(self, workflow_id: str) -> Optional[dict]:
        """Get workflow progress information"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        next_steps = workflow.get_next_steps()
        can_proceed = workflow.can_proceed_to_processing()

        return {
            "workflow_id": str(workflow.id),
            "mode": workflow.mode.value,
            "status": workflow.status.value,
            "script_source": workflow.script_source.value if workflow.script_source else None,
            "skip_research": workflow.skip_research,
            "skip_generation": workflow.skip_generation,
            "can_proceed": can_proceed,
            "next_steps": next_steps,
            "uploaded_script_id": str(workflow.uploaded_script_id) if workflow.uploaded_script_id else None,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        }

    def associate_script_with_workflow(
        self,
        workflow_id: str,
        script_id: str
    ) -> Tuple[bool, str]:
        """Associate an uploaded script with a workflow"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)

            workflow = session.query(Workflow).filter(
                Workflow.id == uuid.UUID(workflow_id)
            ).first()

            if not workflow:
                return False, "Workflow not found"

            # Verify script exists
            script = session.query(UploadedScript).filter(
                UploadedScript.id == uuid.UUID(script_id)
            ).first()

            if not script:
                return False, "Script not found"

            # Associate script with workflow
            workflow.uploaded_script_id = uuid.UUID(script_id)
            workflow.script_source = "UPLOADED"

            # Update status if appropriate
            if workflow.status == WorkflowStatusEnum.MODE_SELECTED:
                workflow.status = WorkflowStatusEnum.SCRIPT_READY

            workflow.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Associated script {script_id} with workflow {workflow_id}")
            return True, "Script associated successfully"

        except ValueError as e:
            logger.error(f"Invalid UUID format: {e}")
            if session:
                session.rollback()
            return False, f"Invalid ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error associating script: {e}")
            if session:
                session.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error associating script: {e}")
            if session:
                session.rollback()
            return False, f"Association failed: {str(e)}"
        finally:
            if created_session and session:
                session.close()