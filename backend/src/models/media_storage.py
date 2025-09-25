"""Media Storage model for file system organization and management."""

from sqlalchemy import Column, String, BigInteger, Integer, DateTime, JSON, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import validates
import uuid
import enum
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from .base import Base


class StorageTypeEnum(enum.Enum):
    """Type of media storage directory."""
    VIDEOS = "VIDEOS"
    IMAGES = "IMAGES"
    AUDIO = "AUDIO"
    TEMP = "TEMP"
    STOCK = "STOCK"


class MediaStorage(Base):
    """
    File system organization metadata with cleanup policies and access control.

    Manages storage directories, tracks usage, and handles cleanup policies
    for different types of media files.
    """
    __tablename__ = "media_storage"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Storage configuration
    directory_path = Column(String(512), nullable=False, unique=True)
    storage_type = Column(Enum(StorageTypeEnum), nullable=False)

    # Usage tracking
    total_size_bytes = Column(BigInteger, default=0, nullable=False)
    file_count = Column(Integer, default=0, nullable=False)

    # Cleanup management
    last_cleanup = Column(DateTime(timezone=True), nullable=True)
    cleanup_policy = Column(JSON, default=dict)  # retention rules
    access_permissions = Column(JSON, default=dict)  # access control

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_media_storage_type', 'storage_type'),
        Index('idx_media_storage_path', 'directory_path'),
        Index('idx_media_storage_size', 'total_size_bytes'),
        Index('idx_media_storage_cleanup', 'last_cleanup'),
    )

    def __repr__(self) -> str:
        return f"<MediaStorage(type={self.storage_type.value}, path='{self.directory_path}', size={self.get_size_mb()}MB)>"

    @validates('directory_path')
    def validate_directory_path(self, key: str, directory_path: str) -> str:
        """Validate that directory_path is absolute and exists."""
        if not directory_path:
            raise ValueError("Directory path cannot be empty")

        if not os.path.isabs(directory_path):
            raise ValueError("Directory path must be absolute")

        # Create directory if it doesn't exist
        Path(directory_path).mkdir(parents=True, exist_ok=True)

        return directory_path

    @validates('total_size_bytes')
    def validate_total_size_bytes(self, key: str, size: int) -> int:
        """Validate that total_size_bytes is non-negative."""
        if size is not None and size < 0:
            raise ValueError("Total size bytes must be non-negative")
        return size

    @validates('file_count')
    def validate_file_count(self, key: str, count: int) -> int:
        """Validate that file_count is non-negative."""
        if count is not None and count < 0:
            raise ValueError("File count must be non-negative")
        return count

    def set_cleanup_policy(self, max_age_days: Optional[int] = None, max_size_mb: Optional[int] = None,
                          preserve_completed_videos: bool = True, **kwargs) -> None:
        """
        Set cleanup policy with retention rules.

        Args:
            max_age_days: Maximum age in days before cleanup
            max_size_mb: Maximum storage size in MB before cleanup
            preserve_completed_videos: Whether to preserve completed videos
            **kwargs: Additional cleanup policy settings
        """
        policy = {
            'preserve_completed_videos': preserve_completed_videos
        }

        if max_age_days is not None:
            if max_age_days <= 0:
                raise ValueError("max_age_days must be positive")
            policy['max_age_days'] = max_age_days

        if max_size_mb is not None:
            if max_size_mb <= 0:
                raise ValueError("max_size_mb must be positive")
            policy['max_size_mb'] = max_size_mb

        policy.update(kwargs)
        self.cleanup_policy = policy

    def set_access_permissions(self, public_read: bool = False, authenticated_read: bool = True,
                             admin_write: bool = True, **kwargs) -> None:
        """
        Set access control permissions.

        Args:
            public_read: Allow public read access
            authenticated_read: Allow authenticated user read access
            admin_write: Allow admin write access
            **kwargs: Additional access permission settings
        """
        permissions = {
            'public_read': public_read,
            'authenticated_read': authenticated_read,
            'admin_write': admin_write
        }
        permissions.update(kwargs)
        self.access_permissions = permissions

    def validate_cleanup_policy(self) -> Tuple[bool, List[str]]:
        """
        Validate that cleanup_policy has valid retention settings.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        policy = self.cleanup_policy or {}

        # Check max_age_days if present
        if 'max_age_days' in policy:
            max_age = policy['max_age_days']
            if not isinstance(max_age, int) or max_age <= 0:
                errors.append("max_age_days must be a positive integer")

        # Check max_size_mb if present
        if 'max_size_mb' in policy:
            max_size = policy['max_size_mb']
            if not isinstance(max_size, int) or max_size <= 0:
                errors.append("max_size_mb must be a positive integer")

        # Check preserve_completed_videos if present
        if 'preserve_completed_videos' in policy:
            preserve = policy['preserve_completed_videos']
            if not isinstance(preserve, bool):
                errors.append("preserve_completed_videos must be a boolean")

        return len(errors) == 0, errors

    def update_usage_stats(self) -> None:
        """Update total_size_bytes and file_count by scanning directory."""
        if not os.path.exists(self.directory_path):
            self.total_size_bytes = 0
            self.file_count = 0
            return

        total_size = 0
        file_count = 0

        try:
            for root, dirs, files in os.walk(self.directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.isfile(file_path):
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        continue

            self.total_size_bytes = total_size
            self.file_count = file_count

        except (OSError, IOError):
            # If we can't scan the directory, keep current values
            pass

    def needs_cleanup(self) -> Tuple[bool, List[str]]:
        """
        Check if storage needs cleanup based on policy.

        Returns:
            Tuple of (needs_cleanup, list_of_reasons)
        """
        reasons = []
        policy = self.cleanup_policy or {}

        # Check age-based cleanup
        if 'max_age_days' in policy and self.last_cleanup:
            max_age = policy['max_age_days']
            cutoff_date = datetime.utcnow() - timedelta(days=max_age)
            if self.last_cleanup < cutoff_date:
                reasons.append(f"Last cleanup was more than {max_age} days ago")

        # Check size-based cleanup
        if 'max_size_mb' in policy:
            max_size_bytes = policy['max_size_mb'] * 1024 * 1024
            if self.total_size_bytes > max_size_bytes:
                current_mb = self.total_size_bytes / (1024 * 1024)
                reasons.append(f"Storage size ({current_mb:.1f}MB) exceeds limit ({policy['max_size_mb']}MB)")

        return len(reasons) > 0, reasons

    def mark_cleanup_completed(self) -> None:
        """Mark that cleanup was completed and update stats."""
        self.last_cleanup = func.now()
        self.update_usage_stats()

    def get_relative_path(self, file_path: str) -> Optional[str]:
        """
        Get relative path within this storage directory.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path within storage directory, or None if outside
        """
        try:
            storage_path = Path(self.directory_path)
            target_path = Path(file_path)
            return str(target_path.relative_to(storage_path))
        except ValueError:
            # Path is not within storage directory
            return None

    def get_full_path(self, relative_path: str) -> str:
        """
        Get full absolute path from relative path within storage.

        Args:
            relative_path: Relative path within storage directory

        Returns:
            Full absolute path
        """
        return os.path.join(self.directory_path, relative_path)

    @property
    def is_accessible(self) -> bool:
        """Check if storage directory is currently accessible."""
        return os.path.exists(self.directory_path) and os.access(self.directory_path, os.R_OK | os.W_OK)

    @property
    def allows_public_read(self) -> bool:
        """Check if public read access is allowed."""
        return self.access_permissions.get('public_read', False)

    @property
    def allows_authenticated_read(self) -> bool:
        """Check if authenticated read access is allowed."""
        return self.access_permissions.get('authenticated_read', True)

    @property
    def allows_admin_write(self) -> bool:
        """Check if admin write access is allowed."""
        return self.access_permissions.get('admin_write', True)

    def get_size_mb(self) -> float:
        """Get storage size in megabytes."""
        return round(self.total_size_bytes / (1024 * 1024), 2)

    def get_size_gb(self) -> float:
        """Get storage size in gigabytes."""
        return round(self.total_size_bytes / (1024 * 1024 * 1024), 2)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of storage usage and configuration."""
        return {
            'storage_type': self.storage_type.value,
            'directory_path': self.directory_path,
            'total_size_mb': self.get_size_mb(),
            'file_count': self.file_count,
            'last_cleanup': self.last_cleanup.isoformat() if self.last_cleanup else None,
            'is_accessible': self.is_accessible,
            'cleanup_policy': self.cleanup_policy,
            'access_permissions': self.access_permissions
        }

    @classmethod
    def get_storage_by_type(cls, storage_type: StorageTypeEnum) -> Optional['MediaStorage']:
        """
        Get storage configuration for a specific type.

        Args:
            storage_type: Type of storage to find

        Returns:
            MediaStorage instance or None if not found
        """
        from sqlalchemy.orm import sessionmaker
        # This would need to be implemented with actual session management
        # For now, returning None as placeholder
        return None

    @classmethod
    def create_default_storages(cls, base_path: str) -> List['MediaStorage']:
        """
        Create default storage configurations.

        Args:
            base_path: Base directory path for all storages

        Returns:
            List of created MediaStorage instances
        """
        storages = []

        storage_configs = [
            (StorageTypeEnum.VIDEOS, 'videos', {'max_size_mb': 10240, 'preserve_completed_videos': True}),
            (StorageTypeEnum.IMAGES, 'images', {'max_age_days': 30, 'max_size_mb': 2048}),
            (StorageTypeEnum.AUDIO, 'audio', {'max_age_days': 30, 'max_size_mb': 1024}),
            (StorageTypeEnum.TEMP, 'temp', {'max_age_days': 7, 'max_size_mb': 5120}),
            (StorageTypeEnum.STOCK, 'stock', {'preserve_completed_videos': True}),
        ]

        for storage_type, subdir, cleanup_policy in storage_configs:
            directory_path = os.path.join(base_path, subdir)

            storage = cls(
                directory_path=directory_path,
                storage_type=storage_type
            )
            storage.set_cleanup_policy(**cleanup_policy)
            storage.set_access_permissions()

            storages.append(storage)

        return storages