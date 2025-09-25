"""
FFmpeg error handling utilities.
Provides comprehensive error handling for FFmpeg operations.
"""
import logging
import re
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FFmpegErrorType(str, Enum):
    """FFmpeg error categories"""
    CODEC_ERROR = "codec_error"
    FILE_ERROR = "file_error"
    FORMAT_ERROR = "format_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class FFmpegError:
    """Structured FFmpeg error"""
    error_type: FFmpegErrorType
    message: str
    original_error: str
    file_path: Optional[str] = None
    suggested_action: Optional[str] = None
    is_retryable: bool = False


class FFmpegErrorHandler:
    """Handles FFmpeg errors with retry logic and fallbacks"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_patterns = self._build_error_patterns()

    def parse_ffmpeg_error(self, error_output: str, file_path: str = None) -> FFmpegError:
        """Parse FFmpeg error output into structured error"""
        error_output = error_output.lower()

        for pattern, error_info in self.error_patterns.items():
            if re.search(pattern, error_output):
                return FFmpegError(
                    error_type=error_info["type"],
                    message=error_info["message"],
                    original_error=error_output,
                    file_path=file_path,
                    suggested_action=error_info.get("action"),
                    is_retryable=error_info.get("retryable", False)
                )

        return FFmpegError(
            error_type=FFmpegErrorType.UNKNOWN_ERROR,
            message="Unknown FFmpeg error occurred",
            original_error=error_output,
            file_path=file_path,
            suggested_action="Check FFmpeg installation and file permissions",
            is_retryable=True
        )

    def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute FFmpeg operation with retry logic"""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)

            except Exception as e:
                last_error = e
                error_str = str(e)

                if attempt < self.max_retries:
                    ffmpeg_error = self.parse_ffmpeg_error(error_str)

                    if ffmpeg_error.is_retryable:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(f"FFmpeg operation failed (attempt {attempt + 1}), retrying in {delay}s: {error_str}")
                        time.sleep(delay)
                        continue

                    logger.error(f"Non-retryable FFmpeg error: {error_str}")
                    break

                logger.error(f"FFmpeg operation failed after {self.max_retries} retries: {error_str}")
                break

        raise last_error

    def _build_error_patterns(self) -> Dict[str, Dict]:
        """Build regex patterns for common FFmpeg errors"""
        return {
            r"no such file or directory": {
                "type": FFmpegErrorType.FILE_ERROR,
                "message": "Input file not found",
                "action": "Check if the input file exists and path is correct",
                "retryable": False
            },
            r"permission denied": {
                "type": FFmpegErrorType.PERMISSION_ERROR,
                "message": "Permission denied accessing file",
                "action": "Check file permissions and directory access",
                "retryable": False
            },
            r"codec.*not found": {
                "type": FFmpegErrorType.CODEC_ERROR,
                "message": "Required codec not available",
                "action": "Install missing codec or use different format",
                "retryable": False
            },
            r"invalid data found": {
                "type": FFmpegErrorType.FORMAT_ERROR,
                "message": "Invalid or corrupted media file",
                "action": "Check if input file is valid and not corrupted",
                "retryable": False
            },
            r"disk full|no space left": {
                "type": FFmpegErrorType.RESOURCE_ERROR,
                "message": "Insufficient disk space",
                "action": "Free up disk space and retry",
                "retryable": True
            },
            r"memory.*allocation failed": {
                "type": FFmpegErrorType.RESOURCE_ERROR,
                "message": "Insufficient memory",
                "action": "Reduce video resolution or close other applications",
                "retryable": True
            }
        }


# Global error handler instance
ffmpeg_error_handler = FFmpegErrorHandler()


def handle_ffmpeg_error(error: Exception, file_path: str = None) -> FFmpegError:
    """Handle FFmpeg error and return structured error info"""
    return ffmpeg_error_handler.parse_ffmpeg_error(str(error), file_path)


def execute_ffmpeg_with_fallback(primary_operation: Callable, fallback_operation: Callable = None, *args, **kwargs) -> Any:
    """Execute FFmpeg operation with fallback"""
    try:
        return ffmpeg_error_handler.execute_with_retry(primary_operation, *args, **kwargs)
    except Exception as e:
        logger.error(f"Primary FFmpeg operation failed: {e}")

        if fallback_operation:
            logger.info("Attempting fallback operation")
            try:
                return fallback_operation(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback operation also failed: {fallback_error}")

        raise e