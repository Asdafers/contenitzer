"""Generated Video model for tracking completed video generation results."""

from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
import uuid
import enum
import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

from .base import Base


class GenerationStatusEnum(enum.Enum):
    """Status of video generation process."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GeneratedVideo(Base):
    """
    Physical video file with comprehensive metadata and generation tracking.

    Represents the final output of the video generation process, including
    file information, metadata, and status tracking.
    """
    __tablename__ = "generated_videos"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File information
    file_path = Column(String(512), nullable=True)  # Nullable until generation completes
    url_path = Column(String(256), nullable=False)
    title = Column(String(256), nullable=False)

    # Video metadata
    duration = Column(Integer, nullable=False)  # Duration in seconds
    resolution = Column(String(16), nullable=False)  # Format: "WIDTHxHEIGHT"
    file_size = Column(BigInteger, nullable=True)  # File size in bytes, nullable until completed
    format = Column(String(16), nullable=False)  # Video format/codec (e.g., "mp4", "webm")

    # Generation tracking
    creation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    completion_timestamp = Column(DateTime(timezone=True), nullable=True)
    generation_status = Column(Enum(GenerationStatusEnum), nullable=False, default=GenerationStatusEnum.PENDING)

    # Foreign key relationships
    script_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to VideoScript or UploadedScript
    session_id = Column(String(128), nullable=False)  # User session that requested generation
    generation_job_id = Column(UUID(as_uuid=True), ForeignKey("video_generation_jobs.id"), nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    generation_job = relationship("VideoGenerationJob", back_populates="generated_video", uselist=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_generated_videos_session', 'session_id'),
        Index('idx_generated_videos_script', 'script_id'),
        Index('idx_generated_videos_status', 'generation_status'),
        Index('idx_generated_videos_creation', 'creation_timestamp'),
    )

    def __repr__(self) -> str:
        return f"<GeneratedVideo(id={self.id}, title='{self.title[:30]}...', status={self.generation_status.value})>"

    @validates('duration')
    def validate_duration(self, key: str, duration: int) -> int:
        """Validate that duration is a positive number."""
        if duration is not None and duration <= 0:
            raise ValueError("Duration must be a positive number")
        return duration

    @validates('resolution')
    def validate_resolution(self, key: str, resolution: str) -> str:
        """Validate that resolution matches format 'WIDTHxHEIGHT'."""
        if resolution and not re.match(r'^\d+x\d+$', resolution):
            raise ValueError("Resolution must match format 'WIDTHxHEIGHT' (e.g., '1920x1080')")
        return resolution

    @validates('file_size')
    def validate_file_size(self, key: str, file_size: Optional[int]) -> Optional[int]:
        """Validate that file_size is positive when provided."""
        if file_size is not None and file_size <= 0:
            raise ValueError("File size must be positive")
        return file_size

    @validates('file_path')
    def validate_file_path(self, key: str, file_path: Optional[str]) -> Optional[str]:
        """Validate that file_path exists when status is COMPLETED."""
        if file_path and self.generation_status == GenerationStatusEnum.COMPLETED:
            if not os.path.exists(file_path):
                raise ValueError(f"File path does not exist: {file_path}")
        return file_path

    def validate_status_transition(self, new_status: GenerationStatusEnum) -> bool:
        """
        Validate that status transition is allowed.

        Valid transitions:
        PENDING → GENERATING → COMPLETED
                ↓
               FAILED

        Args:
            new_status: The status to transition to

        Returns:
            True if transition is valid, False otherwise
        """
        current = self.generation_status

        # Define valid transitions
        valid_transitions = {
            GenerationStatusEnum.PENDING: [GenerationStatusEnum.GENERATING, GenerationStatusEnum.FAILED],
            GenerationStatusEnum.GENERATING: [GenerationStatusEnum.COMPLETED, GenerationStatusEnum.FAILED],
            GenerationStatusEnum.COMPLETED: [],  # Terminal state
            GenerationStatusEnum.FAILED: []  # Terminal state
        }

        return new_status in valid_transitions.get(current, [])

    def transition_status(self, new_status: GenerationStatusEnum) -> bool:
        """
        Safely transition to a new status with validation.

        Args:
            new_status: The status to transition to

        Returns:
            True if transition was successful, False otherwise
        """
        if not self.validate_status_transition(new_status):
            return False

        self.generation_status = new_status

        # Set completion timestamp when transitioning to terminal states
        if new_status in [GenerationStatusEnum.COMPLETED, GenerationStatusEnum.FAILED]:
            self.completion_timestamp = func.now()

        return True

    def validate_completion_requirements(self) -> Tuple[bool, List[str]]:
        """
        Validate that all requirements are met for COMPLETED status.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if self.generation_status == GenerationStatusEnum.COMPLETED:
            if not self.file_path:
                errors.append("file_path is required when status is COMPLETED")
            elif not os.path.exists(self.file_path):
                errors.append(f"File does not exist at path: {self.file_path}")

            if not self.file_size or self.file_size <= 0:
                errors.append("file_size must be positive when status is COMPLETED")

            if not self.completion_timestamp:
                errors.append("completion_timestamp is required when status is COMPLETED")

        return len(errors) == 0, errors

    @property
    def is_completed(self) -> bool:
        """Check if video generation is completed."""
        return self.generation_status == GenerationStatusEnum.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if video generation failed."""
        return self.generation_status == GenerationStatusEnum.FAILED

    @property
    def is_terminal(self) -> bool:
        """Check if video generation is in a terminal state (completed or failed)."""
        return self.generation_status in [GenerationStatusEnum.COMPLETED, GenerationStatusEnum.FAILED]

    @property
    def generation_duration_seconds(self) -> Optional[int]:
        """Calculate generation duration in seconds if completed."""
        if self.completion_timestamp and self.creation_timestamp:
            delta = self.completion_timestamp - self.creation_timestamp
            return int(delta.total_seconds())
        return None

    def get_file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes."""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    def get_resolution_tuple(self) -> Optional[Tuple[int, int]]:
        """Parse resolution string into (width, height) tuple."""
        if self.resolution and 'x' in self.resolution:
            try:
                width, height = self.resolution.split('x')
                return (int(width), int(height))
            except ValueError:
                return None
        return None