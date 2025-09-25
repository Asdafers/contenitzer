"""Video Generation Job model for tracking complete video creation workflow."""

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
import uuid
import enum
from typing import Optional, Dict, Any, List, Tuple

from .base import Base


class JobStatusEnum(enum.Enum):
    """Status of video generation job process."""
    PENDING = "PENDING"
    MEDIA_GENERATION = "MEDIA_GENERATION"
    VIDEO_COMPOSITION = "VIDEO_COMPOSITION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VideoGenerationJob(Base):
    """
    Process record tracking complete video creation workflow with resource usage.

    Tracks the entire video generation process from script to final video,
    including progress tracking, resource usage, and error handling.
    """
    __tablename__ = "video_generation_jobs"

    # Primary key (matches Celery task ID)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job identification
    session_id = Column(String(128), nullable=False)  # User session for progress tracking
    script_id = Column(UUID(as_uuid=True), nullable=False)  # Source script reference

    # Job status and progress
    status = Column(Enum(JobStatusEnum), nullable=False, default=JobStatusEnum.PENDING)
    progress_percentage = Column(Integer, default=0, nullable=False)  # 0-100

    # Timing information
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Performance metrics (JSON field)
    resource_usage = Column(JSON, default=dict)  # performance metrics

    # Generation parameters (JSON field)
    composition_settings = Column(JSON, default=dict)  # video generation parameters

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    media_assets = relationship("MediaAsset", back_populates="generation_job", cascade="all, delete-orphan")
    generated_video = relationship("GeneratedVideo", back_populates="generation_job", uselist=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_video_jobs_session', 'session_id'),
        Index('idx_video_jobs_script', 'script_id'),
        Index('idx_video_jobs_status', 'status'),
        Index('idx_video_jobs_started', 'started_at'),
    )

    def __repr__(self) -> str:
        return f"<VideoGenerationJob(id={self.id}, session={self.session_id}, status={self.status.value})>"

    @validates('progress_percentage')
    def validate_progress_percentage(self, key: str, progress: int) -> int:
        """Validate that progress_percentage is between 0-100."""
        if progress is not None and (progress < 0 or progress > 100):
            raise ValueError("Progress percentage must be between 0 and 100")
        return progress

    def validate_status_transition(self, new_status: JobStatusEnum) -> bool:
        """
        Validate that status transition is allowed.

        Valid transitions:
        PENDING → MEDIA_GENERATION → VIDEO_COMPOSITION → COMPLETED
                ↓                  ↓                  ↓
               FAILED            FAILED            FAILED

        Args:
            new_status: The status to transition to

        Returns:
            True if transition is valid, False otherwise
        """
        current = self.status

        # Define valid transitions
        valid_transitions = {
            JobStatusEnum.PENDING: [JobStatusEnum.MEDIA_GENERATION, JobStatusEnum.FAILED],
            JobStatusEnum.MEDIA_GENERATION: [JobStatusEnum.VIDEO_COMPOSITION, JobStatusEnum.FAILED],
            JobStatusEnum.VIDEO_COMPOSITION: [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED],
            JobStatusEnum.COMPLETED: [],  # Terminal state
            JobStatusEnum.FAILED: []  # Terminal state
        }

        return new_status in valid_transitions.get(current, [])

    def transition_status(self, new_status: JobStatusEnum, error_message: Optional[str] = None) -> bool:
        """
        Safely transition to a new status with validation.

        Args:
            new_status: The status to transition to
            error_message: Error message if transitioning to FAILED status

        Returns:
            True if transition was successful, False otherwise
        """
        if not self.validate_status_transition(new_status):
            return False

        self.status = new_status

        # Set completion timestamp and handle error message for terminal states
        if new_status == JobStatusEnum.COMPLETED:
            self.completed_at = func.now()
            self.progress_percentage = 100
        elif new_status == JobStatusEnum.FAILED:
            self.completed_at = func.now()
            if error_message:
                self.error_message = error_message

        return True

    def validate_completion_requirements(self) -> Tuple[bool, List[str]]:
        """
        Validate that all requirements are met for job completion.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check completed_at is after started_at
        if self.completed_at and self.started_at:
            if self.completed_at <= self.started_at:
                errors.append("completed_at must be after started_at")

        # Check error_message is present when status is FAILED
        if self.status == JobStatusEnum.FAILED:
            if not self.error_message:
                errors.append("error_message is required when status is FAILED")

        # Check resource_usage is populated when status is COMPLETED
        if self.status == JobStatusEnum.COMPLETED:
            if not self.resource_usage:
                errors.append("resource_usage must be populated when status is COMPLETED")

        # Check progress is 100 when completed
        if self.status == JobStatusEnum.COMPLETED:
            if self.progress_percentage != 100:
                errors.append("progress_percentage must be 100 when status is COMPLETED")

        return len(errors) == 0, errors

    def set_composition_settings(self, target_resolution: str, target_duration: int,
                               quality_preset: str, include_audio: bool = True,
                               **kwargs) -> None:
        """
        Set video generation parameters.

        Args:
            target_resolution: Target video resolution (e.g., "1920x1080")
            target_duration: Target video duration in seconds
            quality_preset: Quality preset (e.g., "high", "medium", "low")
            include_audio: Whether to include audio in the video
            **kwargs: Additional composition settings
        """
        settings = {
            'target_resolution': target_resolution,
            'target_duration': target_duration,
            'quality_preset': quality_preset,
            'include_audio': include_audio
        }
        settings.update(kwargs)
        self.composition_settings = settings

    def set_resource_usage(self, generation_time_seconds: float, peak_memory_mb: int,
                          disk_space_used_mb: int, cpu_time_seconds: float,
                          **kwargs) -> None:
        """
        Set performance metrics after job completion.

        Args:
            generation_time_seconds: Total time taken for generation
            peak_memory_mb: Peak memory usage in MB
            disk_space_used_mb: Disk space used in MB
            cpu_time_seconds: CPU time consumed
            **kwargs: Additional resource usage metrics
        """
        usage = {
            'generation_time_seconds': generation_time_seconds,
            'peak_memory_mb': peak_memory_mb,
            'disk_space_used_mb': disk_space_used_mb,
            'cpu_time_seconds': cpu_time_seconds
        }
        usage.update(kwargs)
        self.resource_usage = usage

    def update_progress(self, percentage: int, status: Optional[JobStatusEnum] = None) -> bool:
        """
        Update job progress and optionally status.

        Args:
            percentage: Progress percentage (0-100)
            status: Optional new status

        Returns:
            True if update was successful, False otherwise
        """
        # Validate progress percentage
        if percentage < 0 or percentage > 100:
            return False

        # Update progress
        self.progress_percentage = percentage

        # Update status if provided
        if status and status != self.status:
            return self.transition_status(status)

        return True

    @property
    def is_completed(self) -> bool:
        """Check if job is completed successfully."""
        return self.status == JobStatusEnum.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == JobStatusEnum.FAILED

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state (completed or failed)."""
        return self.status in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED]

    @property
    def is_running(self) -> bool:
        """Check if job is currently running (not pending, not terminal)."""
        return self.status in [JobStatusEnum.MEDIA_GENERATION, JobStatusEnum.VIDEO_COMPOSITION]

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate job duration in seconds if completed."""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds())
        return None

    def get_target_resolution_tuple(self) -> Optional[Tuple[int, int]]:
        """Parse target resolution from composition settings."""
        resolution = self.composition_settings.get('target_resolution', '')
        if 'x' in resolution:
            try:
                width, height = resolution.split('x')
                return (int(width), int(height))
            except ValueError:
                return None
        return None

    def get_estimated_completion_time(self) -> Optional[float]:
        """
        Estimate remaining completion time based on current progress.

        Returns:
            Estimated seconds remaining, or None if can't estimate
        """
        if (self.is_terminal or self.progress_percentage <= 0 or
            not self.started_at):
            return None

        from datetime import datetime, timezone
        elapsed_seconds = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        progress_ratio = self.progress_percentage / 100.0
        estimated_total_time = elapsed_seconds / progress_ratio
        estimated_remaining = estimated_total_time - elapsed_seconds

        return max(0, estimated_remaining)

    def get_status_display(self) -> str:
        """Get a user-friendly status display string."""
        status_map = {
            JobStatusEnum.PENDING: "Pending",
            JobStatusEnum.MEDIA_GENERATION: "Generating Media Assets",
            JobStatusEnum.VIDEO_COMPOSITION: "Composing Video",
            JobStatusEnum.COMPLETED: "Completed",
            JobStatusEnum.FAILED: "Failed"
        }
        return status_map.get(self.status, self.status.value)