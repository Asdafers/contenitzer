"""
Video Composer Service for assembling final videos from media assets.
Uses FFmpeg to combine images, audio, and effects into final video output.
"""
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime

from ..models.media_asset import MediaAsset, AssetTypeEnum as AssetType
from ..models.generated_video import GeneratedVideo, GenerationStatusEnum as VideoStatus
from ..lib.ffmpeg_utils import ffmpeg, FFmpegError
from .storage_manager import StorageManager

logger = logging.getLogger(__name__)


class VideoComposerError(Exception):
    """Exception raised by video composition operations."""
    pass


class VideoComposer:
    """Service for composing final videos from media assets."""

    def __init__(self):
        self.storage_manager = StorageManager()

    def compose_video(
        self,
        assets: List[MediaAsset],
        output_options: Dict[str, Any],
        job_id: uuid.UUID
    ) -> GeneratedVideo:
        """
        Compose a final video from media assets.

        Args:
            assets: List of MediaAsset objects to compose
            output_options: Video output configuration
            job_id: Associated job ID

        Returns:
            GeneratedVideo object with composition results
        """
        try:
            # Validate inputs
            self._validate_composition_inputs(assets, output_options)

            # Organize assets by type
            asset_groups = self._group_assets_by_type(assets)

            # Create output video record
            video = self._create_video_record(output_options, job_id)

            # Create composition timeline
            timeline = self._create_composition_timeline(asset_groups, output_options)

            # Compose video in stages
            temp_video_path = self._compose_visual_track(timeline, output_options)
            final_video_path = self._add_audio_tracks(
                temp_video_path, asset_groups, output_options, video.file_path
            )

            # Validate final video
            video_info = self._validate_output_video(final_video_path)

            # Update video record with actual properties
            video.file_size = video_info["file_size"]
            video.duration = video_info["duration"]
            video.generation_status = VideoStatus.COMPLETED
            video.completion_timestamp = datetime.now()

            logger.info(f"Successfully composed video {video.id}")
            return video

        except Exception as e:
            logger.error(f"Failed to compose video: {e}")
            raise VideoComposerError(f"Video composition failed: {e}")

    def _validate_composition_inputs(
        self,
        assets: List[MediaAsset],
        options: Dict[str, Any]
    ):
        """Validate that we have required assets and options for composition."""
        if not assets:
            raise VideoComposerError("No assets provided for composition")

        # Check for required asset types
        asset_types = {asset.asset_type for asset in assets}

        if AssetType.IMAGE not in asset_types:
            logger.warning("No background images found, composition may fail")

        # Validate output options
        required_options = ["resolution", "duration"]
        for option in required_options:
            if option not in options:
                raise VideoComposerError(f"Missing required option: {option}")

        # Validate resolution format
        resolution = options["resolution"]
        if not isinstance(resolution, str) or "x" not in resolution:
            raise VideoComposerError(f"Invalid resolution format: {resolution}")

    def _group_assets_by_type(self, assets: List[MediaAsset]) -> Dict[AssetType, List[MediaAsset]]:
        """Group assets by their type for easier processing."""
        groups = {
            AssetType.IMAGE: [],
            AssetType.AUDIO: [],
            AssetType.VIDEO_CLIP: [],
            AssetType.TEXT_OVERLAY: []
        }

        for asset in assets:
            if asset.asset_type in groups:
                groups[asset.asset_type].append(asset)

        # Sort images by filename to ensure proper sequence
        groups[AssetType.IMAGE].sort(key=lambda a: a.file_path)

        return groups

    def _create_video_record(
        self,
        options: Dict[str, Any],
        job_id: uuid.UUID
    ) -> GeneratedVideo:
        """Create GeneratedVideo database record."""
        video_id = uuid.uuid4()

        # Generate output file path
        filename = f"video_{video_id}.mp4"
        file_path = str(self.storage_manager.get_video_path() / filename)
        url_path = f"/media/videos/{filename}"

        return GeneratedVideo(
            id=video_id,
            file_path=file_path,
            url_path=url_path,
            title=options.get("title", "Generated Video Content"),
            duration=options["duration"],
            resolution=options["resolution"],
            format="mp4",
            generation_status=VideoStatus.GENERATING,
            script_id=options.get("script_id"),
            session_id=options.get("session_id", "unknown"),
            generation_job_id=job_id,  # Add the missing generation_job_id
            creation_timestamp=datetime.now()
        )

    def _create_composition_timeline(
        self,
        asset_groups: Dict[AssetType, List[MediaAsset]],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create timeline for video composition."""
        total_duration = options["duration"]
        images = asset_groups[AssetType.IMAGE]
        text_overlays = asset_groups[AssetType.TEXT_OVERLAY]

        if not images:
            raise VideoComposerError("No background images available for composition")

        # Calculate timing for each scene
        scene_duration = total_duration / len(images) if images else total_duration

        timeline = {
            "total_duration": total_duration,
            "scene_duration": scene_duration,
            "scenes": []
        }

        for i, image_asset in enumerate(images):
            start_time = i * scene_duration

            # Find corresponding text overlay
            text_overlay = None
            for overlay in text_overlays:
                # Match by index or timing
                if f"_{i:03d}_" in overlay.file_path:
                    text_overlay = overlay
                    break

            timeline["scenes"].append({
                "index": i,
                "start_time": start_time,
                "duration": scene_duration,
                "background_image": image_asset,
                "text_overlay": text_overlay
            })

        return timeline

    def _compose_visual_track(
        self,
        timeline: Dict[str, Any],
        options: Dict[str, Any]
    ) -> Path:
        """Compose the visual track (images + text overlays)."""
        try:
            resolution = options["resolution"]
            width, height = map(int, resolution.split("x"))
            fps = options.get("fps", 30)

            # Create temporary output path
            temp_path = self.storage_manager.get_temp_path() / f"visual_{uuid.uuid4()}.mp4"

            # Collect image paths for FFmpeg
            image_paths = []
            for scene in timeline["scenes"]:
                image_path = Path(scene["background_image"].file_path)
                if image_path.exists():
                    image_paths.append(image_path)
                else:
                    logger.warning(f"Image not found: {image_path}")

            if not image_paths:
                raise VideoComposerError("No valid image files found")

            # Use FFmpeg wrapper to create video from images
            success = ffmpeg.create_video_from_images(
                image_paths=image_paths,
                output_path=temp_path,
                duration=timeline["total_duration"],
                fps=fps,
                resolution=(width, height)
            )

            if not success:
                raise VideoComposerError("Failed to create visual track")

            return temp_path

        except Exception as e:
            logger.error(f"Failed to compose visual track: {e}")
            raise VideoComposerError(f"Visual track composition failed: {e}")

    def _add_audio_tracks(
        self,
        video_path: Path,
        asset_groups: Dict[AssetType, List[MediaAsset]],
        options: Dict[str, Any],
        final_output_path: str
    ) -> Path:
        """Add audio tracks to the visual video."""
        try:
            audio_assets = asset_groups[AssetType.AUDIO]
            final_path = Path(final_output_path)
            final_path.parent.mkdir(parents=True, exist_ok=True)

            if not audio_assets or not options.get("include_audio", True):
                # No audio - just copy video to final location
                if video_path != final_path:
                    video_path.rename(final_path)
                return final_path

            # Find primary audio track (narration)
            narration_track = None
            music_track = None

            for audio in audio_assets:
                if audio.metadata and "content_type" in audio.metadata:
                    if audio.metadata["content_type"] == "narration":
                        narration_track = audio
                    elif audio.metadata["content_type"] == "background_music":
                        music_track = audio

            # Add primary audio track
            if narration_track and Path(narration_track.file_path).exists():
                success = ffmpeg.add_audio_to_video(
                    video_path=video_path,
                    audio_path=Path(narration_track.file_path),
                    output_path=final_path,
                    video_duration=options["duration"]
                )

                if not success:
                    logger.warning("Failed to add narration, copying video without audio")
                    if video_path != final_path:
                        video_path.rename(final_path)
            else:
                # No valid audio - copy video as-is
                if video_path != final_path:
                    video_path.rename(final_path)

            # Clean up temporary video file
            if video_path.exists() and video_path != final_path:
                video_path.unlink()

            return final_path

        except Exception as e:
            logger.error(f"Failed to add audio tracks: {e}")
            # Fallback: copy video without audio
            final_path = Path(final_output_path)
            if video_path.exists() and video_path != final_path:
                video_path.rename(final_path)
            return final_path

    def _validate_output_video(self, video_path: Path) -> Dict[str, Any]:
        """Validate the final output video and return its properties."""
        try:
            if not video_path.exists():
                raise VideoComposerError(f"Output video not found: {video_path}")

            # Get video properties using FFmpeg wrapper
            video_info = ffmpeg.probe_video(video_path)

            # Validate minimum requirements
            if video_info["duration"] <= 0:
                raise VideoComposerError("Invalid video duration")

            if video_info["size"] <= 0:
                raise VideoComposerError("Invalid video file size")

            return {
                "duration": int(video_info["duration"]),
                "file_size": video_info["size"],
                "width": video_info["width"],
                "height": video_info["height"],
                "fps": video_info["fps"],
                "format": video_info["format"]
            }

        except Exception as e:
            logger.error(f"Failed to validate output video: {e}")
            raise VideoComposerError(f"Video validation failed: {e}")

    def compose_video_file_only(
        self,
        assets: List[MediaAsset],
        output_options: Dict[str, Any],
        output_file_path: str
    ) -> Dict[str, Any]:
        """
        Compose video file without creating database record.

        Args:
            assets: List of MediaAsset objects to compose
            output_options: Video output configuration
            output_file_path: Path where video file should be created

        Returns:
            Dictionary with video file properties
        """
        try:
            # Validate inputs
            self._validate_composition_inputs(assets, output_options)

            # Organize assets by type
            asset_groups = self._group_assets_by_type(assets)

            # Create composition timeline
            timeline = self._create_composition_timeline(asset_groups, output_options)

            # Compose video in stages
            temp_video_path = self._compose_visual_track(timeline, output_options)
            final_video_path = self._add_audio_tracks(
                temp_video_path, asset_groups, output_options, output_file_path
            )

            # Validate final video and return properties
            video_info = self._validate_output_video(final_video_path)

            logger.info(f"Successfully composed video file at {output_file_path}")
            return video_info

        except Exception as e:
            logger.error(f"Failed to compose video file: {e}")
            raise VideoComposerError(f"Video file composition failed: {e}")

    def cleanup_temp_files(self, job_id: uuid.UUID):
        """Clean up temporary files created during composition."""
        try:
            temp_dir = self.storage_manager.get_temp_path()

            # Find temp files related to this job
            for temp_file in temp_dir.glob(f"*{job_id}*"):
                try:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files for job {job_id}: {e}")

    def get_composition_progress(self, job_id: uuid.UUID) -> Dict[str, Any]:
        """Get progress information for an ongoing composition."""
        # In a real implementation, this would track actual FFmpeg progress
        # For now, return a simple progress estimate
        return {
            "stage": "composition",
            "progress_percentage": 75,  # Placeholder
            "current_operation": "Composing video from assets",
            "estimated_completion": None
        }