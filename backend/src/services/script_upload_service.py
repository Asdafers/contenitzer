from typing import Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging
from datetime import datetime

from ..models.uploaded_script import UploadedScript, ValidationStatusEnum
from ..models.workflow import Workflow
from ..lib.database import SessionLocal

logger = logging.getLogger(__name__)


class ScriptUploadService:
    """Service for handling script uploads and management"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def _get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        # Create a new session for standalone use
        return SessionLocal()

    def upload_script(
        self,
        content: str,
        workflow_id: str,
        file_name: Optional[str] = None,
        content_type: str = "text/plain"
    ) -> Tuple[bool, Union[UploadedScript, str]]:
        """Upload a script and return success status and result"""
        session = None
        created_session = False

        try:
            session = self._get_session()
            created_session = (self.db_session is None)  # We created the session

            # Create uploaded script instance
            uploaded_script = UploadedScript(
                workflow_id=uuid.UUID(workflow_id),
                content=content,
                file_name=file_name,
                content_type=content_type,
                validation_status=ValidationStatusEnum.PENDING
            )

            # Validate content
            is_valid, errors = uploaded_script.validate_content()

            if not is_valid:
                uploaded_script.validation_status = ValidationStatusEnum.INVALID
                logger.warning(f"Script validation failed for workflow {workflow_id}: {errors}")
                return False, f"Validation failed: {'; '.join(errors)}"
            else:
                uploaded_script.validation_status = ValidationStatusEnum.VALID

            # Save to database
            session.add(uploaded_script)
            session.commit()

            logger.info(f"Script uploaded successfully: {uploaded_script.id} for workflow {workflow_id}")
            return True, uploaded_script

        except ValueError as e:
            logger.error(f"Invalid UUID format for workflow_id {workflow_id}: {e}")
            if session:
                session.rollback()
            return False, f"Invalid workflow ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error during script upload: {e}")
            if session:
                session.rollback()
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during script upload: {e}")
            if session:
                session.rollback()
            return False, f"Upload failed: {str(e)}"
        finally:
            if created_session and session:
                session.close()

    def get_script(self, script_id: str) -> Optional[UploadedScript]:
        """Retrieve uploaded script by ID"""
        try:
            session = self._get_session()

            script = session.query(UploadedScript).filter(
                UploadedScript.id == uuid.UUID(script_id)
            ).first()

            if script:
                logger.info(f"Retrieved script: {script_id}")
            else:
                logger.warning(f"Script not found: {script_id}")

            return script

        except ValueError as e:
            logger.error(f"Invalid UUID format for script_id {script_id}: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving script {script_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving script {script_id}: {e}")
            return None

    def delete_script(self, script_id: str) -> Tuple[bool, str]:
        """Delete uploaded script by ID"""
        try:
            session = self._get_session()

            script = session.query(UploadedScript).filter(
                UploadedScript.id == uuid.UUID(script_id)
            ).first()

            if not script:
                logger.warning(f"Script not found for deletion: {script_id}")
                return False, "Script not found"

            # Check if script is referenced by any workflow
            workflow = session.query(Workflow).filter(
                Workflow.uploaded_script_id == uuid.UUID(script_id)
            ).first()

            if workflow:
                logger.warning(f"Cannot delete script {script_id}: still referenced by workflow {workflow.id}")
                return False, "Cannot delete script: still in use by workflow"

            session.delete(script)
            session.commit()

            logger.info(f"Script deleted successfully: {script_id}")
            return True, "Script deleted successfully"

        except ValueError as e:
            logger.error(f"Invalid UUID format for script_id {script_id}: {e}")
            return False, f"Invalid script ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting script {script_id}: {e}")
            session.rollback() if session else None
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error deleting script {script_id}: {e}")
            session.rollback() if session else None
            return False, f"Deletion failed: {str(e)}"

    def get_scripts_by_workflow(self, workflow_id: str) -> list[UploadedScript]:
        """Get all scripts for a workflow"""
        try:
            session = self._get_session()

            scripts = session.query(UploadedScript).filter(
                UploadedScript.workflow_id == uuid.UUID(workflow_id)
            ).order_by(UploadedScript.upload_timestamp.desc()).all()

            logger.info(f"Retrieved {len(scripts)} scripts for workflow {workflow_id}")
            return scripts

        except ValueError as e:
            logger.error(f"Invalid UUID format for workflow_id {workflow_id}: {e}")
            return []
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving scripts for workflow {workflow_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving scripts for workflow {workflow_id}: {e}")
            return []

    def update_validation_status(
        self,
        script_id: str,
        status: ValidationStatusEnum
    ) -> Tuple[bool, str]:
        """Update validation status of uploaded script"""
        try:
            session = self._get_session()

            script = session.query(UploadedScript).filter(
                UploadedScript.id == uuid.UUID(script_id)
            ).first()

            if not script:
                return False, "Script not found"

            script.validation_status = status
            script.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"Updated validation status for script {script_id} to {status.value}")
            return True, f"Status updated to {status.value}"

        except ValueError as e:
            logger.error(f"Invalid UUID format for script_id {script_id}: {e}")
            return False, f"Invalid script ID format: {e}"
        except SQLAlchemyError as e:
            logger.error(f"Database error updating validation status: {e}")
            session.rollback() if session else None
            return False, f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error updating validation status: {e}")
            session.rollback() if session else None
            return False, f"Update failed: {str(e)}"

    def validate_script_content(self, content: str) -> Tuple[bool, list[str]]:
        """Validate script content without saving"""
        # Create temporary instance for validation
        temp_script = UploadedScript(
            workflow_id=uuid.uuid4(),  # Temporary UUID
            content=content,
            content_type="text/plain"
        )

        return temp_script.validate_content()

    def get_content_stats(self, script_id: str) -> Optional[dict]:
        """Get content statistics for a script"""
        script = self.get_script(script_id)
        if not script:
            return None

        return {
            "content_length": script.content_length,
            "file_name": script.file_name,
            "content_type": script.content_type,
            "validation_status": script.validation_status.value,
            "upload_timestamp": script.upload_timestamp.isoformat(),
            "word_count": len(script.content.split()) if script.content else 0,
            "line_count": script.content.count('\n') + 1 if script.content else 0
        }