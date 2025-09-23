import os
import shutil
import logging
from typing import Optional, List
from pathlib import Path
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StorageManager:
    """File storage management for media assets"""

    def __init__(self, base_path: str = "/tmp/contentizer"):
        self.base_path = Path(base_path)
        self.audio_path = self.base_path / "audio"
        self.images_path = self.base_path / "images"
        self.videos_path = self.base_path / "videos"
        self.composed_path = self.base_path / "composed"
        self.temp_path = self.base_path / "temp"

        # Create directories
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        directories = [
            self.base_path,
            self.audio_path,
            self.images_path,
            self.videos_path,
            self.composed_path,
            self.temp_path
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise

    def get_audio_path(self, asset_id: str) -> str:
        """Get path for audio asset"""
        return str(self.audio_path / f"{asset_id}.mp3")

    def get_image_path(self, asset_id: str) -> str:
        """Get path for image asset"""
        return str(self.images_path / f"{asset_id}.jpg")

    def get_video_path(self, asset_id: str) -> str:
        """Get path for video asset"""
        return str(self.videos_path / f"{asset_id}.mp4")

    def get_composed_path(self, video_id: str) -> str:
        """Get path for composed video"""
        return str(self.composed_path / f"{video_id}.mp4")

    def get_temp_path(self, filename: str) -> str:
        """Get path for temporary file"""
        return str(self.temp_path / filename)

    def save_file(self, content: bytes, file_path: str) -> bool:
        """Save file content to specified path"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'wb') as f:
                f.write(content)

            logger.info(f"Saved file: {file_path} ({len(content)} bytes)")
            return True

        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return False

    def read_file(self, file_path: str) -> Optional[bytes]:
        """Read file content from path"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            logger.debug(f"Read file: {file_path} ({len(content)} bytes)")
            return content

        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            return None

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()

    def list_files(self, directory_type: str) -> List[str]:
        """List files in a specific directory type"""
        directory_map = {
            "audio": self.audio_path,
            "images": self.images_path,
            "videos": self.videos_path,
            "composed": self.composed_path,
            "temp": self.temp_path
        }

        if directory_type not in directory_map:
            logger.error(f"Unknown directory type: {directory_type}")
            return []

        try:
            directory = directory_map[directory_type]
            files = [str(f) for f in directory.iterdir() if f.is_file()]
            logger.debug(f"Listed {len(files)} files in {directory_type}")
            return files

        except Exception as e:
            logger.error(f"Failed to list files in {directory_type}: {e}")
            return []

    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0

            for file_path in self.temp_path.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} temporary files older than {max_age_hours} hours")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            return 0

    def cleanup_project_files(self, project_id: str):
        """Clean up all files associated with a project"""
        try:
            deleted_files = []

            # Search for files with project ID in the name
            for directory in [self.audio_path, self.images_path, self.videos_path, self.composed_path]:
                for file_path in directory.glob(f"*{project_id}*"):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_files.append(str(file_path))

            logger.info(f"Cleaned up {len(deleted_files)} files for project {project_id}")
            return deleted_files

        except Exception as e:
            logger.error(f"Failed to cleanup project files for {project_id}: {e}")
            return []

    def get_storage_stats(self) -> dict:
        """Get storage usage statistics"""
        try:
            stats = {}

            for name, path in [
                ("audio", self.audio_path),
                ("images", self.images_path),
                ("videos", self.videos_path),
                ("composed", self.composed_path),
                ("temp", self.temp_path)
            ]:
                files = list(path.glob("*"))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())

                stats[name] = {
                    "file_count": file_count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }

            # Overall stats
            stats["total"] = {
                "file_count": sum(s["file_count"] for s in stats.values()),
                "total_size_bytes": sum(s["total_size_bytes"] for s in stats.values()),
                "total_size_mb": sum(s["total_size_mb"] for s in stats.values())
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}


# Global storage manager instance
storage_manager = StorageManager(
    base_path=os.getenv("STORAGE_PATH", "/tmp/contentizer")
)