from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class WorkflowModeEnum(enum.Enum):
    GENERATE = "GENERATE"
    UPLOAD = "UPLOAD"


class ScriptSourceEnum(enum.Enum):
    GENERATED = "GENERATED"
    UPLOADED = "UPLOADED"


class WorkflowStatusEnum(enum.Enum):
    CREATED = "CREATED"
    MODE_SELECTED = "MODE_SELECTED"
    SCRIPT_READY = "SCRIPT_READY"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For future user system integration

    # Mode and script handling
    mode = Column(Enum(WorkflowModeEnum), nullable=False, default=WorkflowModeEnum.GENERATE)
    script_source = Column(Enum(ScriptSourceEnum), nullable=True)
    uploaded_script_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_scripts.id"), nullable=True)

    # Skip flags for workflow steps
    skip_research = Column(Boolean, nullable=False, default=False)
    skip_generation = Column(Boolean, nullable=False, default=False)

    # Workflow status
    status = Column(Enum(WorkflowStatusEnum), nullable=False, default=WorkflowStatusEnum.CREATED)

    # Metadata
    title = Column(String(200), nullable=True)
    description = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    uploaded_script = relationship("UploadedScript", backref="workflow")

    def __repr__(self):
        return f"<Workflow(id={self.id}, mode={self.mode.value}, status={self.status.value})>"

    def set_upload_mode(self, uploaded_script_id: uuid.UUID) -> None:
        """Configure workflow for script upload mode"""
        self.mode = WorkflowModeEnum.UPLOAD
        self.script_source = ScriptSourceEnum.UPLOADED
        self.uploaded_script_id = uploaded_script_id
        self.skip_research = True
        self.skip_generation = True
        self.status = WorkflowStatusEnum.MODE_SELECTED

    def set_generate_mode(self) -> None:
        """Configure workflow for script generation mode"""
        self.mode = WorkflowModeEnum.GENERATE
        self.script_source = ScriptSourceEnum.GENERATED
        self.uploaded_script_id = None
        self.skip_research = False
        self.skip_generation = False
        self.status = WorkflowStatusEnum.MODE_SELECTED

    def can_proceed_to_processing(self) -> bool:
        """Check if workflow is ready to proceed to content processing"""
        if self.mode == WorkflowModeEnum.UPLOAD:
            return (self.uploaded_script_id is not None and
                   self.status == WorkflowStatusEnum.SCRIPT_READY)
        elif self.mode == WorkflowModeEnum.GENERATE:
            return self.status == WorkflowStatusEnum.SCRIPT_READY
        return False

    def get_next_steps(self) -> list[str]:
        """Get list of next workflow steps based on current state and mode"""
        if self.status == WorkflowStatusEnum.CREATED:
            return ["select_mode"]

        if self.status == WorkflowStatusEnum.MODE_SELECTED:
            if self.mode == WorkflowModeEnum.UPLOAD:
                return ["upload_script", "validate_script"]
            elif self.mode == WorkflowModeEnum.GENERATE:
                return ["youtube_research", "generate_script"]

        if self.status == WorkflowStatusEnum.SCRIPT_READY:
            return ["content_optimization", "formatting", "publishing"]

        return []