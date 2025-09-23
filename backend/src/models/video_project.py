from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class ProjectStatusEnum(enum.Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    uploading = "uploading"
    completed = "completed"
    failed = "failed"


class VideoProject(Base):
    __tablename__ = "video_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_id = Column(UUID(as_uuid=True), ForeignKey("video_scripts.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    status = Column(Enum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completion_percentage = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

    # Relationships
    script = relationship("VideoScript", back_populates="project")
    media_assets = relationship("MediaAsset", back_populates="project")
    composed_video = relationship("ComposedVideo", back_populates="project", uselist=False)

    def __repr__(self):
        return f"<VideoProject(name={self.project_name}, status={self.status.value})>"