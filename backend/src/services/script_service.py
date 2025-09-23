from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import uuid
import logging

from ..models.video_script import VideoScript, InputSourceEnum, FormatTypeEnum
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


class ScriptService:
    """Service for managing video script generation and processing"""

    def __init__(self, db: Session, gemini_service: GeminiService):
        self.db = db
        self.gemini_service = gemini_service

    async def generate_from_theme(
        self,
        theme_id: str,
        theme_name: str,
        theme_description: str = ""
    ) -> VideoScript:
        """
        Generate script from a trending theme

        Args:
            theme_id: UUID of the theme
            theme_name: Name of the theme
            theme_description: Additional theme context

        Returns:
            Created VideoScript instance
        """
        try:
            # Generate script content using Gemini
            script_data = await self.gemini_service.generate_script_from_theme(
                theme_name=theme_name,
                theme_description=theme_description,
                min_duration_seconds=180
            )

            # Create database record
            script = VideoScript(
                id=uuid.uuid4(),
                theme_id=uuid.UUID(theme_id),
                title=f"Video Script: {theme_name}",
                content=script_data["content"],
                estimated_duration=script_data["estimated_duration"],
                format_type=FormatTypeEnum.conversational,
                speaker_count=2,
                input_source=InputSourceEnum.generated
            )

            self.db.add(script)
            self.db.commit()
            self.db.refresh(script)

            logger.info(f"Generated script from theme: {theme_name} (ID: {script.id})")
            return script

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate script from theme: {e}")
            raise

    async def generate_from_manual_subject(
        self,
        subject: str
    ) -> VideoScript:
        """
        Generate script from manual subject input

        Args:
            subject: The topic/subject provided by user

        Returns:
            Created VideoScript instance
        """
        try:
            # Generate script content using Gemini
            script_data = await self.gemini_service.generate_script_from_subject(
                subject=subject,
                min_duration_seconds=180
            )

            # Create database record
            script = VideoScript(
                id=uuid.uuid4(),
                theme_id=None,
                title=f"Video Script: {subject[:50]}...",
                content=script_data["content"],
                estimated_duration=script_data["estimated_duration"],
                format_type=FormatTypeEnum.conversational,
                speaker_count=2,
                input_source=InputSourceEnum.manual_subject,
                manual_input=subject
            )

            self.db.add(script)
            self.db.commit()
            self.db.refresh(script)

            logger.info(f"Generated script from manual subject: {subject[:50]} (ID: {script.id})")
            return script

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate script from manual subject: {e}")
            raise

    async def process_manual_script(
        self,
        script_content: str
    ) -> VideoScript:
        """
        Process a complete manual script

        Args:
            script_content: The complete script provided by user

        Returns:
            Created VideoScript instance
        """
        try:
            # Process script using Gemini service
            script_data = await self.gemini_service.process_manual_script(script_content)

            # Validate minimum duration
            if script_data["estimated_duration"] < 180:
                raise ValueError("Script too short - must be at least 3 minutes (180 seconds)")

            # Extract title from first few words
            first_line = script_content.split('\n')[0]
            title = first_line[:100] if first_line else "Manual Script"

            # Create database record
            script = VideoScript(
                id=uuid.uuid4(),
                theme_id=None,
                title=title,
                content=script_content,
                estimated_duration=script_data["estimated_duration"],
                format_type=FormatTypeEnum.conversational,
                speaker_count=2,
                input_source=InputSourceEnum.manual_script,
                manual_input=script_content
            )

            self.db.add(script)
            self.db.commit()
            self.db.refresh(script)

            logger.info(f"Processed manual script (ID: {script.id})")
            return script

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process manual script: {e}")
            raise

    def get_script_by_id(self, script_id: str) -> Optional[VideoScript]:
        """Get script by ID"""
        try:
            return self.db.query(VideoScript).filter(
                VideoScript.id == uuid.UUID(script_id)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get script {script_id}: {e}")
            return None

    def validate_script_duration(self, script: VideoScript) -> bool:
        """Validate that script meets minimum duration requirement"""
        return script.estimated_duration >= 180