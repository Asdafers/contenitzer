from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import uuid
import logging
import ffmpeg
import os

from ..models.composed_video import ComposedVideo, UploadStatusEnum
from ..models.video_project import VideoProject, ProjectStatusEnum
from ..models.media_asset import MediaAsset, AssetTypeEnum

logger = logging.getLogger(__name__)


class VideoService:
    """Service for composing final videos from media assets"""

    def __init__(self, db: Session):
        self.db = db

    async def compose_video(
        self,
        project_id: str
    ) -> ComposedVideo:
        """
        Compose final video from all project assets

        Args:
            project_id: UUID of the video project

        Returns:
            Created ComposedVideo instance
        """
        try:
            # Get project and validate it's ready
            project = self.db.query(VideoProject).filter(
                VideoProject.id == uuid.UUID(project_id)
            ).first()

            if not project:
                raise ValueError(f"Project not found: {project_id}")

            if project.status != ProjectStatusEnum.ready:
                raise ValueError(f"Project not ready for composition: {project.status}")

            # Get all assets
            assets = self.db.query(MediaAsset).filter(
                MediaAsset.project_id == project.id
            ).all()

            audio_assets = [a for a in assets if a.asset_type == AssetTypeEnum.audio]
            image_assets = [a for a in assets if a.asset_type == AssetTypeEnum.image]
            video_assets = [a for a in assets if a.asset_type == AssetTypeEnum.video]

            if not audio_assets:
                raise ValueError("No audio assets found for composition")

            # Create composed video record
            composed_video = ComposedVideo(
                id=uuid.uuid4(),
                project_id=project.id,
                file_path=f"/media/composed/{uuid.uuid4()}.mp4",
                resolution="1920x1080",
                format="mp4",
                upload_status=UploadStatusEnum.pending
            )

            # Compose video using FFmpeg
            composition_result = await self._compose_with_ffmpeg(
                audio_assets=audio_assets,
                image_assets=image_assets,
                video_assets=video_assets,
                output_path=composed_video.file_path
            )

            # Update composed video with results
            composed_video.file_size = composition_result["file_size"]
            composed_video.duration = composition_result["duration"]
            composed_video.composition_settings = composition_result["settings"]

            self.db.add(composed_video)
            self.db.commit()
            self.db.refresh(composed_video)

            # Update project status
            project.status = ProjectStatusEnum.ready
            self.db.commit()

            logger.info(f"Composed video for project: {project_id}")
            return composed_video

        except Exception as e:
            logger.error(f"Failed to compose video: {e}")
            if 'project' in locals():
                project.status = ProjectStatusEnum.failed
                project.error_message = str(e)
                self.db.commit()
            raise

    async def _compose_with_ffmpeg(
        self,
        audio_assets: List[MediaAsset],
        image_assets: List[MediaAsset],
        video_assets: List[MediaAsset],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Use FFmpeg to compose final video

        Args:
            audio_assets: List of audio assets
            image_assets: List of image assets
            video_assets: List of video assets
            output_path: Path for final video

        Returns:
            Composition metadata
        """
        try:
            # For now, simulate video composition
            # In a real implementation, this would use ffmpeg-python to:
            # 1. Create video timeline from images and video clips
            # 2. Overlay conversational audio
            # 3. Add transitions and effects
            # 4. Render final video

            main_audio = audio_assets[0]
            total_duration = main_audio.duration

            # Simulate composition settings
            settings = {
                "resolution": "1920x1080",
                "fps": 30,
                "audio_codec": "aac",
                "video_codec": "h264",
                "bitrate": "2000k",
                "audio_sources": len(audio_assets),
                "image_sources": len(image_assets),
                "video_sources": len(video_assets)
            }

            # Simulate file creation
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create a dummy file to simulate the composed video
            with open(output_path, 'w') as f:
                f.write(f"Simulated video file - Duration: {total_duration}s")

            # Estimate file size (rough calculation)
            estimated_size = total_duration * 250000  # ~250KB per second for 1080p

            return {
                "duration": total_duration,
                "file_size": estimated_size,
                "settings": settings,
                "output_path": output_path
            }

        except Exception as e:
            logger.error(f"FFmpeg composition failed: {e}")
            raise Exception(f"Video composition failed: {e}")

    def get_composed_video_by_project(self, project_id: str) -> Optional[ComposedVideo]:
        """Get composed video for a project"""
        try:
            return self.db.query(ComposedVideo).filter(
                ComposedVideo.project_id == uuid.UUID(project_id)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get composed video for project {project_id}: {e}")
            return None

    def validate_assets_for_composition(self, project_id: str) -> bool:
        """Validate that all required assets are available for composition"""
        try:
            assets = self.db.query(MediaAsset).filter(
                MediaAsset.project_id == uuid.UUID(project_id)
            ).all()

            audio_assets = [a for a in assets if a.asset_type == AssetTypeEnum.audio]

            # Must have at least one audio asset
            return len(audio_assets) > 0

        except Exception as e:
            logger.error(f"Failed to validate assets for project {project_id}: {e}")
            return False