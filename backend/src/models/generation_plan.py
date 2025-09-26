"""
Generation Plan Database Model
Stores content generation plans for approval workflow.
"""

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class PlanStatusEnum(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GenerationPlan(Base):
    __tablename__ = "generation_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_id = Column(UUID(as_uuid=True), ForeignKey('uploaded_scripts.id'), nullable=False)
    plan_data = Column(Text, nullable=False)  # JSON serialized plan
    status = Column(Enum(PlanStatusEnum), nullable=False, default=PlanStatusEnum.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to uploaded script
    script = relationship("UploadedScript", back_populates="generation_plans")

    def __repr__(self):
        return f"<GenerationPlan(id={self.id}, script_id={self.script_id}, status={self.status.value})>"