"""
Media Assets API endpoints.
Handles serving individual media assets used in video generation.
"""
import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import mimetypes

from ..lib.database import get_db_session
from ..models.media_asset import MediaAsset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media/assets", tags=["media-assets"])


@router.get("/{asset_id}")
async def get_media_asset(asset_id: str):
    """
    Get individual media asset file.

    Serves media assets (images, audio, video clips) used in video generation.
    """
    try:
        asset_uuid = uuid.UUID(asset_id)

        with get_db_session() as db:
            asset = db.query(MediaAsset).filter(
                MediaAsset.id == asset_uuid
            ).first()

            if not asset:
                raise HTTPException(
                    status_code=404,
                    detail=f"Media asset {asset_id} not found"
                )

            # Check if asset file exists
            asset_path = Path(asset.file_path)
            if not asset_path.exists():
                logger.error(f"Asset file not found: {asset_path}")
                raise HTTPException(
                    status_code=404,
                    detail="Asset file not found on server"
                )

            # Determine MIME type based on asset type and file extension
            media_type = _get_media_type(asset, asset_path)

            # Generate appropriate filename
            filename = _generate_asset_filename(asset, asset_path)

            # Return file with appropriate headers
            return FileResponse(
                path=str(asset_path),
                media_type=media_type,
                filename=filename,
                headers={
                    "Content-Length": str(asset_path.stat().st_size),
                    "Cache-Control": "public, max-age=86400",  # 24 hours cache
                    "X-Content-Type-Options": "nosniff",
                    "X-Asset-Type": asset.asset_type.value,
                    "X-Source-Type": asset.source_type.value
                }
            )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_media_asset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{asset_id}/info")
async def get_asset_info(asset_id: str):
    """
    Get media asset metadata information.

    Returns detailed information about a media asset without serving the file.
    """
    try:
        asset_uuid = uuid.UUID(asset_id)

        with get_db_session() as db:
            asset = db.query(MediaAsset).filter(
                MediaAsset.id == asset_uuid
            ).first()

            if not asset:
                raise HTTPException(
                    status_code=404,
                    detail=f"Media asset {asset_id} not found"
                )

            # Check if file exists and get file info
            asset_path = Path(asset.file_path)
            file_exists = asset_path.exists()
            file_size = asset_path.stat().st_size if file_exists else None

            return {
                "id": str(asset.id),
                "asset_type": asset.asset_type.value,
                "source_type": asset.source_type.value,
                "url_path": asset.url_path,
                "file_path": asset.file_path,
                "duration": asset.duration,
                "generation_model": getattr(asset, 'gemini_model_used', 'unknown'),
                "model_fallback_used": getattr(asset, 'model_fallback_used', False),
                "generation_metadata": getattr(asset, 'generation_metadata', {}),
                "metadata": asset.metadata,
                "creation_timestamp": asset.creation_timestamp.isoformat(),
                "created_at": asset.creation_timestamp.isoformat(),
                "generation_job_id": str(asset.generation_job_id),
                "file_exists": file_exists,
                "file_size": file_size,
                "media_type": _get_media_type(asset, asset_path) if file_exists else None
            }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID format")
    except Exception as e:
        logger.error(f"Unexpected error in get_asset_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _get_media_type(asset: MediaAsset, asset_path: Path) -> str:
    """Determine the appropriate MIME type for a media asset."""
    # First try to guess from file extension
    mime_type, _ = mimetypes.guess_type(str(asset_path))

    if mime_type:
        return mime_type

    # Fallback based on asset type
    asset_type_defaults = {
        "IMAGE": "image/jpeg",
        "AUDIO": "audio/mpeg",
        "VIDEO_CLIP": "video/mp4",
        "TEXT_OVERLAY": "application/json"
    }

    return asset_type_defaults.get(asset.asset_type.value, "application/octet-stream")


def _generate_asset_filename(asset: MediaAsset, asset_path: Path) -> str:
    """Generate an appropriate filename for the asset download."""
    # Use the original filename if available
    original_filename = asset_path.name

    # If it's a generic filename, create a more descriptive one
    if original_filename.startswith(("bg_", "text_", "narration_", "music_")):
        asset_type_names = {
            "IMAGE": "image",
            "AUDIO": "audio",
            "VIDEO_CLIP": "video",
            "TEXT_OVERLAY": "text"
        }

        type_name = asset_type_names.get(asset.asset_type.value, "asset")
        extension = asset_path.suffix or _get_default_extension(asset.asset_type.value)

        return f"{type_name}_{str(asset.id)[:8]}{extension}"

    return original_filename


def _get_default_extension(asset_type: str) -> str:
    """Get default file extension for asset type."""
    extensions = {
        "IMAGE": ".jpg",
        "AUDIO": ".mp3",
        "VIDEO_CLIP": ".mp4",
        "TEXT_OVERLAY": ".json"
    }
    return extensions.get(asset_type, ".bin")