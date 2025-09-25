"""
Video file validation utilities.
Provides comprehensive validation for video files used in the system.
"""
import logging
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .ffmpeg_utils import probe_video, is_ffmpeg_available

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation strictness levels"""
    BASIC = "basic"      # File exists and has video extension
    FORMAT = "format"    # Basic + format validation
    FULL = "full"        # Format + detailed technical validation


class ValidationResult:
    """Video validation result"""

    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
        logger.debug(f"Validation error: {message}")

    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
        logger.debug(f"Validation warning: {message}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


@dataclass
class VideoRequirements:
    """Video file requirements"""
    max_duration_seconds: Optional[int] = 300  # 5 minutes
    min_duration_seconds: Optional[int] = 1
    max_width: Optional[int] = 1920
    max_height: Optional[int] = 1080
    min_width: Optional[int] = 320
    min_height: Optional[int] = 240
    max_file_size_mb: Optional[int] = 100
    allowed_formats: List[str] = None
    required_codecs: List[str] = None

    def __post_init__(self):
        if self.allowed_formats is None:
            self.allowed_formats = ['mp4', 'avi', 'mov', 'webm']
        if self.required_codecs is None:
            self.required_codecs = ['h264', 'h265', 'vp8', 'vp9']


class VideoValidator:
    """Comprehensive video file validator"""

    def __init__(self, requirements: VideoRequirements = None):
        """Initialize validator with requirements"""
        self.requirements = requirements or VideoRequirements()
        self.ffmpeg_available = is_ffmpeg_available()

        if not self.ffmpeg_available:
            logger.warning("FFmpeg not available - validation will be limited")

    def validate_video(
        self,
        video_path: Path,
        level: ValidationLevel = ValidationLevel.FULL
    ) -> ValidationResult:
        """
        Validate video file

        Args:
            video_path: Path to video file
            level: Validation level

        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult()

        try:
            # Basic validation
            self._validate_file_exists(video_path, result)
            if not result.is_valid:
                return result

            self._validate_file_extension(video_path, result)
            self._validate_file_size(video_path, result)

            if level == ValidationLevel.BASIC:
                return result

            # Format validation
            self._validate_mime_type(video_path, result)

            if level == ValidationLevel.FORMAT or not self.ffmpeg_available:
                return result

            # Full validation with FFmpeg
            self._validate_with_ffmpeg(video_path, result)

        except Exception as e:
            result.add_error(f"Validation failed with error: {str(e)}")
            logger.error(f"Video validation error for {video_path}: {e}")

        return result

    def validate_video_batch(
        self,
        video_paths: List[Path],
        level: ValidationLevel = ValidationLevel.FULL
    ) -> Dict[str, ValidationResult]:
        """Validate multiple video files"""
        results = {}

        for video_path in video_paths:
            try:
                results[str(video_path)] = self.validate_video(video_path, level)
            except Exception as e:
                result = ValidationResult()
                result.add_error(f"Batch validation failed: {str(e)}")
                results[str(video_path)] = result

        return results

    def _validate_file_exists(self, video_path: Path, result: ValidationResult):
        """Validate file exists and is readable"""
        if not video_path.exists():
            result.add_error(f"Video file does not exist: {video_path}")
            return

        if not video_path.is_file():
            result.add_error(f"Path is not a file: {video_path}")
            return

        try:
            # Check if file is readable
            with open(video_path, 'rb') as f:
                f.read(1024)  # Read first KB
        except (IOError, OSError) as e:
            result.add_error(f"Cannot read video file: {str(e)}")

    def _validate_file_extension(self, video_path: Path, result: ValidationResult):
        """Validate file extension"""
        extension = video_path.suffix.lower().lstrip('.')

        if not extension:
            result.add_error("Video file has no extension")
            return

        if extension not in self.requirements.allowed_formats:
            result.add_error(
                f"Unsupported video format: {extension}. "
                f"Allowed: {', '.join(self.requirements.allowed_formats)}"
            )

    def _validate_file_size(self, video_path: Path, result: ValidationResult):
        """Validate file size"""
        try:
            file_size_bytes = video_path.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)

            result.metadata['file_size_mb'] = round(file_size_mb, 2)

            if self.requirements.max_file_size_mb:
                if file_size_mb > self.requirements.max_file_size_mb:
                    result.add_error(
                        f"File size {file_size_mb:.1f}MB exceeds maximum "
                        f"{self.requirements.max_file_size_mb}MB"
                    )

            # Warn about very small files
            if file_size_mb < 0.1:
                result.add_warning("Video file is very small (< 0.1MB)")

        except OSError as e:
            result.add_error(f"Cannot get file size: {str(e)}")

    def _validate_mime_type(self, video_path: Path, result: ValidationResult):
        """Validate MIME type"""
        mime_type, _ = mimetypes.guess_type(str(video_path))

        if mime_type:
            result.metadata['mime_type'] = mime_type

            if not mime_type.startswith('video/'):
                result.add_warning(f"MIME type is not video/*: {mime_type}")
        else:
            result.add_warning("Could not determine MIME type")

    def _validate_with_ffmpeg(self, video_path: Path, result: ValidationResult):
        """Validate video using FFmpeg probe"""
        try:
            video_info = probe_video(str(video_path))

            if not video_info:
                result.add_error("FFmpeg could not read video file")
                return

            # Extract and validate video properties
            self._validate_duration(video_info, result)
            self._validate_resolution(video_info, result)
            self._validate_codec(video_info, result)
            self._validate_streams(video_info, result)

            # Store metadata
            result.metadata.update({
                'duration': video_info.get('duration'),
                'width': video_info.get('width'),
                'height': video_info.get('height'),
                'codec': video_info.get('codec_name'),
                'bitrate': video_info.get('bit_rate'),
                'fps': video_info.get('r_frame_rate'),
                'has_audio': video_info.get('has_audio', False)
            })

        except Exception as e:
            result.add_error(f"FFmpeg validation failed: {str(e)}")

    def _validate_duration(self, video_info: Dict[str, Any], result: ValidationResult):
        """Validate video duration"""
        duration = video_info.get('duration')
        if not duration:
            result.add_warning("Could not determine video duration")
            return

        try:
            duration_seconds = float(duration)

            if self.requirements.max_duration_seconds:
                if duration_seconds > self.requirements.max_duration_seconds:
                    result.add_error(
                        f"Duration {duration_seconds:.1f}s exceeds maximum "
                        f"{self.requirements.max_duration_seconds}s"
                    )

            if self.requirements.min_duration_seconds:
                if duration_seconds < self.requirements.min_duration_seconds:
                    result.add_error(
                        f"Duration {duration_seconds:.1f}s below minimum "
                        f"{self.requirements.min_duration_seconds}s"
                    )

        except (ValueError, TypeError):
            result.add_warning(f"Invalid duration format: {duration}")

    def _validate_resolution(self, video_info: Dict[str, Any], result: ValidationResult):
        """Validate video resolution"""
        width = video_info.get('width')
        height = video_info.get('height')

        if not width or not height:
            result.add_warning("Could not determine video resolution")
            return

        try:
            width, height = int(width), int(height)

            # Check maximum resolution
            if self.requirements.max_width and width > self.requirements.max_width:
                result.add_error(f"Width {width} exceeds maximum {self.requirements.max_width}")

            if self.requirements.max_height and height > self.requirements.max_height:
                result.add_error(f"Height {height} exceeds maximum {self.requirements.max_height}")

            # Check minimum resolution
            if self.requirements.min_width and width < self.requirements.min_width:
                result.add_error(f"Width {width} below minimum {self.requirements.min_width}")

            if self.requirements.min_height and height < self.requirements.min_height:
                result.add_error(f"Height {height} below minimum {self.requirements.min_height}")

            # Aspect ratio warning
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                result.add_warning(f"Unusual aspect ratio: {aspect_ratio:.2f}")

        except (ValueError, TypeError):
            result.add_warning(f"Invalid resolution values: {width}x{height}")

    def _validate_codec(self, video_info: Dict[str, Any], result: ValidationResult):
        """Validate video codec"""
        codec = video_info.get('codec_name', '').lower()

        if not codec:
            result.add_warning("Could not determine video codec")
            return

        if self.requirements.required_codecs:
            if codec not in self.requirements.required_codecs:
                result.add_warning(
                    f"Codec {codec} not in preferred list: "
                    f"{', '.join(self.requirements.required_codecs)}"
                )

    def _validate_streams(self, video_info: Dict[str, Any], result: ValidationResult):
        """Validate video streams"""
        # Check for video stream
        if not video_info.get('width') or not video_info.get('height'):
            result.add_error("No valid video stream found")

        # Warn if no audio stream for video files that should have audio
        has_audio = video_info.get('has_audio', False)
        if not has_audio:
            result.add_warning("Video has no audio stream")


# Default validator instance
default_validator = VideoValidator()


def validate_video_file(
    video_path: Path,
    level: ValidationLevel = ValidationLevel.FULL,
    requirements: VideoRequirements = None
) -> ValidationResult:
    """
    Convenience function to validate a single video file

    Args:
        video_path: Path to video file
        level: Validation level
        requirements: Custom requirements (uses default if None)

    Returns:
        ValidationResult
    """
    if requirements:
        validator = VideoValidator(requirements)
    else:
        validator = default_validator

    return validator.validate_video(video_path, level)


def is_valid_video_file(video_path: Path, level: ValidationLevel = ValidationLevel.BASIC) -> bool:
    """
    Quick check if video file is valid

    Args:
        video_path: Path to video file
        level: Validation level

    Returns:
        True if valid, False otherwise
    """
    result = validate_video_file(video_path, level)
    return result.is_valid