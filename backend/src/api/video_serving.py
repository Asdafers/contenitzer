"""
Video Serving API endpoints.
Handles video file download and streaming.
"""
import logging
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
import os
import mimetypes

from ..lib.database import get_db_session
from ..models.generated_video import GeneratedVideo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/videos", tags=["video-serving"])


@router.get("/{video_id}/download")
async def download_video(video_id: str):
    """
    Download generated video file.

    Returns the video file as a downloadable attachment.
    """
    try:
        video_uuid = uuid.UUID(video_id)

        with get_db_session() as db:
            video = db.query(GeneratedVideo).filter(
                GeneratedVideo.id == video_uuid
            ).first()

            if not video:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video {video_id} not found"
                )

            # Check if video is still being generated
            if video.generation_status.value != "COMPLETED":
                raise HTTPException(
                    status_code=202,
                    detail={
                        "message": "Video still being generated",
                        "status": video.generation_status.value
                    }
                )

            # Check if video file exists
            video_path = Path(video.file_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                raise HTTPException(
                    status_code=404,
                    detail="Video file not found on server"
                )

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(video_path))
            if not mime_type:
                mime_type = "video/mp4"

            # Generate filename for download
            safe_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.{video.format}"

            # Return file as download
            return FileResponse(
                path=str(video_path),
                media_type=mime_type,
                filename=filename,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(video_path.stat().st_size),
                    "Cache-Control": "public, max-age=3600",
                    "X-Content-Type-Options": "nosniff"
                }
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download_video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{video_id}/stream")
async def stream_video(video_id: str, request: Request):
    """
    Stream generated video file with HTTP range support.

    Supports partial content requests for video streaming.
    """
    try:
        video_uuid = uuid.UUID(video_id)

        with get_db_session() as db:
            video = db.query(GeneratedVideo).filter(
                GeneratedVideo.id == video_uuid
            ).first()

            if not video:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video {video_id} not found"
                )

            # Check if video is still being generated
            if video.generation_status.value != "COMPLETED":
                raise HTTPException(
                    status_code=202,
                    detail={
                        "message": "Video still being generated",
                        "status": video.generation_status.value
                    }
                )

            # Check if video file exists
            video_path = Path(video.file_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                raise HTTPException(
                    status_code=404,
                    detail="Video file not found on server"
                )

            # Get file info
            file_size = video_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(video_path))
            if not mime_type:
                mime_type = "video/mp4"

            # Handle range requests
            range_header = request.headers.get("Range")
            if range_header:
                return _handle_range_request(video_path, file_size, mime_type, range_header)

            # Return full video stream
            return _stream_full_video(video_path, file_size, mime_type)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in stream_video: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _handle_range_request(
    video_path: Path,
    file_size: int,
    mime_type: str,
    range_header: str
) -> StreamingResponse:
    """Handle HTTP range request for partial content."""
    try:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = range_header.replace("bytes=", "")
        range_parts = range_match.split("-")

        if len(range_parts) != 2:
            raise ValueError("Invalid range format")

        start = int(range_parts[0]) if range_parts[0] else 0
        end = int(range_parts[1]) if range_parts[1] else file_size - 1

        # Validate range
        if start >= file_size or end >= file_size or start > end:
            return Response(
                status_code=416,
                headers={
                    "Content-Range": f"bytes */{file_size}",
                    "Content-Type": mime_type
                }
            )

        # Calculate content length
        content_length = end - start + 1

        # Create streaming response
        def generate_chunk():
            with open(video_path, "rb") as video_file:
                video_file.seek(start)
                remaining = content_length
                chunk_size = 8192

                while remaining > 0:
                    chunk = video_file.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            generate_chunk(),
            status_code=206,
            headers={
                "Content-Type": mime_type,
                "Content-Length": str(content_length),
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600"
            }
        )

    except (ValueError, IndexError) as e:
        logger.warning(f"Invalid range request: {range_header}, error: {e}")
        # Return 400 for malformed range requests
        raise HTTPException(status_code=400, detail="Invalid range request")


def _stream_full_video(
    video_path: Path,
    file_size: int,
    mime_type: str
) -> StreamingResponse:
    """Stream the full video file."""
    def generate_full_video():
        with open(video_path, "rb") as video_file:
            chunk_size = 8192
            while True:
                chunk = video_file.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        generate_full_video(),
        status_code=200,
        headers={
            "Content-Type": mime_type,
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600"
        }
    )