"""
File validation utilities for media files.
Provides comprehensive validation for image, video, and audio files.
"""
import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Set, Tuple, List
import logging

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Exception raised when file validation fails"""
    pass


class FileValidator:
    """Utility class for validating media files"""

    # File size limits (in bytes)
    MAX_FILE_SIZES = {
        'image': 50 * 1024 * 1024,  # 50MB
        'video': 500 * 1024 * 1024,  # 500MB
        'audio': 100 * 1024 * 1024,  # 100MB
    }

    # Supported formats based on user requirements
    SUPPORTED_FORMATS = {
        'image': {'.jpg', '.jpeg', '.png'},  # User specified JPG, PNG
        'video': {'.mp4'},  # User specified MP4
        'audio': {'.mp3', '.wav', '.aac', '.ogg'}  # Common audio formats
    }

    # MIME type mappings
    MIME_TYPE_MAPPING = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.aac': 'audio/aac',
        '.ogg': 'audio/ogg'
    }

    @classmethod
    def validate_file(cls, file_path: Path) -> Dict[str, Any]:
        """
        Perform comprehensive file validation.

        Args:
            file_path: Path to the file to validate

        Returns:
            Dictionary with validation results and file metadata

        Raises:
            FileValidationError: If validation fails
        """
        if not file_path.exists():
            raise FileValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")

        # Get basic file info
        file_info = cls._get_basic_file_info(file_path)

        # Validate file format
        cls._validate_format(file_path, file_info['type'])

        # Validate file size
        cls._validate_file_size(file_path, file_info['type'])

        # Validate file integrity
        cls._validate_file_integrity(file_path, file_info['type'])

        logger.info(f"File validation passed: {file_path}")
        return file_info

    @classmethod
    def _get_basic_file_info(cls, file_path: Path) -> Dict[str, Any]:
        """Get basic file information"""
        stat = file_path.stat()
        extension = file_path.suffix.lower()

        # Determine file type
        file_type = cls._get_file_type(extension)
        if not file_type:
            raise FileValidationError(f"Unsupported file extension: {extension}")

        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': stat.st_size,
            'type': file_type,
            'extension': extension,
            'mime_type': cls.MIME_TYPE_MAPPING.get(extension, 'application/octet-stream'),
            'modified': stat.st_mtime
        }

    @classmethod
    def _get_file_type(cls, extension: str) -> Optional[str]:
        """Determine file type from extension"""
        for file_type, extensions in cls.SUPPORTED_FORMATS.items():
            if extension in extensions:
                return file_type
        return None

    @classmethod
    def _validate_format(cls, file_path: Path, file_type: str) -> None:
        """Validate file format is supported"""
        extension = file_path.suffix.lower()
        supported_extensions = cls.SUPPORTED_FORMATS.get(file_type, set())

        if extension not in supported_extensions:
            raise FileValidationError(
                f"Unsupported {file_type} format: {extension}. "
                f"Supported formats: {', '.join(supported_extensions)}"
            )

    @classmethod
    def _validate_file_size(cls, file_path: Path, file_type: str) -> None:
        """Validate file size is within limits with performance optimization"""
        try:
            # Use stat to get file size efficiently
            stat_result = file_path.stat()
            file_size = stat_result.st_size

            # Quick check for empty files
            if file_size == 0:
                raise FileValidationError("File is empty")

            # Check minimum file size (avoid corrupt files)
            min_size = 100  # 100 bytes minimum
            if file_size < min_size:
                raise FileValidationError(f"File too small: {file_size} bytes (minimum {min_size} bytes)")

            # Check maximum file size
            max_size = cls.MAX_FILE_SIZES.get(file_type, float('inf'))
            if file_size > max_size:
                max_size_mb = max_size / (1024 * 1024)
                actual_size_mb = file_size / (1024 * 1024)
                raise FileValidationError(
                    f"File too large: {actual_size_mb:.1f}MB exceeds limit of {max_size_mb:.1f}MB"
                )

            # Performance optimization: warn about large files that might be slow to process
            if file_type == 'video' and file_size > 100 * 1024 * 1024:  # 100MB
                logger.warning(f"Large video file detected: {actual_size_mb:.1f}MB - processing may be slow")
            elif file_type == 'image' and file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Large image file detected: {actual_size_mb:.1f}MB - processing may be slow")

        except OSError as e:
            raise FileValidationError(f"Cannot access file size: {e}")
        except Exception as e:
            raise FileValidationError(f"File size validation error: {e}")

    @classmethod
    def _validate_file_integrity(cls, file_path: Path, file_type: str) -> None:
        """Validate file integrity based on type"""
        try:
            if file_type == 'image':
                cls._validate_image_integrity(file_path)
            elif file_type == 'video':
                cls._validate_video_integrity(file_path)
            elif file_type == 'audio':
                cls._validate_audio_integrity(file_path)
        except Exception as e:
            raise FileValidationError(f"File integrity check failed: {e}")

    @classmethod
    def _validate_image_integrity(cls, file_path: Path) -> None:
        """Validate image file integrity"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                # Try to load the image to verify it's valid
                img.verify()

                # Reopen to get dimensions (verify() closes the image)
                with Image.open(file_path) as img2:
                    width, height = img2.size

                    # Check minimum dimensions
                    if width < 1 or height < 1:
                        raise FileValidationError("Invalid image dimensions")

                    # Check maximum dimensions (prevent extremely large images)
                    max_dimension = 10000  # 10k pixels
                    if width > max_dimension or height > max_dimension:
                        raise FileValidationError(
                            f"Image too large: {width}x{height} exceeds {max_dimension}px limit"
                        )

        except ImportError:
            logger.warning("PIL not available, skipping image integrity check")
        except Exception as e:
            raise FileValidationError(f"Invalid image file: {e}")

    @classmethod
    def _validate_video_integrity(cls, file_path: Path) -> None:
        """Validate video file integrity"""
        # Basic validation - check if file starts with expected video headers
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)

            # Check for common video file signatures
            if file_path.suffix.lower() == '.mp4':
                # MP4 files typically start with ftyp box
                if not (b'ftyp' in header[:12] or header.startswith(b'\x00\x00\x00')):
                    raise FileValidationError("Invalid MP4 file format")

        except Exception as e:
            raise FileValidationError(f"Invalid video file: {e}")

    @classmethod
    def _validate_audio_integrity(cls, file_path: Path) -> None:
        """Validate audio file integrity"""
        extension = file_path.suffix.lower()

        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)

            # Check for common audio file signatures
            if extension == '.mp3':
                # MP3 files start with ID3 tag or frame sync
                if not (header.startswith(b'ID3') or header.startswith(b'\xff\xfb')):
                    raise FileValidationError("Invalid MP3 file format")
            elif extension == '.wav':
                # WAV files start with RIFF header
                if not header.startswith(b'RIFF'):
                    raise FileValidationError("Invalid WAV file format")

        except Exception as e:
            raise FileValidationError(f"Invalid audio file: {e}")

    @classmethod
    def get_supported_formats(cls) -> Dict[str, Set[str]]:
        """Get all supported file formats"""
        return cls.SUPPORTED_FORMATS.copy()

    @classmethod
    def is_supported_format(cls, file_path: Path) -> bool:
        """Check if file format is supported"""
        extension = file_path.suffix.lower()
        for extensions in cls.SUPPORTED_FORMATS.values():
            if extension in extensions:
                return True
        return False

    @classmethod
    def get_file_type_from_path(cls, file_path: Path) -> Optional[str]:
        """Get file type from file path"""
        extension = file_path.suffix.lower()
        return cls._get_file_type(extension)

    @classmethod
    def validate_file_name(cls, filename: str) -> None:
        """Validate filename for security and compatibility"""
        if not filename:
            raise FileValidationError("Filename cannot be empty")

        if len(filename) > 255:
            raise FileValidationError("Filename too long (max 255 characters)")

        # Check for dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
        for char in dangerous_chars:
            if char in filename:
                raise FileValidationError(f"Invalid character in filename: {char}")

        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            raise FileValidationError(f"Reserved filename: {filename}")

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe usage"""
        # Replace dangerous characters with underscores
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')

        # Limit length
        if len(sanitized) > 255:
            name = Path(sanitized).stem[:240]  # Leave room for extension
            ext = Path(sanitized).suffix
            sanitized = f"{name}{ext}"

        return sanitized

    @classmethod
    def validate_multiple_files(cls, file_paths: List[Path]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Validate multiple files efficiently for batch operations.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Tuple of (successful_validations, failed_validations)
        """
        successful = []
        failed = []

        logger.info(f"Starting batch validation of {len(file_paths)} files")

        for file_path in file_paths:
            try:
                # Quick existence check first (most efficient)
                if not file_path.exists():
                    failed.append({
                        'path': str(file_path),
                        'error': 'File not found'
                    })
                    continue

                # Validate file
                file_info = cls.validate_file(file_path)
                successful.append(file_info)

            except FileValidationError as e:
                failed.append({
                    'path': str(file_path),
                    'error': str(e)
                })
            except Exception as e:
                failed.append({
                    'path': str(file_path),
                    'error': f'Unexpected error: {e}'
                })

        success_rate = len(successful) / len(file_paths) * 100 if file_paths else 0
        logger.info(f"Batch validation complete: {len(successful)}/{len(file_paths)} files valid ({success_rate:.1f}%)")

        return successful, failed

    @classmethod
    def get_validation_summary(cls, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Get validation summary without full validation for performance preview.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Summary dictionary with counts and potential issues
        """
        summary = {
            'total_files': len(file_paths),
            'by_type': {'image': 0, 'video': 0, 'audio': 0, 'unknown': 0},
            'total_size_mb': 0,
            'potential_issues': [],
            'large_files': []
        }

        for file_path in file_paths:
            try:
                if not file_path.exists():
                    continue

                # Get basic file info efficiently
                stat_result = file_path.stat()
                file_size = stat_result.st_size
                file_type = cls._get_file_type(file_path.suffix.lower())

                if file_type:
                    summary['by_type'][file_type] += 1
                else:
                    summary['by_type']['unknown'] += 1

                summary['total_size_mb'] += file_size / (1024 * 1024)

                # Check for potential issues
                if file_size > cls.MAX_FILE_SIZES.get(file_type or 'unknown', float('inf')):
                    summary['potential_issues'].append(f'File too large: {file_path.name}')

                if file_size > 50 * 1024 * 1024:  # 50MB
                    summary['large_files'].append({
                        'name': file_path.name,
                        'size_mb': file_size / (1024 * 1024)
                    })

            except Exception:
                summary['potential_issues'].append(f'Cannot access: {file_path.name}')

        return summary


class SecurityValidator:
    """Additional security validation for uploaded files"""

    @classmethod
    def check_path_traversal(cls, file_path: str, base_path: Path) -> None:
        """Check for path traversal attempts"""
        try:
            resolved_path = (base_path / file_path).resolve()
            if not resolved_path.is_relative_to(base_path.resolve()):
                raise FileValidationError("Path traversal attempt detected")
        except (OSError, ValueError) as e:
            raise FileValidationError(f"Invalid file path: {e}")

    @classmethod
    def validate_content_type(cls, file_path: Path, expected_type: str) -> None:
        """Validate file content matches expected type"""
        actual_type = FileValidator.get_file_type_from_path(file_path)
        if actual_type != expected_type:
            raise FileValidationError(
                f"File type mismatch: expected {expected_type}, got {actual_type}"
            )