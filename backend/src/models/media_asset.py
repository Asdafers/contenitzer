from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from .base import Base


class AssetTypeEnum(enum.Enum):
    audio = "audio"
    image = "image"
    video = "video"


class GenerationStatusEnum(enum.Enum):
    pending = "pending"
    generating = "generating"
    completed = "completed"
    failed = "failed"


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("video_projects.id"), nullable=False)
    asset_type = Column(Enum(AssetTypeEnum), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    duration = Column(Integer, nullable=True)  # seconds, null for images
    generation_prompt = Column(Text, nullable=False)
    gemini_model_used = Column(String(100), nullable=False)
    generation_status = Column(Enum(GenerationStatusEnum), nullable=False, default=GenerationStatusEnum.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    asset_metadata = Column(JSON, default=dict)

    # Progress tracking fields
    generation_progress = Column(Integer, default=0, nullable=False)  # 0-100 progress percentage
    generation_started_at = Column(DateTime(timezone=True), nullable=True)  # When generation started
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)  # When generation completed
    estimated_duration = Column(Float, nullable=True)  # Estimated generation time in seconds
    task_id = Column(String(100), nullable=True)  # Associated Celery task ID

    # Relationships
    project = relationship("VideoProject", back_populates="media_assets")

    def __repr__(self):
        return f"<MediaAsset(type={self.asset_type.value}, status={self.generation_status.value})>"