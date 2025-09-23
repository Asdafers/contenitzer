from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import uuid
import logging
import asyncio

from ..models.media_asset import MediaAsset, AssetTypeEnum, GenerationStatusEnum
from ..models.video_project import VideoProject, ProjectStatusEnum
from ..models.video_script import VideoScript
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


class MediaService:
    """Service for generating and managing media assets"""

    def __init__(self, db: Session, gemini_service: GeminiService):
        self.db = db
        self.gemini_service = gemini_service

    async def generate_media_assets(
        self,
        script_id: str
    ) -> VideoProject:
        """
        Generate all media assets (audio, images, videos) for a script

        Args:
            script_id: UUID of the script

        Returns:
            Created VideoProject instance
        """
        try:
            # Get the script
            script = self.db.query(VideoScript).filter(
                VideoScript.id == uuid.UUID(script_id)
            ).first()

            if not script:
                raise ValueError(f"Script not found: {script_id}")

            # Create video project
            project = VideoProject(
                id=uuid.uuid4(),
                script_id=script.id,
                project_name=f"Project_{script.title[:50]}",
                status=ProjectStatusEnum.generating,
                completion_percentage=0
            )

            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

            # Generate media assets in parallel
            audio_task = self._generate_audio_asset(project, script)
            images_task = self._generate_image_assets(project, script)
            videos_task = self._generate_video_assets(project, script)

            # Wait for all assets to complete
            await asyncio.gather(audio_task, images_task, videos_task)

            # Update project status
            project.status = ProjectStatusEnum.ready
            project.completion_percentage = 100
            self.db.commit()

            logger.info(f"Generated all media assets for project: {project.id}")
            return project

        except Exception as e:
            # Mark project as failed
            if 'project' in locals():
                project.status = ProjectStatusEnum.failed
                project.error_message = str(e)
                self.db.commit()

            logger.error(f"Failed to generate media assets: {e}")
            raise

    async def _generate_audio_asset(
        self,
        project: VideoProject,
        script: VideoScript
    ) -> MediaAsset:
        """Generate conversational audio asset"""
        try:
            # Create audio asset record
            audio_asset = MediaAsset(
                id=uuid.uuid4(),
                project_id=project.id,
                asset_type=AssetTypeEnum.audio,
                generation_prompt=f"Generate conversational audio for: {script.title}",
                gemini_model_used="tts-1",
                generation_status=GenerationStatusEnum.generating
            )

            self.db.add(audio_asset)
            self.db.commit()

            # Generate audio using Gemini service
            audio_data = await self.gemini_service.generate_audio_from_script(
                script_content=script.content
            )

            # Update asset with generated data
            audio_asset.duration = int(audio_data["estimated_audio_duration"])
            audio_asset.file_path = f"/media/audio/{audio_asset.id}.mp3"
            audio_asset.file_size = audio_asset.duration * 32000  # Estimate: 32KB per second
            audio_asset.generation_status = GenerationStatusEnum.completed
            audio_asset.asset_metadata = {
                "speaker1_lines": audio_data["speaker1_lines"],
                "speaker2_lines": audio_data["speaker2_lines"],
                "audio_segments": audio_data["audio_segments"]
            }

            self.db.commit()
            logger.info(f"Generated audio asset: {audio_asset.id}")
            return audio_asset

        except Exception as e:
            if 'audio_asset' in locals():
                audio_asset.generation_status = GenerationStatusEnum.failed
                self.db.commit()
            logger.error(f"Failed to generate audio asset: {e}")
            raise

    async def _generate_image_assets(
        self,
        project: VideoProject,
        script: VideoScript
    ) -> List[MediaAsset]:
        """Generate background image assets"""
        try:
            # Generate image prompts
            image_prompts = await self.gemini_service.generate_images_for_script(
                script_content=script.content,
                num_images=5
            )

            image_assets = []

            for i, prompt_data in enumerate(image_prompts):
                image_asset = MediaAsset(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    asset_type=AssetTypeEnum.image,
                    generation_prompt=prompt_data["prompt"],
                    gemini_model_used="dall-e-3",
                    generation_status=GenerationStatusEnum.generating
                )

                self.db.add(image_asset)
                self.db.commit()

                # Simulate image generation completion
                image_asset.file_path = f"/media/images/{image_asset.id}.jpg"
                image_asset.file_size = 1024 * 1024  # 1MB estimate
                image_asset.generation_status = GenerationStatusEnum.completed
                image_asset.asset_metadata = {
                    "dimensions": prompt_data["dimensions"],
                    "style": prompt_data["style"]
                }

                self.db.commit()
                image_assets.append(image_asset)

            logger.info(f"Generated {len(image_assets)} image assets for project: {project.id}")
            return image_assets

        except Exception as e:
            logger.error(f"Failed to generate image assets: {e}")
            raise

    async def _generate_video_assets(
        self,
        project: VideoProject,
        script: VideoScript
    ) -> List[MediaAsset]:
        """Generate background video clip assets"""
        try:
            # Generate video clip prompts
            video_prompts = await self.gemini_service.generate_video_clips(
                script_content=script.content,
                num_clips=3
            )

            video_assets = []

            for i, prompt_data in enumerate(video_prompts):
                video_asset = MediaAsset(
                    id=uuid.uuid4(),
                    project_id=project.id,
                    asset_type=AssetTypeEnum.video,
                    generation_prompt=prompt_data["prompt"],
                    gemini_model_used="video-generator-1",
                    generation_status=GenerationStatusEnum.generating
                )

                self.db.add(video_asset)
                self.db.commit()

                # Simulate video generation completion
                video_asset.duration = prompt_data["duration"]
                video_asset.file_path = f"/media/videos/{video_asset.id}.mp4"
                video_asset.file_size = prompt_data["duration"] * 1024 * 1024  # 1MB per second estimate
                video_asset.generation_status = GenerationStatusEnum.completed
                video_asset.asset_metadata = {
                    "resolution": prompt_data["resolution"],
                    "format": prompt_data["format"]
                }

                self.db.commit()
                video_assets.append(video_asset)

            logger.info(f"Generated {len(video_assets)} video assets for project: {project.id}")
            return video_assets

        except Exception as e:
            logger.error(f"Failed to generate video assets: {e}")
            raise

    def get_project_by_id(self, project_id: str) -> Optional[VideoProject]:
        """Get project by ID with assets"""
        try:
            return self.db.query(VideoProject).filter(
                VideoProject.id == uuid.UUID(project_id)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    def get_project_assets(self, project_id: str) -> List[MediaAsset]:
        """Get all assets for a project"""
        try:
            return self.db.query(MediaAsset).filter(
                MediaAsset.project_id == uuid.UUID(project_id)
            ).all()
        except Exception as e:
            logger.error(f"Failed to get assets for project {project_id}: {e}")
            return []