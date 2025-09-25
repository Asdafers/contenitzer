"""
Media Asset Generator Service for creating video components from script content.
Generates images, audio, and video clips for video composition.
"""
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime

from ..models.media_asset import MediaAsset, AssetTypeEnum as AssetType, SourceTypeEnum as SourceType
from ..models.video_generation_job import VideoGenerationJob
from ..lib.database import get_db_session
from .storage_manager import StorageManager

logger = logging.getLogger(__name__)


class MediaAssetGeneratorError(Exception):
    """Exception raised by media asset generation operations."""
    pass


class MediaAssetGenerator:
    """Service for generating media assets from script content."""

    def __init__(self):
        self.storage_manager = StorageManager()

    def analyze_script_requirements(self, script_content: str, duration: int) -> Dict[str, Any]:
        """
        Analyze script content to determine media asset requirements.

        Args:
            script_content: Text content of the script
            duration: Target video duration in seconds

        Returns:
            Dictionary with asset requirements and scene breakdown
        """
        try:
            # Parse script into scenes/segments
            scenes = self._parse_script_scenes(script_content)

            # Calculate timing for each scene
            scene_duration = duration / max(len(scenes), 1)

            requirements = {
                "total_duration": duration,
                "scene_count": len(scenes),
                "scene_duration": scene_duration,
                "scenes": [],
                "assets_needed": {
                    "images": 0,
                    "audio_tracks": 1,  # Background music + narration
                    "video_clips": 0,
                    "text_overlays": len(scenes)
                }
            }

            for i, scene in enumerate(scenes):
                scene_info = {
                    "index": i,
                    "text": scene,
                    "start_time": i * scene_duration,
                    "duration": scene_duration,
                    "needs_background": True,
                    "needs_text_overlay": True,
                    "background_style": self._determine_background_style(scene)
                }
                requirements["scenes"].append(scene_info)
                requirements["assets_needed"]["images"] += 1

            return requirements

        except Exception as e:
            logger.error(f"Failed to analyze script requirements: {e}")
            raise MediaAssetGeneratorError(f"Script analysis failed: {e}")

    def generate_assets_for_job(
        self,
        job_id: uuid.UUID,
        script_content: str,
        options: Dict[str, Any]
    ) -> List[MediaAsset]:
        """
        Generate all required media assets for a video generation job.

        Args:
            job_id: Video generation job UUID
            script_content: Script text content
            options: Generation options (resolution, duration, etc.)

        Returns:
            List of created MediaAsset objects
        """
        try:
            # Analyze script requirements
            requirements = self.analyze_script_requirements(
                script_content,
                options.get("duration", 180)
            )

            generated_assets = []

            with get_db_session() as db:
                # Generate background images
                for scene in requirements["scenes"]:
                    image_asset = self._generate_background_image(
                        db, job_id, scene, options
                    )
                    generated_assets.append(image_asset)

                # Generate text overlays
                for scene in requirements["scenes"]:
                    text_asset = self._generate_text_overlay(
                        db, job_id, scene, options
                    )
                    generated_assets.append(text_asset)

                # Generate audio tracks
                audio_asset = self._generate_audio_track(
                    db, job_id, script_content, requirements["total_duration"], options
                )
                generated_assets.append(audio_asset)

                # Generate background music if requested
                if options.get("include_audio", True):
                    music_asset = self._generate_background_music(
                        db, job_id, requirements["total_duration"], options
                    )
                    generated_assets.append(music_asset)

                db.commit()

            logger.info(f"Generated {len(generated_assets)} assets for job {job_id}")
            return generated_assets

        except Exception as e:
            logger.error(f"Failed to generate assets for job {job_id}: {e}")
            raise MediaAssetGeneratorError(f"Asset generation failed: {e}")

    def _parse_script_scenes(self, script_content: str) -> List[str]:
        """Parse script content into scenes or segments."""
        # Simple scene parsing - split by paragraphs or sentences
        sentences = re.split(r'[.!?]+', script_content.strip())
        scenes = [s.strip() for s in sentences if s.strip()]

        # Ensure we have at least one scene
        if not scenes:
            scenes = [script_content.strip() or "Generated video content"]

        return scenes

    def _determine_background_style(self, scene_text: str) -> str:
        """Determine appropriate background style based on scene content."""
        # Simple keyword-based style detection
        scene_lower = scene_text.lower()

        if any(word in scene_lower for word in ["nature", "outdoor", "landscape"]):
            return "nature"
        elif any(word in scene_lower for word in ["business", "office", "professional"]):
            return "business"
        elif any(word in scene_lower for word in ["technology", "tech", "digital"]):
            return "technology"
        else:
            return "abstract"

    def _generate_background_image(
        self,
        db,
        job_id: uuid.UUID,
        scene: Dict[str, Any],
        options: Dict[str, Any]
    ) -> MediaAsset:
        """Generate a background image for a scene."""
        try:
            resolution = options.get("resolution", "1920x1080")
            width, height = map(int, resolution.split("x"))

            # Create asset record
            asset = MediaAsset(
                id=uuid.uuid4(),
                asset_type=AssetType.IMAGE,
                source_type=SourceType.GENERATED,
                generation_job_id=job_id,
                creation_timestamp=datetime.now()
            )

            # Generate file path
            filename = f"bg_{scene['index']:03d}_{asset.id}.jpg"
            file_path = Path(self.storage_manager.get_asset_path("images") / filename)

            # Create the image file FIRST
            self._create_placeholder_image(
                file_path,
                width, height,
                scene["background_style"],
                scene["text"][:50]  # Use first 50 chars as description
            )

            # Now set the paths after file exists
            asset.file_path = str(file_path)
            asset.url_path = f"/media/assets/images/{filename}"

            # Set metadata
            asset.set_image_metadata(
                width=width,
                height=height,
                format="jpeg",
                generation_method="PLACEHOLDER"
            )

            db.add(asset)
            return asset

        except Exception as e:
            logger.error(f"Failed to generate background image: {e}")
            raise MediaAssetGeneratorError(f"Background image generation failed: {e}")

    def _generate_text_overlay(
        self,
        db,
        job_id: uuid.UUID,
        scene: Dict[str, Any],
        options: Dict[str, Any]
    ) -> MediaAsset:
        """Generate a text overlay for a scene."""
        try:
            # Create asset record
            asset = MediaAsset(
                id=uuid.uuid4(),
                asset_type=AssetType.TEXT_OVERLAY,
                source_type=SourceType.GENERATED,
                generation_job_id=job_id,
                creation_timestamp=datetime.now(),
                duration=int(scene["duration"])
            )

            # Generate file path (JSON file with text overlay data)
            filename = f"text_{scene['index']:03d}_{asset.id}.json"
            asset.file_path = str(self.storage_manager.get_asset_path("temp") / filename)
            asset.url_path = f"/media/assets/temp/{filename}"

            # Set metadata
            asset.set_text_metadata(
                font="Arial",
                size=48,
                color="#FFFFFF",
                position="bottom_center",
                background_color="#000000AA",
                text=scene["text"]
            )

            # Create text overlay data file
            self._create_text_overlay_data(Path(asset.file_path), asset.metadata)

            db.add(asset)
            return asset

        except Exception as e:
            logger.error(f"Failed to generate text overlay: {e}")
            raise MediaAssetGeneratorError(f"Text overlay generation failed: {e}")

    def _generate_audio_track(
        self,
        db,
        job_id: uuid.UUID,
        script_content: str,
        duration: int,
        options: Dict[str, Any]
    ) -> MediaAsset:
        """Generate narration audio track from script content."""
        try:
            # Create asset record
            asset = MediaAsset(
                id=uuid.uuid4(),
                asset_type=AssetType.AUDIO,
                source_type=SourceType.GENERATED,
                generation_job_id=job_id,
                creation_timestamp=datetime.now(),
                duration=duration
            )

            # Generate file path
            filename = f"narration_{asset.id}.mp3"
            asset.file_path = str(self.storage_manager.get_asset_path("audio") / filename)
            asset.url_path = f"/media/assets/audio/{filename}"

            # Set metadata
            asset.set_audio_metadata(
                sample_rate=44100,
                channels=1,  # Mono for narration
                codec="mp3",
                content_type="narration"
            )

            # Create placeholder audio file
            self._create_placeholder_audio(
                Path(asset.file_path),
                duration,
                "narration"
            )

            db.add(asset)
            return asset

        except Exception as e:
            logger.error(f"Failed to generate audio track: {e}")
            raise MediaAssetGeneratorError(f"Audio track generation failed: {e}")

    def _generate_background_music(
        self,
        db,
        job_id: uuid.UUID,
        duration: int,
        options: Dict[str, Any]
    ) -> MediaAsset:
        """Generate background music track."""
        try:
            # Create asset record
            asset = MediaAsset(
                id=uuid.uuid4(),
                asset_type=AssetType.AUDIO,
                source_type=SourceType.STOCK,  # Use stock music
                generation_job_id=job_id,
                creation_timestamp=datetime.now(),
                duration=duration
            )

            # Generate file path
            filename = f"music_{asset.id}.mp3"
            asset.file_path = str(self.storage_manager.get_asset_path("audio") / filename)
            asset.url_path = f"/media/assets/audio/{filename}"

            # Set metadata
            asset.set_audio_metadata(
                sample_rate=44100,
                channels=2,  # Stereo for music
                codec="mp3",
                content_type="background_music"
            )

            # Create placeholder music file
            self._create_placeholder_audio(
                Path(asset.file_path),
                duration,
                "music"
            )

            db.add(asset)
            return asset

        except Exception as e:
            logger.error(f"Failed to generate background music: {e}")
            raise MediaAssetGeneratorError(f"Background music generation failed: {e}")

    def _create_placeholder_image(
        self,
        file_path: Path,
        width: int,
        height: int,
        style: str,
        description: str
    ):
        """Create a placeholder image file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a simple placeholder image (solid color with text)
            # In real implementation, this would generate actual images
            placeholder_content = f"PLACEHOLDER IMAGE\n{width}x{height}\nStyle: {style}\n{description}"

            # Try to create a real image file using PIL
            try:
                from PIL import Image, ImageDraw, ImageFont

                # Create solid color background based on style
                background_colors = {
                    "nature": (34, 139, 34),    # Forest green
                    "technology": (70, 130, 180),  # Steel blue
                    "business": (105, 105, 105),   # Dim gray
                    "education": (255, 165, 0),    # Orange
                    "default": (100, 100, 100)     # Gray
                }
                bg_color = background_colors.get(style.lower(), background_colors["default"])

                # Create image
                image = Image.new('RGB', (width, height), bg_color)
                draw = ImageDraw.Draw(image)

                # Add text overlay
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                except:
                    font = ImageFont.load_default()

                # Draw text lines
                text_lines = [
                    "Generated Image",
                    f"{width}x{height}",
                    f"Style: {style}",
                    description[:40] + "..." if len(description) > 40 else description
                ]

                y_offset = height // 2 - 80
                for line in text_lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (width - text_width) // 2
                    draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
                    y_offset += 50

                # Save as JPEG
                image.save(file_path, "JPEG", quality=85)
                logger.info(f"Created placeholder image: {file_path}")

            except ImportError:
                # Fallback: create a simple text file with content but save as .jpg extension
                logger.warning("PIL not available, creating text placeholder with .jpg extension")
                with open(file_path, 'w') as f:
                    f.write(placeholder_content)

        except Exception as e:
            logger.error(f"Failed to create placeholder image: {e}")
            raise

    def _create_text_overlay_data(self, file_path: Path, metadata: Dict[str, Any]):
        """Create text overlay configuration file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to create text overlay data: {e}")
            raise

    def _create_placeholder_audio(self, file_path: Path, duration: int, content_type: str):
        """Create a placeholder audio file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create placeholder audio content description
            placeholder_content = f"PLACEHOLDER AUDIO\nDuration: {duration}s\nType: {content_type}"

            # Write as text file for now (in real implementation, would create actual audio)
            with open(file_path.with_suffix('.txt'), 'w') as f:
                f.write(placeholder_content)

            # Create empty audio file marker
            file_path.touch()

        except Exception as e:
            logger.error(f"Failed to create placeholder audio: {e}")
            raise