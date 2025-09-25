"""
Static file serving configuration for media files.
Configures FastAPI static file mounts for video and media asset serving.
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def configure_static_file_serving(app: FastAPI, base_media_path: Path = None):
    """
    Configure static file serving for media files.

    Args:
        app: FastAPI application instance
        base_media_path: Base path for media files (defaults to 'media')
    """
    if base_media_path is None:
        base_media_path = Path("media")

    try:
        # Ensure media directories exist
        media_dirs = {
            "/media/videos": base_media_path / "videos",
            "/media/assets": base_media_path / "assets",
            "/media/stock": base_media_path / "stock"
        }

        for url_path, directory_path in media_dirs.items():
            directory_path.mkdir(parents=True, exist_ok=True)

            # Mount static files with custom StaticFiles class for better control
            app.mount(
                url_path,
                MediaStaticFiles(directory=str(directory_path)),
                name=f"media_{url_path.split('/')[-1]}"
            )

            logger.info(f"Mounted static files: {url_path} -> {directory_path}")

        # Add custom media serving endpoint for better control
        @app.get("/media/{file_type}/{filename:path}")
        async def serve_media_file(file_type: str, filename: str):
            """
            Custom media file serving with additional security and logging.
            """
            try:
                # Validate file type
                valid_types = ["videos", "assets", "stock"]
                if file_type not in valid_types:
                    raise HTTPException(status_code=404, detail="Invalid media type")

                # Construct file path
                file_path = base_media_path / file_type / filename

                # Security check - ensure file is within allowed directory
                if not _is_safe_path(base_media_path / file_type, file_path):
                    logger.warning(f"Unsafe file path access attempt: {file_path}")
                    raise HTTPException(status_code=403, detail="Access denied")

                # Check if file exists
                if not file_path.exists() or not file_path.is_file():
                    raise HTTPException(status_code=404, detail="File not found")

                # Log access for monitoring
                logger.debug(f"Serving media file: {file_path}")

                # Return file with appropriate headers
                return FileResponse(
                    path=str(file_path),
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "X-Content-Type-Options": "nosniff"
                    }
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error serving media file {file_type}/{filename}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        logger.error(f"Failed to configure static file serving: {e}")
        raise


class MediaStaticFiles(StaticFiles):
    """
    Custom StaticFiles class with enhanced security and logging for media files.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_response(self, path: str, scope):
        """Override to add custom handling for media files."""
        try:
            # Log access attempts for monitoring
            client_ip = scope.get("client", ["unknown"])[0]
            logger.debug(f"Media file request: {path} from {client_ip}")

            # Check file extension for allowed types
            allowed_extensions = {
                '.mp4', '.avi', '.mov', '.webm',  # Video files
                '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Image files
                '.mp3', '.wav', '.ogg', '.m4a',  # Audio files
                '.json', '.txt'  # Text/data files
            }

            file_extension = Path(path).suffix.lower()
            if file_extension and file_extension not in allowed_extensions:
                logger.warning(f"Blocked request for disallowed file type: {path}")
                return self._create_error_response(403, "File type not allowed")

            # Call parent implementation
            response = await super().get_response(path, scope)

            # Add custom headers for media files
            if hasattr(response, 'headers'):
                response.headers["X-Content-Type-Options"] = "nosniff"

                # Add different cache policies based on file type
                if file_extension in {'.mp4', '.avi', '.mov', '.webm'}:
                    response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
                elif file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
                    response.headers["Cache-Control"] = "public, max-age=3600"   # 1 hour
                else:
                    response.headers["Cache-Control"] = "public, max-age=1800"   # 30 minutes

            return response

        except Exception as e:
            logger.error(f"Error in media static file serving: {e}")
            return self._create_error_response(500, "Internal server error")

    def _create_error_response(self, status_code: int, message: str):
        """Create a simple error response."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status_code,
            content={"error": message}
        )


def _is_safe_path(base_path: Path, file_path: Path) -> bool:
    """
    Check if the file path is safe (within the base directory).

    Args:
        base_path: Base directory path
        file_path: File path to check

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve both paths to handle symlinks and relative paths
        base_resolved = base_path.resolve()
        file_resolved = file_path.resolve()

        # Check if file path is within base path
        return str(file_resolved).startswith(str(base_resolved))

    except Exception as e:
        logger.warning(f"Path safety check failed: {e}")
        return False


def get_media_file_info(file_path: Path) -> dict:
    """
    Get information about a media file.

    Args:
        file_path: Path to the media file

    Returns:
        Dictionary with file information
    """
    try:
        if not file_path.exists():
            return {"exists": False}

        stat = file_path.stat()

        return {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "extension": file_path.suffix.lower(),
            "name": file_path.name
        }

    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {"exists": False, "error": str(e)}


def cleanup_temp_files(base_media_path: Path = None, max_age_hours: int = 24):
    """
    Clean up temporary media files older than specified age.

    Args:
        base_media_path: Base path for media files
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        Number of files cleaned up
    """
    if base_media_path is None:
        base_media_path = Path("media")

    try:
        import time
        from datetime import datetime, timedelta

        cutoff_time = time.time() - (max_age_hours * 3600)
        temp_dir = base_media_path / "assets" / "temp"

        if not temp_dir.exists():
            return 0

        cleaned_count = 0
        for temp_file in temp_dir.rglob("*"):
            if temp_file.is_file():
                try:
                    if temp_file.stat().st_mtime < cutoff_time:
                        temp_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_file}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} temporary media files")

        return cleaned_count

    except Exception as e:
        logger.error(f"Temp file cleanup failed: {e}")
        return 0