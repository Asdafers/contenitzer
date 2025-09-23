from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class UploadStatusEnum(enum.Enum):
    pending = "pending"
    uploading = "uploading"
    completed = "completed"
    failed = "failed"


class ComposedVideo(Base):
    __tablename__ = "composed_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("video_projects.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    duration = Column(Integer, nullable=False)  # seconds
    resolution = Column(String(20), nullable=False)  # e.g., "1920x1080"
    format = Column(String(10), nullable=False)  # e.g., "mp4"
    composition_settings = Column(JSON, default=dict)
    youtube_video_id = Column(String(20), nullable=True)
    upload_status = Column(Enum(UploadStatusEnum), nullable=False, default=UploadStatusEnum.pending)
    upload_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("VideoProject", back_populates="composed_video")

    def __repr__(self):
        return f"<ComposedVideo(duration={self.duration}s, status={self.upload_status.value})>"