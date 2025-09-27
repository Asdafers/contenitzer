"""
Pydantic models for media browsing functionality.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MediaFileDimensions(BaseModel):
    """Media file dimensions"""
    width: int
    height: int


class MediaFileInfo(BaseModel):
    """Information about a media file"""
    path: str = Field(..., description="Relative path from media root")
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="File type: image, video, or audio")
    format: str = Field(..., description="File format/extension")
    created_at: str = Field(..., description="Creation timestamp")
    modified_at: str = Field(..., description="Last modified timestamp")
    dimensions: Optional[MediaFileDimensions] = Field(None, description="Image/video dimensions")
    duration: Optional[float] = Field(None, description="Duration in seconds for video/audio")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL if available")


class MediaBrowseResponse(BaseModel):
    """Response for media browsing requests"""
    files: List[MediaFileInfo] = Field(default_factory=list, description="List of media files")
    total_count: int = Field(..., description="Total number of files")
    current_path: str = Field(..., description="Current directory path")
    parent_path: Optional[str] = Field(None, description="Parent directory path")


class MediaSearchRequest(BaseModel):
    """Request for searching media files"""
    query: str = Field(..., description="Search query")
    file_type: Optional[str] = Field(None, description="Filter by file type")
    limit: int = Field(50, ge=1, le=200, description="Maximum results")
    offset: int = Field(0, ge=0, description="Results offset")