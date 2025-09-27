"""
Media Browsing Service for file system exploration.
Provides functionality to scan and retrieve media files from the media directory.
"""
import os
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import logging
from datetime import datetime

from ..models.media_browsing import MediaFileInfo, MediaBrowseResponse, MediaFileDimensions
from ..lib.exceptions import MediaBrowsingError


logger = logging.getLogger(__name__)


class MediaBrowsingService:
    """Service for browsing and retrieving media file information"""

    # Supported file formats by type
    SUPPORTED_FORMATS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'},
        'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
    }

    def __init__(self, media_root: Optional[Path] = None):
        """
        Initialize MediaBrowsingService.

        Args:
            media_root: Optional custom media root directory
        """
        self.media_root = media_root or self._get_media_root()
        self._ensure_media_root_exists()

    def _get_media_root(self) -> Path:
        """Get the media root directory path"""
        # Look for media directory in current working directory or parent
        current_dir = Path.cwd()

        # Check current directory first
        media_dir = current_dir / "backend" / "media"
        if media_dir.exists():
            return media_dir

        media_dir = current_dir / "media"
        if media_dir.exists():
            return media_dir

        # Default fallback
        return current_dir / "backend" / "media"

    def _ensure_media_root_exists(self) -> None:
        """Ensure media root directory exists"""
        if not self.media_root.exists():
            logger.warning(f"Media root directory does not exist: {self.media_root}")
            # Create basic structure
            self.media_root.mkdir(parents=True, exist_ok=True)
            (self.media_root / "images").mkdir(exist_ok=True)
            (self.media_root / "videos").mkdir(exist_ok=True)
            (self.media_root / "audio").mkdir(exist_ok=True)
            logger.info(f"Created media directory structure at: {self.media_root}")

    async def browse_files(
        self,
        path: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> MediaBrowseResponse:
        """
        Browse media files in the specified directory.

        Args:
            path: Subdirectory path relative to media root
            file_type: Filter by file type (image, video, audio)
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            MediaBrowseResponse with filtered file list

        Raises:
            MediaBrowsingError: If path is invalid or access denied
        """
        try:
            # Resolve target directory
            if path:
                target_dir = self.media_root / path
                # Security check - ensure path stays within media root
                if not self._is_path_safe(target_dir):
                    raise MediaBrowsingError(f"Invalid path: {path}")
            else:
                target_dir = self.media_root
                path = ""

            if not target_dir.exists():
                raise MediaBrowsingError(f"Directory not found: {path}")

            if not target_dir.is_dir():
                raise MediaBrowsingError(f"Path is not a directory: {path}")

            # Scan files
            all_files = await self._scan_directory(target_dir)

            # Apply file type filter
            if file_type:
                if file_type not in self.SUPPORTED_FORMATS:
                    raise MediaBrowsingError(f"Unsupported file type: {file_type}")
                all_files = [f for f in all_files if f.type == file_type]

            # Sort by name for consistent ordering
            all_files.sort(key=lambda f: f.name.lower())

            # Apply pagination
            total_count = len(all_files)
            paginated_files = all_files[offset:offset + limit]

            # Determine parent path
            parent_path = None
            if path:
                parent_parts = Path(path).parts
                if len(parent_parts) > 1:
                    parent_path = str(Path(*parent_parts[:-1]))
                else:
                    parent_path = ""

            logger.info(f"Browsed {len(paginated_files)}/{total_count} files from: {target_dir}")

            return MediaBrowseResponse(
                files=paginated_files,
                total_count=total_count,
                current_path=path,
                parent_path=parent_path
            )

        except MediaBrowsingError:
            raise
        except Exception as e:
            logger.error(f"Error browsing files in {path}: {e}")
            raise MediaBrowsingError(f"Failed to browse directory: {e}")

    async def get_file_info(self, file_path: str) -> Optional[MediaFileInfo]:
        """
        Get detailed information about a specific media file.

        Args:
            file_path: Relative path to the media file

        Returns:
            MediaFileInfo if file exists and is supported, None otherwise

        Raises:
            MediaBrowsingError: If file access fails
        """
        try:
            full_path = self.media_root / file_path

            # Security check
            if not self._is_path_safe(full_path):
                raise MediaBrowsingError(f"Invalid file path: {file_path}")

            if not full_path.exists():
                return None

            if not full_path.is_file():
                raise MediaBrowsingError(f"Path is not a file: {file_path}")

            # Get file info
            file_info = await self._get_file_metadata(full_path, file_path)
            logger.info(f"Retrieved info for file: {file_path}")
            return file_info

        except MediaBrowsingError:
            raise
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            raise MediaBrowsingError(f"Failed to get file information: {e}")

    async def _scan_directory(self, directory: Path) -> List[MediaFileInfo]:
        """
        Scan directory for supported media files.

        Args:
            directory: Directory to scan

        Returns:
            List of MediaFileInfo objects
        """
        files = []
        unsupported_extensions = set()
        errors_count = 0

        try:
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        # Get relative path from media root
                        relative_path = item.relative_to(self.media_root)

                        # Check if file is supported
                        if self._is_supported_file(item):
                            try:
                                file_info = await self._get_file_metadata(item, str(relative_path))
                                if file_info:
                                    files.append(file_info)
                            except Exception as e:
                                logger.warning(f"Failed to get metadata for {item}: {e}")
                                errors_count += 1
                                continue
                        else:
                            # Track unsupported extensions for reporting
                            ext = item.suffix.lower()
                            if ext and ext not in unsupported_extensions:
                                unsupported_extensions.add(ext)

                    elif item.is_dir() and not item.name.startswith('.'):
                        # Recursively scan subdirectories
                        try:
                            subdirectory_files = await self._scan_directory(item)
                            files.extend(subdirectory_files)
                        except Exception as e:
                            logger.warning(f"Error scanning subdirectory {item}: {e}")
                            errors_count += 1

                except OSError as e:
                    logger.warning(f"Cannot access {item}: {e}")
                    errors_count += 1
                    continue

        except PermissionError as e:
            logger.warning(f"Permission denied accessing {directory}: {e}")
            raise MediaBrowsingError(f"Permission denied: {directory}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            raise MediaBrowsingError(f"Failed to scan directory: {e}")

        # Log summary of scan results
        if unsupported_extensions:
            logger.debug(f"Found unsupported file extensions in {directory}: {sorted(unsupported_extensions)}")

        if errors_count > 0:
            logger.info(f"Encountered {errors_count} errors while scanning {directory}")

        logger.debug(f"Successfully scanned {directory}: {len(files)} supported files found")
        return files

    async def _get_file_metadata(self, file_path: Path, relative_path: str) -> Optional[MediaFileInfo]:
        """
        Extract metadata from media file.

        Args:
            file_path: Full path to the file
            relative_path: Relative path from media root

        Returns:
            MediaFileInfo object or None if file is not supported
        """
        try:
            stat = file_path.stat()
            file_type = self._get_file_type(file_path)

            if not file_type:
                return None

            # Basic file info
            file_info = MediaFileInfo(
                path=str(relative_path),
                name=file_path.name,
                size=stat.st_size,
                type=file_type,
                format=file_path.suffix.lower().lstrip('.'),
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )

            # Add type-specific metadata
            if file_type == 'image':
                dimensions = await self._get_image_dimensions(file_path)
                if dimensions:
                    file_info.dimensions = dimensions
                file_info.thumbnail_url = f"/api/media/thumbnails/{relative_path}"

            elif file_type == 'video':
                video_info = await self._get_video_metadata(file_path)
                if video_info:
                    file_info.duration = video_info.get('duration')
                    dimensions_dict = video_info.get('dimensions')
                    if dimensions_dict and isinstance(dimensions_dict, dict):
                        file_info.dimensions = MediaFileDimensions(**dimensions_dict)

            elif file_type == 'audio':
                audio_info = await self._get_audio_metadata(file_path)
                if audio_info:
                    file_info.duration = audio_info.get('duration')

            return file_info

        except Exception as e:
            logger.warning(f"Failed to get metadata for {file_path}: {e}")
            return None

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file format is supported"""
        try:
            extension = file_path.suffix.lower()
            if not extension:
                logger.debug(f"File has no extension: {file_path}")
                return False

            for file_formats in self.SUPPORTED_FORMATS.values():
                if extension in file_formats:
                    return True

            logger.debug(f"Unsupported file format: {extension} for file: {file_path}")
            return False
        except Exception as e:
            logger.warning(f"Error checking file support for {file_path}: {e}")
            return False

    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """Get file type (image, video, audio) based on extension"""
        extension = file_path.suffix.lower()
        for file_type, formats in self.SUPPORTED_FORMATS.items():
            if extension in formats:
                return file_type
        return None

    def _is_path_safe(self, path: Path) -> bool:
        """Check if path is safe (within media root)"""
        try:
            # Resolve both paths to handle symlinks and .. components
            resolved_path = path.resolve()
            resolved_root = self.media_root.resolve()

            # Check if the resolved path is within the media root
            return resolved_path.is_relative_to(resolved_root)
        except (OSError, ValueError):
            return False

    async def _get_image_dimensions(self, file_path: Path) -> Optional[MediaFileDimensions]:
        """Get image dimensions using PIL"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return MediaFileDimensions(width=img.width, height=img.height)
        except Exception as e:
            logger.debug(f"Could not get image dimensions for {file_path}: {e}")
            return None

    async def _get_video_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get video metadata using ffprobe or similar"""
        try:
            # This would require ffmpeg/ffprobe to be installed
            # For now, return basic info
            logger.debug(f"Video metadata extraction not implemented for {file_path}")
            return {"duration": None, "dimensions": None}
        except Exception as e:
            logger.debug(f"Could not get video metadata for {file_path}: {e}")
            return None

    async def _get_audio_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get audio metadata"""
        try:
            # This would require audio processing libraries
            # For now, return basic info
            logger.debug(f"Audio metadata extraction not implemented for {file_path}")
            return {"duration": None}
        except Exception as e:
            logger.debug(f"Could not get audio metadata for {file_path}: {e}")
            return None