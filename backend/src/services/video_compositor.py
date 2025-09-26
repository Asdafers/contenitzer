"""
Video Compositor Service - Stitch together images and videos into final composition.
Uses FFmpeg to combine AI-generated assets with transitions and audio.
"""

import logging
import subprocess
import os
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class VideoCompositorError(Exception):
    """Exception raised by video composition operations."""
    pass


class VideoCompositor:
    """Service for compositing final videos from generated assets."""

    def __init__(self):
        self.temp_dir = Path("/tmp/claude/video_composition")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def compose_hybrid_video(
        self,
        assets_plan: Dict[str, Any],
        output_path: str,
        composition_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose final video from mixed image and video assets.

        Args:
            assets_plan: Plan from EnhancedContentPlanner with images/videos
            output_path: Final video output path
            composition_settings: Additional settings

        Returns:
            Composition result metadata
        """
        try:
            logger.info("Starting hybrid video composition")

            settings = composition_settings or {}
            resolution = settings.get("resolution", "1920x1080")
            fps = settings.get("fps", 30)

            # Create composition timeline
            timeline = self._create_timeline(assets_plan)

            # Generate FFmpeg filter complex
            filter_complex = self._build_filter_complex(timeline, resolution, fps)

            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(timeline, filter_complex, output_path, settings)

            # Execute composition
            result = self._execute_ffmpeg(cmd)

            # Get output video info
            video_info = self._get_video_info(output_path)

            logger.info(f"Video composition completed: {output_path}")

            return {
                "output_path": output_path,
                "duration": video_info.get("duration", 0),
                "resolution": resolution,
                "fps": fps,
                "file_size_mb": video_info.get("size_mb", 0),
                "composition_metadata": {
                    "total_scenes": len(timeline),
                    "image_count": sum(1 for scene in timeline if scene["type"] == "image"),
                    "video_count": sum(1 for scene in timeline if scene["type"] == "video"),
                    "processing_time": result.get("processing_time", 0),
                    "created_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            raise VideoCompositorError(f"Composition failed: {e}")

    def _create_timeline(self, assets_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create timeline from assets plan."""
        timeline = []
        current_time = 0.0

        # Process images
        for image_asset in assets_plan.get("assets", {}).get("images", []):
            timeline.append({
                "id": image_asset["id"],
                "type": "image",
                "path": self._get_mock_image_path(),  # Placeholder for now
                "start_time": current_time,
                "duration": image_asset["duration"],
                "transition": "fade"
            })
            current_time += image_asset["duration"]

        # Process videos
        for video_asset in assets_plan.get("assets", {}).get("videos", []):
            timeline.append({
                "id": video_asset["id"],
                "type": "video",
                "path": self._get_mock_video_path(),  # Placeholder for now
                "start_time": current_time,
                "duration": video_asset["duration"],
                "transition": "crossfade"
            })
            current_time += video_asset["duration"]

        # Sort by start time
        timeline.sort(key=lambda x: x["start_time"])
        return timeline

    def _build_filter_complex(self, timeline: List[Dict[str, Any]], resolution: str, fps: int) -> str:
        """Build FFmpeg filter_complex for timeline."""
        filters = []
        width, height = map(int, resolution.split("x"))

        # Scale and prepare each input
        for i, scene in enumerate(timeline):
            if scene["type"] == "image":
                # Convert image to video with specified duration
                filters.append(f"[{i}:v]scale={width}:{height},fps={fps},loop=loop=-1:size={fps * scene['duration']}[v{i}]")
            else:
                # Scale video
                filters.append(f"[{i}:v]scale={width}:{height}[v{i}]")

        # Concatenate all segments
        input_refs = "".join([f"[v{i}]" for i in range(len(timeline))])
        filters.append(f"{input_refs}concat=n={len(timeline)}:v=1:a=0[out]")

        return ";".join(filters)

    def _build_ffmpeg_command(
        self,
        timeline: List[Dict[str, Any]],
        filter_complex: str,
        output_path: str,
        settings: Dict[str, Any]
    ) -> List[str]:
        """Build complete FFmpeg command."""
        cmd = ["ffmpeg", "-y"]  # -y to overwrite output

        # Add input files
        for scene in timeline:
            cmd.extend(["-i", scene["path"]])

        # Add filter complex
        cmd.extend(["-filter_complex", filter_complex])

        # Map output
        cmd.extend(["-map", "[out]"])

        # Output settings
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"
        ])

        # Add output path
        cmd.append(output_path)

        return cmd

    def _execute_ffmpeg(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute FFmpeg command with error handling."""
        try:
            start_time = datetime.now()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise VideoCompositorError(f"FFmpeg failed: {result.stderr}")

            return {
                "success": True,
                "processing_time": processing_time,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            raise VideoCompositorError("Video composition timed out")
        except Exception as e:
            raise VideoCompositorError(f"FFmpeg execution failed: {e}")

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                info = json.loads(result.stdout)
                format_info = info.get("format", {})

                return {
                    "duration": float(format_info.get("duration", 0)),
                    "size_mb": float(format_info.get("size", 0)) / (1024 * 1024),
                    "format": format_info.get("format_name", "unknown")
                }
        except Exception as e:
            logger.warning(f"Could not get video info: {e}")

        return {"duration": 0, "size_mb": 0, "format": "unknown"}

    def _get_mock_image_path(self) -> str:
        """Get path to mock image for testing."""
        # Create simple test image if needed
        mock_path = self.temp_dir / "test_image.jpg"
        if not mock_path.exists():
            self._create_test_image(str(mock_path))
        return str(mock_path)

    def _get_mock_video_path(self) -> str:
        """Get path to mock video for testing."""
        mock_path = self.temp_dir / "test_video.mp4"
        if not mock_path.exists():
            self._create_test_video(str(mock_path))
        return str(mock_path)

    def _create_test_image(self, path: str):
        """Create test image using FFmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "color=c=blue:size=1920x1080:duration=1",
                "-frames:v", "1", path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            logger.warning(f"Could not create test image: {e}")

    def _create_test_video(self, path: str):
        """Create test video using FFmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", "testsrc=duration=3:size=1920x1080:rate=30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            logger.warning(f"Could not create test video: {e}")

    def cleanup(self, composition_id: str):
        """Clean up temporary files for composition."""
        try:
            # Remove temporary files associated with composition
            temp_pattern = self.temp_dir / f"{composition_id}_*"
            for temp_file in temp_pattern.parent.glob(temp_pattern.name):
                temp_file.unlink(missing_ok=True)

            logger.info(f"Cleaned up composition {composition_id}")
        except Exception as e:
            logger.warning(f"Cleanup failed for {composition_id}: {e}")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return ["mp4", "mov", "avi", "mkv", "webm"]

    def estimate_processing_time(self, assets_plan: Dict[str, Any]) -> int:
        """Estimate processing time in seconds."""
        total_duration = assets_plan.get("summary", {}).get("total_duration", 180)
        asset_count = assets_plan.get("summary", {}).get("total_assets", 10)

        # Base time + time per asset + time per minute of output
        base_time = 30  # 30 seconds base
        per_asset = asset_count * 5  # 5 seconds per asset
        per_minute = (total_duration / 60) * 20  # 20 seconds per output minute

        return int(base_time + per_asset + per_minute)