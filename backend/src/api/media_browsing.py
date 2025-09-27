"""
Media Browsing API endpoints for file system exploration.
Provides functionality to browse and list media files from the media directory.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from ..models.media_browsing import MediaFileInfo, MediaBrowseResponse, MediaSearchRequest
from ..services.media_browsing_service import MediaBrowsingService
from ..lib.exceptions import MediaBrowsingError

logger = logging.getLogger(__name__)
router = APIRouter()




@router.get("/api/media/browse", response_model=MediaBrowseResponse)
async def browse_media_files(
    path: Optional[str] = Query(None, description="Subdirectory path to browse"),
    file_type: Optional[str] = Query(None, description="Filter by file type: image, video, audio"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of files to return"),
    offset: int = Query(0, ge=0, description="Number of files to skip")
) -> MediaBrowseResponse:
    """
    Browse media files in the media directory.

    Args:
        path: Optional subdirectory path relative to media root
        file_type: Optional filter for file type (image, video, audio)
        limit: Maximum number of files to return (1-200)
        offset: Number of files to skip for pagination

    Returns:
        MediaBrowseResponse with file list and metadata

    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        service = MediaBrowsingService()

        # Browse files with filters
        result = await service.browse_files(
            path=path,
            file_type=file_type,
            limit=limit,
            offset=offset
        )

        logger.info(f"Successfully browsed {len(result.files)} files from path: {result.current_path}")
        return result

    except MediaBrowsingError as e:
        logger.error(f"Media browsing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in browse_media_files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/media/info/{file_path:path}", response_model=MediaFileInfo)
async def get_media_file_info(file_path: str) -> MediaFileInfo:
    """
    Get detailed information about a specific media file.

    Args:
        file_path: Relative path to the media file

    Returns:
        MediaFileInfo with detailed file metadata

    Raises:
        HTTPException: 404 if file not found, 400 for invalid path, 500 for server errors
    """
    try:
        service = MediaBrowsingService()

        file_info = await service.get_file_info(file_path)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        logger.info(f"Retrieved info for file: {file_path}")
        return file_info

    except MediaBrowsingError as e:
        logger.error(f"Media file info error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_media_file_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")