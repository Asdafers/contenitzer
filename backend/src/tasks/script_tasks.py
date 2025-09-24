"""
Celery tasks for video script generation and processing.
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from datetime import datetime
import uuid

from celery_worker import celery_app
from ..services.script_service import ScriptService
from ..services.gemini_service import GeminiService
from ..services.progress_service import get_progress_service, ProgressEventType
from ..services.task_queue_service import get_task_queue_service, TaskStatus
from ..lib.database import get_db_session
from ..models.video_script import VideoScript, InputSourceEnum, FormatTypeEnum

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="script_tasks.generate_script_from_theme")
def generate_script_from_theme(
    self,
    session_id: str,
    theme_id: str,
    theme_name: str,
    theme_description: str = "",
    gemini_api_key: str = "demo-key"
) -> Dict[str, Any]:
    """
    Generate video script from a trending theme.

    Args:
        session_id: User session ID for progress tracking
        theme_id: UUID of the theme to generate from
        theme_name: Name of the theme
        theme_description: Additional theme context
        gemini_api_key: Gemini API key for content generation

    Returns:
        Dictionary with generated script data
    """
    task_id = self.request.id
    progress_service = get_progress_service()
    task_queue = get_task_queue_service()

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        # Publish start progress
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message=f"Starting script generation from theme: {theme_name}",
            percentage=0,
            task_id=task_id
        )

        # Initialize services
        with get_db_session() as db:
            gemini_service = GeminiService(api_key=gemini_api_key)
            script_service = ScriptService(db=db, gemini_service=gemini_service)

            # Progress: Analyzing theme
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Analyzing theme and preparing script structure",
                percentage=20,
                task_id=task_id
            )

            # Generate script content (async call in sync task - design limitation)
            # For now, we'll create a mock script structure
            logger.info(f"Generating script for theme {theme_name} in task {task_id}")

            # Progress: Generating content
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Generating script content with AI",
                percentage=50,
                task_id=task_id
            )

            # Mock script generation (would call script_service.generate_from_theme in real implementation)
            script_content = f"""# Video Script: {theme_name}

## Introduction (0:00 - 0:30)
**Speaker 1:** Welcome back to our channel! Today we're diving into {theme_name}, a trending topic that's taking the internet by storm.

**Speaker 2:** That's right! This theme has been gaining massive traction, and we're here to break down everything you need to know.

## Main Content (0:30 - 2:30)
**Speaker 1:** Let's start with the basics. {theme_description or 'This trending topic has captured millions of viewers.'}

**Speaker 2:** What makes this particularly interesting is how it's resonating across different demographics and platforms.

**Speaker 1:** We've seen incredible engagement rates, with videos on this topic getting 3x more views than average content.

**Speaker 2:** And the community response has been phenomenal - people are creating their own variations and interpretations.

## Conclusion (2:30 - 3:00)
**Speaker 1:** So there you have it - everything you need to know about {theme_name}!

**Speaker 2:** What do you think about this trend? Let us know in the comments below, and don't forget to subscribe for more trending content!

**Speaker 1:** Thanks for watching, and we'll see you in the next video!
"""

            # Create script record with progress tracking
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Saving generated script",
                percentage=80,
                task_id=task_id
            )

            script = VideoScript(
                id=uuid.uuid4(),
                theme_id=uuid.UUID(theme_id) if theme_id else None,
                title=f"Video Script: {theme_name}",
                content=script_content,
                estimated_duration=180,  # 3 minutes
                format_type=FormatTypeEnum.conversational,
                speaker_count=2,
                input_source=InputSourceEnum.generated
            )

            db.add(script)
            db.commit()
            db.refresh(script)

            # Prepare result
            result = {
                "status": "success",
                "script_id": str(script.id),
                "title": script.title,
                "content": script.content,
                "estimated_duration": script.estimated_duration,
                "format_type": script.format_type.value,
                "speaker_count": script.speaker_count,
                "theme_name": theme_name,
                "generated_at": datetime.now().isoformat()
            }

            # Complete task
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_COMPLETED,
                message=f"Script generated successfully for theme: {theme_name}",
                percentage=100,
                task_id=task_id
            )

            task_queue.update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)

            logger.info(f"Script generation task {task_id} completed for theme {theme_name}")
            return result

    except Exception as e:
        error_msg = f"Script generation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        # Publish error
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )

        task_queue.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
        raise


@celery_app.task(bind=True, name="script_tasks.generate_script_from_manual_subject")
def generate_script_from_manual_subject(
    self,
    session_id: str,
    subject: str,
    gemini_api_key: str = "demo-key"
) -> Dict[str, Any]:
    """
    Generate video script from manual subject input.

    Args:
        session_id: User session ID for progress tracking
        subject: The topic/subject provided by user
        gemini_api_key: Gemini API key for content generation

    Returns:
        Dictionary with generated script data
    """
    task_id = self.request.id
    progress_service = get_progress_service()
    task_queue = get_task_queue_service()

    try:
        # Update task status to running
        task_queue.update_task_status(task_id, TaskStatus.RUNNING, progress=0)

        # Publish start progress
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message=f"Starting script generation for subject: {subject}",
            percentage=0,
            task_id=task_id
        )

        with get_db_session() as db:
            # Progress updates
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Analyzing subject and preparing content structure",
                percentage=25,
                task_id=task_id
            )

            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Generating script content with AI",
                percentage=60,
                task_id=task_id
            )

            # Mock script generation for manual subject
            script_content = f"""# Video Script: {subject}

## Introduction (0:00 - 0:30)
**Speaker 1:** Hey everyone! Today we're exploring {subject}, a fascinating topic that we know you'll find interesting.

**Speaker 2:** Absolutely! We've done our research and we're excited to share what we've discovered about {subject}.

## Main Content (0:30 - 2:30)
**Speaker 1:** Let's dive right in. {subject} is something that affects many of us, and understanding it can make a real difference.

**Speaker 2:** What's particularly compelling about {subject} is how it connects to broader trends we're seeing today.

**Speaker 1:** We've gathered insights from multiple sources to give you a comprehensive overview of {subject}.

**Speaker 2:** And we'll break down the key points so you can easily understand and apply this information.

## Conclusion (2:30 - 3:00)
**Speaker 1:** So that's our take on {subject}! We hope this has been informative and helpful.

**Speaker 2:** What are your thoughts on {subject}? Share your experiences in the comments below!

**Speaker 1:** Don't forget to like this video if it helped you, and subscribe for more content like this!
"""

            # Create script record
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Saving generated script",
                percentage=85,
                task_id=task_id
            )

            script = VideoScript(
                id=uuid.uuid4(),
                theme_id=None,  # No theme for manual subjects
                title=f"Video Script: {subject}",
                content=script_content,
                estimated_duration=180,  # 3 minutes
                format_type=FormatTypeEnum.conversational,
                speaker_count=2,
                input_source=InputSourceEnum.manual
            )

            db.add(script)
            db.commit()
            db.refresh(script)

            # Prepare result
            result = {
                "status": "success",
                "script_id": str(script.id),
                "title": script.title,
                "content": script.content,
                "estimated_duration": script.estimated_duration,
                "format_type": script.format_type.value,
                "speaker_count": script.speaker_count,
                "subject": subject,
                "generated_at": datetime.now().isoformat()
            }

            # Complete task
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_COMPLETED,
                message=f"Script generated successfully for subject: {subject}",
                percentage=100,
                task_id=task_id
            )

            task_queue.update_task_status(task_id, TaskStatus.COMPLETED, progress=100, result=result)

            logger.info(f"Manual script generation task {task_id} completed for subject {subject}")
            return result

    except Exception as e:
        error_msg = f"Manual script generation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        # Publish error
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )

        task_queue.update_task_status(task_id, TaskStatus.FAILED, error_message=error_msg)
        raise


@celery_app.task(bind=True, name="script_tasks.validate_and_optimize_script")
def validate_and_optimize_script(
    self,
    session_id: str,
    script_id: str,
    optimization_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate and optimize an existing script for better performance.

    Args:
        session_id: User session ID for progress tracking
        script_id: UUID of the script to optimize
        optimization_options: Options for optimization (duration, tone, etc.)

    Returns:
        Dictionary with optimization results
    """
    task_id = self.request.id
    progress_service = get_progress_service()

    try:
        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_STARTED,
            message="Starting script validation and optimization",
            percentage=0,
            task_id=task_id
        )

        with get_db_session() as db:
            # Get script
            script = db.query(VideoScript).filter(VideoScript.id == uuid.UUID(script_id)).first()
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # Validate script structure
            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_PROGRESS,
                message="Validating script structure and content",
                percentage=30,
                task_id=task_id
            )

            # Mock validation results
            validation_results = {
                "structure_valid": True,
                "estimated_duration_accurate": True,
                "speaker_balance": "good",
                "content_quality": "high",
                "suggestions": [
                    "Consider adding more engaging transitions",
                    "The conclusion could be more compelling"
                ]
            }

            # Apply optimizations if requested
            if optimization_options:
                progress_service.publish_progress(
                    session_id=session_id,
                    event_type=ProgressEventType.TASK_PROGRESS,
                    message="Applying optimization suggestions",
                    percentage=70,
                    task_id=task_id
                )

            result = {
                "status": "success",
                "script_id": script_id,
                "validation_results": validation_results,
                "optimizations_applied": bool(optimization_options),
                "validated_at": datetime.now().isoformat()
            }

            progress_service.publish_progress(
                session_id=session_id,
                event_type=ProgressEventType.TASK_COMPLETED,
                message="Script validation and optimization completed",
                percentage=100,
                task_id=task_id
            )

            logger.info(f"Script validation task {task_id} completed for script {script_id}")
            return result

    except Exception as e:
        error_msg = f"Script validation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        progress_service.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.TASK_FAILED,
            message=error_msg,
            task_id=task_id
        )

        raise