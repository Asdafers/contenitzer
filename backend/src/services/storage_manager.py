"""
Storage Manager Service for organizing media files and managing storage policies.
Handles file organization, cleanup, quota enforcement, and path management.
"""
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime, timedelta
import uuid

from ..models.media_storage import MediaStorage, StorageTypeEnum as StorageType
from ..lib.database import get_db_session

logger = logging.getLogger(__name__)


class StorageManagerError(Exception):
    """Exception raised by storage management operations."""
    pass


class StorageManager:
    """Service for managing media file storage and organization."""

    def __init__(self, base_path: Optional[Path] = None):
        # Use absolute path, defaulting to current working directory + media
        if base_path is None:
            self.base_path = Path.cwd() / "media"
        else:
            self.base_path = base_path if base_path.is_absolute() else Path.cwd() / base_path
        self.ensure_directory_structure()

    def ensure_directory_structure(self):
        """Ensure all required media directories exist."""
        required_dirs = [
            self.base_path / "videos",
            self.base_path / "assets" / "images",
            self.base_path / "assets" / "audio",
            self.base_path / "assets" / "temp",
            self.base_path / "stock"
        ]

        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_video_path(self) -> Path:
        """Get path for video storage."""
        return self.base_path / "videos"

    def get_asset_path(self, asset_type: str) -> Path:
        """Get path for specific asset type storage."""
        asset_paths = {
            "images": self.base_path / "assets" / "images",
            "audio": self.base_path / "assets" / "audio",
            "video": self.base_path / "assets" / "video",
            "temp": self.base_path / "assets" / "temp"
        }

        if asset_type not in asset_paths:
            raise StorageManagerError(f"Unknown asset type: {asset_type}")

        path = asset_paths[asset_type]
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_stock_path(self) -> Path:
        """Get path for stock assets."""
        return self.base_path / "stock"

    def get_temp_path(self) -> Path:
        """Get path for temporary files."""
        temp_path = self.base_path / "assets" / "temp"
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path

    def initialize_storage_records(self) -> List[MediaStorage]:
        """Initialize MediaStorage records for all storage directories."""
        try:
            storage_configs = [
                {
                    "type": StorageType.VIDEOS,
                    "path": self.get_video_path(),
                    "cleanup_policy": {
                        "max_age_days": 30,
                        "max_size_mb": 10240,  # 10GB
                        "preserve_completed_videos": True
                    }
                },
                {
                    "type": StorageType.IMAGES,
                    "path": self.get_asset_path("images"),
                    "cleanup_policy": {
                        "max_age_days": 7,
                        "max_size_mb": 2048,  # 2GB
                        "preserve_completed_videos": False
                    }
                },
                {
                    "type": StorageType.AUDIO,
                    "path": self.get_asset_path("audio"),
                    "cleanup_policy": {
                        "max_age_days": 7,
                        "max_size_mb": 1024,  # 1GB
                        "preserve_completed_videos": False
                    }
                },
                {
                    "type": StorageType.TEMP,
                    "path": self.get_temp_path(),
                    "cleanup_policy": {
                        "max_age_days": 1,
                        "max_size_mb": 5120,  # 5GB
                        "preserve_completed_videos": False
                    }
                },
                {
                    "type": StorageType.STOCK,
                    "path": self.get_stock_path(),
                    "cleanup_policy": {
                        "max_age_days": 365,
                        "max_size_mb": 1024,  # 1GB
                        "preserve_completed_videos": True
                    }
                }
            ]

            storage_records = []

            with get_db_session() as db:
                for config in storage_configs:
                    # Check if record already exists
                    existing = db.query(MediaStorage).filter(
                        MediaStorage.storage_type == config["type"]
                    ).first()

                    if existing:
                        storage_records.append(existing)
                        continue

                    # Create new storage record
                    storage = MediaStorage(
                        id=uuid.uuid4(),
                        directory_path=str(config["path"]),
                        storage_type=config["type"],
                        cleanup_policy=config["cleanup_policy"],
                        access_permissions={
                            "public_read": config["type"] == StorageType.VIDEOS,
                            "authenticated_read": True,
                            "admin_write": True
                        }
                    )

                    # Update usage statistics
                    storage.update_usage_stats()

                    db.add(storage)
                    storage_records.append(storage)

                db.commit()

            return storage_records

        except Exception as e:
            logger.error(f"Failed to initialize storage records: {e}")
            raise StorageManagerError(f"Storage initialization failed: {e}")

    def scan_storage_usage(self) -> Dict[StorageType, Dict[str, Any]]:
        """Scan all storage directories and return usage statistics."""
        try:
            usage_stats = {}

            with get_db_session() as db:
                storage_records = db.query(MediaStorage).all()

                for storage in storage_records:
                    # Update storage statistics
                    storage.update_usage_stats()

                    usage_stats[storage.storage_type] = {
                        "directory_path": storage.directory_path,
                        "total_size_bytes": storage.total_size_bytes,
                        "file_count": storage.file_count,
                        "last_cleanup": storage.last_cleanup,
                        "needs_cleanup": storage.needs_cleanup(),
                        "cleanup_policy": storage.cleanup_policy
                    }

                db.commit()

            return usage_stats

        except Exception as e:
            logger.error(f"Failed to scan storage usage: {e}")
            raise StorageManagerError(f"Storage usage scan failed: {e}")

    def cleanup_expired_files(self, storage_type: Optional[StorageType] = None) -> Dict[str, Any]:
        """Clean up expired files based on storage policies."""
        try:
            cleanup_results = {
                "files_removed": 0,
                "bytes_freed": 0,
                "errors": []
            }

            with get_db_session() as db:
                # Get storage records to clean
                query = db.query(MediaStorage)
                if storage_type:
                    query = query.filter(MediaStorage.storage_type == storage_type)

                storage_records = query.all()

                for storage in storage_records:
                    try:
                        result = self._cleanup_storage_directory(storage)
                        cleanup_results["files_removed"] += result["files_removed"]
                        cleanup_results["bytes_freed"] += result["bytes_freed"]

                        # Update last cleanup time
                        storage.last_cleanup = datetime.now()

                    except Exception as e:
                        error_msg = f"Cleanup failed for {storage.storage_type}: {e}"
                        cleanup_results["errors"].append(error_msg)
                        logger.error(error_msg)

                db.commit()

            logger.info(f"Cleanup completed: {cleanup_results['files_removed']} files, "
                       f"{cleanup_results['bytes_freed']} bytes freed")

            return cleanup_results

        except Exception as e:
            logger.error(f"Failed to cleanup expired files: {e}")
            raise StorageManagerError(f"File cleanup failed: {e}")

    def _cleanup_storage_directory(self, storage: MediaStorage) -> Dict[str, Any]:
        """Clean up a specific storage directory."""
        result = {"files_removed": 0, "bytes_freed": 0}

        if not storage.cleanup_policy:
            return result

        directory = Path(storage.directory_path)
        if not directory.exists():
            return result

        max_age_days = storage.cleanup_policy.get("max_age_days", 30)
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                # Check file age
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime > cutoff_date:
                    continue

                # Check if file should be preserved
                if self._should_preserve_file(file_path, storage):
                    continue

                # Remove the file
                file_size = file_path.stat().st_size
                file_path.unlink()

                result["files_removed"] += 1
                result["bytes_freed"] += file_size

                logger.debug(f"Removed expired file: {file_path}")

            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")

        return result

    def _should_preserve_file(self, file_path: Path, storage: MediaStorage) -> bool:
        """Check if a file should be preserved based on storage policy."""
        policy = storage.cleanup_policy or {}

        # Always preserve if policy says so
        if policy.get("preserve_completed_videos", False):
            # Check if this file is associated with a completed video
            # In real implementation, would check database relationships
            if storage.storage_type == StorageType.VIDEOS:
                return True

        # Don't preserve temp files
        if storage.storage_type == StorageType.TEMP:
            return False

        # Don't preserve old asset files unless they're stock
        if storage.storage_type == StorageType.STOCK:
            return True

        return False

    def enforce_storage_quotas(self) -> Dict[str, Any]:
        """Enforce storage quotas by cleaning up excess files."""
        try:
            quota_results = {
                "quotas_enforced": 0,
                "bytes_freed": 0,
                "warnings": []
            }

            with get_db_session() as db:
                storage_records = db.query(MediaStorage).all()

                for storage in storage_records:
                    try:
                        # Update current usage
                        storage.update_usage_stats()

                        policy = storage.cleanup_policy or {}
                        max_size_mb = policy.get("max_size_mb", 1024)
                        max_size_bytes = max_size_mb * 1024 * 1024

                        if storage.total_size_bytes > max_size_bytes:
                            # Quota exceeded - clean up oldest files
                            bytes_to_free = storage.total_size_bytes - max_size_bytes
                            freed = self._free_storage_space(storage, bytes_to_free)

                            quota_results["quotas_enforced"] += 1
                            quota_results["bytes_freed"] += freed

                            logger.info(f"Freed {freed} bytes from {storage.storage_type}")

                    except Exception as e:
                        warning = f"Quota enforcement failed for {storage.storage_type}: {e}"
                        quota_results["warnings"].append(warning)
                        logger.warning(warning)

                db.commit()

            return quota_results

        except Exception as e:
            logger.error(f"Failed to enforce storage quotas: {e}")
            raise StorageManagerError(f"Quota enforcement failed: {e}")

    def _free_storage_space(self, storage: MediaStorage, bytes_needed: int) -> int:
        """Free up storage space by removing oldest files."""
        directory = Path(storage.directory_path)
        if not directory.exists():
            return 0

        # Get all files with their modification times
        files_with_times = []
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    mtime = file_path.stat().st_mtime
                    size = file_path.stat().st_size
                    files_with_times.append((file_path, mtime, size))
                except Exception:
                    continue

        # Sort by oldest first
        files_with_times.sort(key=lambda x: x[1])

        bytes_freed = 0
        for file_path, _, file_size in files_with_times:
            if bytes_freed >= bytes_needed:
                break

            if self._should_preserve_file(file_path, storage):
                continue

            try:
                file_path.unlink()
                bytes_freed += file_size
                logger.debug(f"Freed {file_size} bytes by removing {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")

        return bytes_freed

    def get_available_space(self) -> Dict[str, Any]:
        """Get available disk space information."""
        try:
            stat = shutil.disk_usage(self.base_path.parent)

            return {
                "total_bytes": stat.total,
                "used_bytes": stat.used,
                "free_bytes": stat.free,
                "free_gb": stat.free / (1024 ** 3),
                "usage_percentage": (stat.used / stat.total) * 100
            }

        except Exception as e:
            logger.error(f"Failed to get available space: {e}")
            raise StorageManagerError(f"Space check failed: {e}")

    def validate_storage_health(self) -> Dict[str, Any]:
        """Validate overall storage system health."""
        try:
            health_report = {
                "status": "healthy",
                "issues": [],
                "recommendations": [],
                "storage_usage": {},
                "disk_space": {}
            }

            # Check disk space
            space_info = self.get_available_space()
            health_report["disk_space"] = space_info

            if space_info["usage_percentage"] > 90:
                health_report["status"] = "warning"
                health_report["issues"].append("Disk usage above 90%")
                health_report["recommendations"].append("Run cleanup or add storage")

            # Check storage directory usage
            usage_stats = self.scan_storage_usage()
            health_report["storage_usage"] = usage_stats

            # Check for directories needing cleanup
            for storage_type, stats in usage_stats.items():
                if stats["needs_cleanup"]:
                    health_report["issues"].append(f"{storage_type} needs cleanup")
                    health_report["recommendations"].append(f"Run cleanup for {storage_type}")

            if health_report["issues"]:
                health_report["status"] = "warning" if health_report["status"] == "healthy" else "critical"

            return health_report

        except Exception as e:
            logger.error(f"Failed to validate storage health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": ["Storage health check failed"],
                "recommendations": ["Check storage system configuration"]
            }