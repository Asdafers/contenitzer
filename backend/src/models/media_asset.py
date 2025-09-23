from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey
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

    # Relationships
    project = relationship("VideoProject", back_populates="media_assets")

    def __repr__(self):
        return f"<MediaAsset(type={self.asset_type.value}, status={self.generation_status.value})>"