"""Media Asset model for video composition components."""

from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, JSON, Enum, ForeignKey, Index, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
import uuid
import enum
import os
import re
from datetime import datetime
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

    # Gemini model tracking
    gemini_model_used = Column(String(100), nullable=True)  # Model used for generation (e.g., 'gemini-1.5-pro')
    generation_status = Column(Enum(GenerationStatusEnum), nullable=False, default=GenerationStatusEnum.pending)
    generation_metadata = Column(JSON, default=dict)  # Model availability, parameters, timestamps
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)

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
        Index('idx_media_assets_status', 'generation_status'),
        Index('idx_media_assets_model', 'gemini_model_used'),
        Index('idx_media_assets_generation_started', 'generation_started_at'),
        Index('idx_media_assets_generation_completed', 'generation_completed_at'),
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

    @validates('gemini_model_used')
    def validate_gemini_model(self, key: str, model_name: Optional[str]) -> Optional[str]:
        """Validate that gemini_model_used follows correct pattern when provided."""
        if model_name is not None:
            # Must be non-empty string
            if not isinstance(model_name, str) or not model_name.strip():
                raise ValueError("gemini_model_used must be a non-empty string when provided")

            model_name = model_name.strip()

            # Must follow gemini-* pattern (allowing dots, numbers, and hyphens)
            if not re.match(r'^gemini(-[a-z0-9.]+)*$', model_name, re.IGNORECASE):
                raise ValueError(f"gemini_model_used must follow 'gemini-*' pattern, got: {model_name}")

        return model_name

    @validates('generation_status')
    def validate_generation_status(self, key: str, status: GenerationStatusEnum) -> GenerationStatusEnum:
        """Validate generation status transitions."""
        if hasattr(self, '_original_status') and self._original_status is not None:
            old_status = self._original_status
            new_status = status

            # Define valid transitions
            valid_transitions = {
                GenerationStatusEnum.pending: [GenerationStatusEnum.generating, GenerationStatusEnum.failed],
                GenerationStatusEnum.generating: [GenerationStatusEnum.completed, GenerationStatusEnum.failed],
                GenerationStatusEnum.completed: [],  # Terminal state
                GenerationStatusEnum.failed: [GenerationStatusEnum.pending]  # Allow retry
            }

            if new_status not in valid_transitions.get(old_status, []):
                raise ValueError(f"Invalid status transition from {old_status.value} to {new_status.value}")

        return status

    @validates('generation_metadata')
    def validate_generation_metadata(self, key: str, metadata: Optional[Dict]) -> Dict:
        """Validate generation metadata structure."""
        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise ValueError("generation_metadata must be a dictionary")

        # Validate model availability info when present
        if 'model_availability' in metadata:
            availability = metadata['model_availability']
            if not isinstance(availability, dict):
                raise ValueError("model_availability must be a dictionary")

            # Check required fields in model availability
            required_fields = ['is_available', 'checked_at']
            for field in required_fields:
                if field not in availability:
                    raise ValueError(f"model_availability missing required field: {field}")

            # Validate timestamp format
            if 'checked_at' in availability:
                checked_at = availability['checked_at']
                if isinstance(checked_at, str):
                    try:
                        datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValueError("model_availability.checked_at must be a valid ISO format timestamp")

        # Validate generation parameters when present
        if 'generation_parameters' in metadata:
            params = metadata['generation_parameters']
            if not isinstance(params, dict):
                raise ValueError("generation_parameters must be a dictionary")

        return metadata

    @validates('generation_started_at')
    def validate_generation_started_at(self, key: str, timestamp: Optional[datetime]) -> Optional[datetime]:
        """Validate generation_started_at timestamp."""
        if timestamp is not None and not isinstance(timestamp, datetime):
            raise ValueError("generation_started_at must be a datetime object when provided")
        return timestamp

    @validates('generation_completed_at')
    def validate_generation_completed_at(self, key: str, timestamp: Optional[datetime]) -> Optional[datetime]:
        """Validate generation_completed_at timestamp."""
        if timestamp is not None and not isinstance(timestamp, datetime):
            raise ValueError("generation_completed_at must be a datetime object when provided")

        # Ensure completion timestamp is after start timestamp
        if (timestamp is not None and
            hasattr(self, 'generation_started_at') and
            self.generation_started_at is not None and
            timestamp < self.generation_started_at):
            raise ValueError("generation_completed_at cannot be before generation_started_at")

        return timestamp

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

    # New methods for Gemini model tracking

    def start_generation(self, model_name: str, generation_params: Optional[Dict] = None) -> None:
        """Mark asset generation as started with specified model."""
        if self.generation_status != GenerationStatusEnum.pending:
            raise ValueError(f"Cannot start generation from status: {self.generation_status.value}")

        self.gemini_model_used = model_name
        self.generation_status = GenerationStatusEnum.generating
        self.generation_started_at = datetime.utcnow()

        # Update generation metadata
        if not self.generation_metadata:
            self.generation_metadata = {}

        self.generation_metadata.update({
            'generation_started': datetime.utcnow().isoformat(),
            'generation_parameters': generation_params or {}
        })

    def complete_generation(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark asset generation as completed or failed."""
        if self.generation_status != GenerationStatusEnum.generating:
            raise ValueError(f"Cannot complete generation from status: {self.generation_status.value}")

        self.generation_status = GenerationStatusEnum.completed if success else GenerationStatusEnum.failed
        self.generation_completed_at = datetime.utcnow()

        # Update generation metadata
        if not self.generation_metadata:
            self.generation_metadata = {}

        self.generation_metadata.update({
            'generation_completed': datetime.utcnow().isoformat(),
            'success': success
        })

        if not success and error_message:
            self.generation_metadata['error_message'] = error_message

    def retry_generation(self) -> None:
        """Reset asset for retry after failure."""
        if self.generation_status != GenerationStatusEnum.failed:
            raise ValueError(f"Cannot retry from status: {self.generation_status.value}")

        self.generation_status = GenerationStatusEnum.pending
        self.generation_started_at = None
        self.generation_completed_at = None

        # Clear failure metadata but keep model info
        if self.generation_metadata:
            self.generation_metadata.pop('error_message', None)
            self.generation_metadata.pop('generation_started', None)
            self.generation_metadata.pop('generation_completed', None)

    def set_model_availability(self, is_available: bool, checked_at: Optional[datetime] = None) -> None:
        """Set model availability information in metadata."""
        if not self.generation_metadata:
            self.generation_metadata = {}

        check_time = checked_at or datetime.utcnow()
        self.generation_metadata['model_availability'] = {
            'is_available': is_available,
            'checked_at': check_time.isoformat()
        }

    def get_generation_duration(self) -> Optional[float]:
        """Get generation duration in seconds if available."""
        if (self.generation_started_at and self.generation_completed_at and
            self.generation_completed_at > self.generation_started_at):
            delta = self.generation_completed_at - self.generation_started_at
            return delta.total_seconds()
        return None

    @property
    def is_generation_in_progress(self) -> bool:
        """Check if generation is currently in progress."""
        return self.generation_status == GenerationStatusEnum.generating

    @property
    def is_generation_completed(self) -> bool:
        """Check if generation completed successfully."""
        return self.generation_status == GenerationStatusEnum.completed

    @property
    def is_generation_failed(self) -> bool:
        """Check if generation failed."""
        return self.generation_status == GenerationStatusEnum.failed

    def ensure_backward_compatibility(self) -> None:
        """Ensure backward compatibility with existing records without Gemini fields."""
        # Set default status if not set (for existing records)
        if not hasattr(self, 'generation_status') or self.generation_status is None:
            self.generation_status = GenerationStatusEnum.completed  # Assume existing records are completed

        # Initialize generation_metadata if not present
        if not hasattr(self, 'generation_metadata') or self.generation_metadata is None:
            self.generation_metadata = {}

        # For existing completed records without timestamps, set creation timestamp as completion
        if (self.generation_status == GenerationStatusEnum.completed and
            not self.generation_completed_at and
            hasattr(self, 'creation_timestamp') and self.creation_timestamp):
            self.generation_completed_at = self.creation_timestamp

    def validate_complete_model(self) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation that includes both existing and new validation rules.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Run existing metadata structure validation
        is_valid, metadata_errors = self.validate_metadata_structure()
        errors.extend(metadata_errors)

        # Validate Gemini model fields
        if self.gemini_model_used is not None:
            try:
                self.validate_gemini_model('gemini_model_used', self.gemini_model_used)
            except ValueError as e:
                errors.append(str(e))

        # Validate generation metadata structure
        try:
            self.validate_generation_metadata('generation_metadata', self.generation_metadata)
        except ValueError as e:
            errors.append(str(e))

        # Validate timestamp consistency
        if (self.generation_started_at and self.generation_completed_at and
            self.generation_completed_at < self.generation_started_at):
            errors.append("generation_completed_at cannot be before generation_started_at")

        # Validate status-timestamp consistency
        if self.generation_status == GenerationStatusEnum.generating and not self.generation_started_at:
            errors.append("generation_started_at is required when status is 'generating'")

        if (self.generation_status in [GenerationStatusEnum.completed, GenerationStatusEnum.failed] and
            not self.generation_completed_at):
            errors.append("generation_completed_at is required when status is 'completed' or 'failed'")

        # Validate that generation timestamps are set if model is specified
        if (self.gemini_model_used and
            self.generation_status != GenerationStatusEnum.pending and
            not self.generation_started_at):
            errors.append("generation_started_at is required when gemini_model_used is specified and status is not pending")

        return len(errors) == 0, errors


# SQLAlchemy event listeners for automatic status tracking

@event.listens_for(MediaAsset, 'load')
def receive_load(target, context):
    """Track original status on load for transition validation."""
    target._original_status = target.generation_status

@event.listens_for(MediaAsset, 'before_update')
def receive_before_update(mapper, connection, target):
    """Handle status transitions and timestamp updates."""
    # Store original status for validation
    if hasattr(target, 'generation_status'):
        original_status = getattr(target, '_original_status', None)
        if original_status != target.generation_status:
            # Status is changing, update original for validation
            target._original_status = original_status

    # Auto-set timestamps based on status changes
    if target.generation_status == GenerationStatusEnum.generating and not target.generation_started_at:
        target.generation_started_at = datetime.utcnow()

    if (target.generation_status in [GenerationStatusEnum.completed, GenerationStatusEnum.failed] and
        not target.generation_completed_at):
        target.generation_completed_at = datetime.utcnow()

@event.listens_for(MediaAsset.generation_status, 'set')
def receive_set_status(target, value, oldvalue, initiator):
    """Update original status tracking when status changes."""
    if oldvalue != value:
        target._original_status = oldvalue