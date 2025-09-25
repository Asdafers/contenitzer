"""Media Asset model for video composition components."""

from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
import uuid
import enum
import os
from typing import Optional, Dict, Any, List, Tuple

from .base import Base


class AssetTypeEnum(enum.Enum):
    """Type of media asset used in video composition."""
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO_CLIP = "VIDEO_CLIP"
    TEXT_OVERLAY = "TEXT_OVERLAY"


class SourceTypeEnum(enum.Enum):
    """Source type indicating how the asset was obtained."""
    GENERATED = "GENERATED"
    STOCK = "STOCK"
    USER_UPLOADED = "USER_UPLOADED"


class GenerationStatusEnum(enum.Enum):
    """Status of media asset generation process."""
    pending = "pending"
    generating = "generating"
    completed = "completed"
    failed = "failed"


class MediaAsset(Base):
    """
    Individual components used in video composition with processing metadata.

    Represents individual media assets (images, audio, video clips, text overlays)
    that are used as building blocks for video composition.
    """
    __tablename__ = "media_assets"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset classification
    asset_type = Column(Enum(AssetTypeEnum), nullable=False)
    source_type = Column(Enum(SourceTypeEnum), nullable=False)

    # File information
    file_path = Column(String(512), nullable=False)
    url_path = Column(String(256), nullable=False)

    # Asset properties
    duration = Column(Integer, nullable=True)  # Duration in seconds (null for images)
    asset_metadata = Column(JSON, default=dict)  # Type-specific properties

    # Generation tracking
    creation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    generation_job_id = Column(UUID(as_uuid=True), ForeignKey("video_generation_jobs.id"), nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    generation_job = relationship("VideoGenerationJob", back_populates="media_assets")

    # Indexes for performance
    __table_args__ = (
        Index('idx_media_assets_job', 'generation_job_id'),
        Index('idx_media_assets_type', 'asset_type'),
        Index('idx_media_assets_source', 'source_type'),
        Index('idx_media_assets_creation', 'creation_timestamp'),
    )

    def __repr__(self) -> str:
        return f"<MediaAsset(id={self.id}, type={self.asset_type.value}, source={self.source_type.value})>"

    @validates('file_path')
    def validate_file_path(self, key: str, file_path: str) -> str:
        """Validate that file_path exists for all asset types."""
        if file_path and not os.path.exists(file_path):
            raise ValueError(f"File path does not exist: {file_path}")
        return file_path

    @validates('duration')
    def validate_duration(self, key: str, duration: Optional[int]) -> Optional[int]:
        """Validate that duration is required for AUDIO and VIDEO_CLIP types."""
        if self.asset_type in [AssetTypeEnum.AUDIO, AssetTypeEnum.VIDEO_CLIP]:
            if duration is None or duration <= 0:
                raise ValueError(f"Duration is required and must be positive for {self.asset_type.value} assets")
        return duration

    def validate_metadata_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate that metadata structure matches asset_type requirements.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        metadata = self.asset_metadata or {}

        if self.asset_type == AssetTypeEnum.IMAGE:
            # Images: dimensions, format, generation_method
            required_fields = ['dimensions', 'format']
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field for IMAGE: {field}")

            if 'dimensions' in metadata:
                dims = metadata['dimensions']
                if not isinstance(dims, dict) or 'width' not in dims or 'height' not in dims:
                    errors.append("Image dimensions must be a dict with 'width' and 'height' fields")

        elif self.asset_type == AssetTypeEnum.AUDIO:
            # Audio: sample_rate, channels, codec
            required_fields = ['sample_rate', 'channels', 'codec']
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field for AUDIO: {field}")

            if 'sample_rate' in metadata and not isinstance(metadata['sample_rate'], int):
                errors.append("Audio sample_rate must be an integer")

            if 'channels' in metadata and not isinstance(metadata['channels'], int):
                errors.append("Audio channels must be an integer")

        elif self.asset_type == AssetTypeEnum.VIDEO_CLIP:
            # Video: resolution, fps, codec
            required_fields = ['resolution', 'fps', 'codec']
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field for VIDEO_CLIP: {field}")

            if 'fps' in metadata and not isinstance(metadata['fps'], (int, float)):
                errors.append("Video fps must be a number")

        elif self.asset_type == AssetTypeEnum.TEXT_OVERLAY:
            # Text: font, size, color, position
            required_fields = ['font', 'size', 'color', 'position']
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field for TEXT_OVERLAY: {field}")

            if 'position' in metadata:
                pos = metadata['position']
                if not isinstance(pos, dict) or 'x' not in pos or 'y' not in pos:
                    errors.append("Text position must be a dict with 'x' and 'y' fields")

        return len(errors) == 0, errors

    def set_image_metadata(self, width: int, height: int, format: str, generation_method: Optional[str] = None) -> None:
        """Set metadata for image assets."""
        if self.asset_type != AssetTypeEnum.IMAGE:
            raise ValueError("Can only set image metadata for IMAGE assets")

        self.asset_metadata = {
            'dimensions': {'width': width, 'height': height},
            'format': format,
            'generation_method': generation_method
        }

    def set_audio_metadata(self, sample_rate: int, channels: int, codec: str, bitrate: Optional[int] = None) -> None:
        """Set metadata for audio assets."""
        if self.asset_type != AssetTypeEnum.AUDIO:
            raise ValueError("Can only set audio metadata for AUDIO assets")

        metadata = {
            'sample_rate': sample_rate,
            'channels': channels,
            'codec': codec
        }
        if bitrate:
            metadata['bitrate'] = bitrate

        self.asset_metadata = metadata

    def set_video_metadata(self, resolution: str, fps: float, codec: str, bitrate: Optional[int] = None) -> None:
        """Set metadata for video clip assets."""
        if self.asset_type != AssetTypeEnum.VIDEO_CLIP:
            raise ValueError("Can only set video metadata for VIDEO_CLIP assets")

        metadata = {
            'resolution': resolution,
            'fps': fps,
            'codec': codec
        }
        if bitrate:
            metadata['bitrate'] = bitrate

        self.asset_metadata = metadata

    def set_text_metadata(self, font: str, size: int, color: str, x: int, y: int,
                         text_content: Optional[str] = None) -> None:
        """Set metadata for text overlay assets."""
        if self.asset_type != AssetTypeEnum.TEXT_OVERLAY:
            raise ValueError("Can only set text metadata for TEXT_OVERLAY assets")

        metadata = {
            'font': font,
            'size': size,
            'color': color,
            'position': {'x': x, 'y': y}
        }
        if text_content:
            metadata['text_content'] = text_content

        self.asset_metadata = metadata

    @property
    def requires_duration(self) -> bool:
        """Check if this asset type requires a duration value."""
        return self.asset_type in [AssetTypeEnum.AUDIO, AssetTypeEnum.VIDEO_CLIP]

    @property
    def is_generated(self) -> bool:
        """Check if this asset was generated (vs stock or user uploaded)."""
        return self.source_type == SourceTypeEnum.GENERATED

    @property
    def is_stock(self) -> bool:
        """Check if this asset is from stock library."""
        return self.source_type == SourceTypeEnum.STOCK

    def get_dimensions(self) -> Optional[Tuple[int, int]]:
        """Get asset dimensions for image and video assets."""
        if self.asset_type == AssetTypeEnum.IMAGE:
            dims = self.asset_metadata.get('dimensions', {})
            return (dims.get('width'), dims.get('height'))
        elif self.asset_type == AssetTypeEnum.VIDEO_CLIP:
            resolution = self.asset_metadata.get('resolution', '')
            if 'x' in resolution:
                try:
                    width, height = resolution.split('x')
                    return (int(width), int(height))
                except ValueError:
                    return None
        return None

    def get_file_extension(self) -> Optional[str]:
        """Extract file extension from file_path."""
        if self.file_path:
            return os.path.splitext(self.file_path)[1].lower()
        return None

    def get_display_name(self) -> str:
        """Get a user-friendly display name for the asset."""
        if self.file_path:
            filename = os.path.basename(self.file_path)
            name_without_ext = os.path.splitext(filename)[0]
            return f"{self.asset_type.value.title()}: {name_without_ext}"
        return f"{self.asset_type.value.title()} Asset"