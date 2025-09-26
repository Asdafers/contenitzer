"""
Redis-based progress event service for real-time progress tracking and notifications.
Handles progress updates, event publishing, and real-time communication with UI.
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from ..lib.redis import RedisService, RedisConfig, get_redis_client

logger = logging.getLogger(__name__)

class ProgressEventType(str, Enum):
    """Progress event type enumeration"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    WORKFLOW_STEP = "workflow_step"
    MEDIA_GENERATION = "media_generation"
    UPLOAD_PROGRESS = "upload_progress"
    ERROR_OCCURRED = "error_occurred"
    INFO_MESSAGE = "info_message"

    # Video generation specific events
    VIDEO_GENERATION_STARTED = "video_generation_started"
    VIDEO_GENERATION_PROGRESS = "video_generation_progress"
    VIDEO_GENERATION_COMPLETED = "video_generation_completed"
    VIDEO_GENERATION_FAILED = "video_generation_failed"
    MEDIA_ASSET_CREATED = "media_asset_created"
    VIDEO_COMPOSITION_STARTED = "video_composition_started"
    VIDEO_COMPOSITION_PROGRESS = "video_composition_progress"
    VIDEO_COMPOSITION_COMPLETED = "video_composition_completed"
    VIDEO_FILE_READY = "video_file_ready"

    # AI processing specific events
    AI_SCRIPT_ANALYSIS_STARTED = "ai_script_analysis_started"
    AI_SCRIPT_ANALYSIS_PROGRESS = "ai_script_analysis_progress"
    AI_SCRIPT_ANALYSIS_COMPLETED = "ai_script_analysis_completed"
    AI_IMAGE_GENERATION_STARTED = "ai_image_generation_started"
    AI_IMAGE_GENERATION_PROGRESS = "ai_image_generation_progress"
    AI_IMAGE_GENERATION_COMPLETED = "ai_image_generation_completed"
    AI_AUDIO_GENERATION_STARTED = "ai_audio_generation_started"
    AI_AUDIO_GENERATION_PROGRESS = "ai_audio_generation_progress"
    AI_AUDIO_GENERATION_COMPLETED = "ai_audio_generation_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

class ProgressServiceError(Exception):
    """Custom exception for progress service operations"""
    pass

class ProgressService(RedisService):
    """Redis service for progress event management"""

    def __init__(self):
        """Initialize progress service with Redis connection"""
        super().__init__(RedisConfig.PROGRESS_PREFIX)
        self.pubsub_client = get_redis_client()
        logger.info("ProgressService initialized")

    def publish_progress(
        self,
        session_id: str,
        event_type: ProgressEventType,
        message: str,
        percentage: Optional[int] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish a progress event and store it

        Args:
            session_id: Associated session ID
            event_type: Type of progress event
            message: Human-readable progress message
            percentage: Progress percentage (0-100)
            task_id: Associated task ID (optional)
            metadata: Additional event metadata

        Returns:
            event_id: New event UUID

        Raises:
            ProgressServiceError: If event publishing fails
        """
        try:
            event_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            event_data = {
                "event_id": event_id,
                "session_id": session_id,
                "task_id": task_id,
                "event_type": event_type.value,
                "message": message,
                "percentage": percentage,
                "metadata": metadata or {},
                "timestamp": now,
                "read": False
            }

            # Store event with short TTL (progress events are transient)
            success = self.set_json(event_id, event_data, RedisConfig.PROGRESS_TTL)

            if not success:
                raise ProgressServiceError(f"Failed to store progress event {event_id}")

            # Publish to Redis pub/sub for real-time updates
            self._publish_to_channel(session_id, event_data)

            # Store in session-specific progress log
            self._add_to_session_progress(session_id, event_id)

            logger.debug(f"Published progress event {event_id} for session {session_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to publish progress event: {e}")
            raise ProgressServiceError(f"Progress event publishing failed: {e}")

    def get_progress_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve progress event by ID

        Args:
            event_id: Event UUID

        Returns:
            Event data dictionary or None if not found
        """
        try:
            event_data = self.get_json(event_id)

            if not event_data:
                logger.debug(f"Progress event {event_id} not found")
                return None

            logger.debug(f"Retrieved progress event {event_id}")
            return event_data

        except Exception as e:
            logger.error(f"Failed to get progress event {event_id}: {e}")
            return None

    def get_session_progress(
        self,
        session_id: str,
        limit: int = 50,
        event_type: Optional[ProgressEventType] = None,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get progress events for a session

        Args:
            session_id: Session ID
            limit: Maximum number of events to return
            event_type: Filter by event type
            unread_only: Only return unread events

        Returns:
            List of progress event dictionaries
        """
        try:
            # Get session progress list
            progress_key = f"session_progress:{session_id}"
            event_ids = self.client.lrange(self._make_key(progress_key), 0, limit - 1)

            events = []
            for event_id in event_ids:
                event_data = self.get_json(event_id)
                if not event_data:
                    continue

                # Apply filters
                if event_type and event_data.get("event_type") != event_type.value:
                    continue

                if unread_only and event_data.get("read", False):
                    continue

                events.append(event_data)

            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            logger.debug(f"Retrieved {len(events)} progress events for session {session_id}")
            return events

        except Exception as e:
            logger.error(f"Failed to get session progress for {session_id}: {e}")
            return []

    def get_task_progress(
        self,
        task_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get progress events for a specific task

        Args:
            task_id: Task ID
            limit: Maximum number of events to return

        Returns:
            List of progress event dictionaries
        """
        try:
            # Get task progress list
            progress_key = f"task_progress:{task_id}"
            event_ids = self.client.lrange(self._make_key(progress_key), 0, limit - 1)

            events = []
            for event_id in event_ids:
                event_data = self.get_json(event_id)
                if event_data:
                    events.append(event_data)

            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            logger.debug(f"Retrieved {len(events)} progress events for task {task_id}")
            return events

        except Exception as e:
            logger.error(f"Failed to get task progress for {task_id}: {e}")
            return []

    def mark_progress_read(self, event_id: str) -> bool:
        """
        Mark a progress event as read

        Args:
            event_id: Event UUID

        Returns:
            True if marking successful, False otherwise
        """
        try:
            event_data = self.get_json(event_id)

            if not event_data:
                logger.warning(f"Progress event {event_id} not found for read marking")
                return False

            event_data["read"] = True
            success = self.set_json(event_id, event_data, RedisConfig.PROGRESS_TTL)

            if success:
                logger.debug(f"Marked progress event {event_id} as read")

            return success

        except Exception as e:
            logger.error(f"Failed to mark progress event {event_id} as read: {e}")
            return False

    def mark_session_progress_read(self, session_id: str) -> int:
        """
        Mark all progress events for a session as read

        Args:
            session_id: Session ID

        Returns:
            Number of events marked as read
        """
        try:
            events = self.get_session_progress(session_id, unread_only=True)
            marked_count = 0

            for event in events:
                if self.mark_progress_read(event["event_id"]):
                    marked_count += 1

            logger.info(f"Marked {marked_count} progress events as read for session {session_id}")
            return marked_count

        except Exception as e:
            logger.error(f"Failed to mark session progress as read for {session_id}: {e}")
            return 0

    def subscribe_to_progress(self, session_id: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to real-time progress updates for a session

        Args:
            session_id: Session ID to subscribe to
            callback: Function to call when progress event received

        Note:
            This is a blocking operation and should be run in a separate thread/process
        """
        try:
            pubsub = self.pubsub_client.pubsub()
            channel = f"{RedisConfig.PROGRESS_CHANNEL}:{session_id}"
            pubsub.subscribe(channel)

            logger.info(f"Subscribed to progress updates for session {session_id}")

            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        callback(event_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode progress message: {e}")
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")

        except Exception as e:
            logger.error(f"Failed to subscribe to progress for {session_id}: {e}")

    def clear_session_progress(self, session_id: str) -> bool:
        """
        Clear all progress events for a session

        Args:
            session_id: Session ID

        Returns:
            True if clearing successful, False otherwise
        """
        try:
            # Get all event IDs for the session
            progress_key = f"session_progress:{session_id}"
            event_ids = self.client.lrange(self._make_key(progress_key), 0, -1)

            # Delete individual events
            deleted_count = 0
            for event_id in event_ids:
                if self.delete(event_id):
                    deleted_count += 1

            # Clear the progress list
            self.client.delete(self._make_key(progress_key))

            logger.info(f"Cleared {deleted_count} progress events for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear progress for session {session_id}: {e}")
            return False

    def cleanup_expired_progress(self) -> int:
        """
        Clean up expired progress events and stale progress lists

        Returns:
            Number of events cleaned up
        """
        try:
            # Clean up expired individual events
            all_keys = self.get_keys_by_pattern("*")
            cleaned_count = 0

            for event_id in all_keys:
                if not self.exists(event_id):
                    cleaned_count += 1

            # Clean up progress lists
            progress_list_keys = self.get_keys_by_pattern("session_progress:*")
            progress_list_keys.extend(self.get_keys_by_pattern("task_progress:*"))

            for list_key in progress_list_keys:
                redis_key = self._make_key(list_key)
                event_ids = self.client.lrange(redis_key, 0, -1)

                # Remove stale event IDs from lists
                for event_id in event_ids:
                    if not self.exists(event_id):
                        self.client.lrem(redis_key, 0, event_id)

            logger.info(f"Cleaned up {cleaned_count} expired progress events")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired progress events: {e}")
            return 0

    def _publish_to_channel(self, session_id: str, event_data: Dict[str, Any]):
        """Publish event to Redis pub/sub channel"""
        try:
            channel = f"{RedisConfig.PROGRESS_CHANNEL}:{session_id}"
            message = json.dumps(event_data, default=str)
            self.pubsub_client.publish(channel, message)
            logger.debug(f"Published to channel {channel}")

        except Exception as e:
            logger.error(f"Failed to publish to channel: {e}")

    def _add_to_session_progress(self, session_id: str, event_id: str):
        """Add event to session progress list"""
        try:
            progress_key = f"session_progress:{session_id}"
            self.client.lpush(self._make_key(progress_key), event_id)
            # Keep only recent events (limit list size)
            self.client.ltrim(self._make_key(progress_key), 0, 99)  # Keep last 100 events
            # Set TTL on progress list
            self.client.expire(self._make_key(progress_key), RedisConfig.PROGRESS_TTL)

        except Exception as e:
            logger.error(f"Failed to add event to session progress: {e}")

    def _add_to_task_progress(self, task_id: str, event_id: str):
        """Add event to task progress list"""
        try:
            progress_key = f"task_progress:{task_id}"
            self.client.lpush(self._make_key(progress_key), event_id)
            # Keep only recent events (limit list size)
            self.client.ltrim(self._make_key(progress_key), 0, 49)  # Keep last 50 events
            # Set TTL on progress list
            self.client.expire(self._make_key(progress_key), RedisConfig.PROGRESS_TTL)

        except Exception as e:
            logger.error(f"Failed to add event to task progress: {e}")

    # Video generation specific convenience methods
    def publish_video_generation_started(
        self,
        session_id: str,
        job_id: str,
        script_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish video generation started event."""
        video_metadata = {
            "job_id": job_id,
            "script_id": script_id,
            "stage": "initialization",
            **(metadata or {})
        }

        return self.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.VIDEO_GENERATION_STARTED,
            message=f"Starting video generation for script {script_id}",
            percentage=0,
            task_id=job_id,
            metadata=video_metadata
        )

    def publish_video_generation_progress(
        self,
        session_id: str,
        job_id: str,
        stage: str,
        message: str,
        percentage: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish video generation progress event."""
        video_metadata = {
            "job_id": job_id,
            "stage": stage,
            "current_operation": message,
            **(metadata or {})
        }

        return self.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.VIDEO_GENERATION_PROGRESS,
            message=message,
            percentage=percentage,
            task_id=job_id,
            metadata=video_metadata
        )

    def publish_video_generation_completed(
        self,
        session_id: str,
        job_id: str,
        video_id: str,
        video_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish video generation completed event."""
        video_metadata = {
            "job_id": job_id,
            "video_id": video_id,
            "video_url": video_url,
            "stage": "completed",
            **(metadata or {})
        }

        return self.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.VIDEO_GENERATION_COMPLETED,
            message=f"Video generation completed successfully",
            percentage=100,
            task_id=job_id,
            metadata=video_metadata
        )

    def publish_video_file_ready(
        self,
        session_id: str,
        video_id: str,
        video_url: str,
        download_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish video file ready event."""
        video_metadata = {
            "video_id": video_id,
            "video_url": video_url,
            "download_url": download_url,
            "ready_for_download": True,
            **(metadata or {})
        }

        return self.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.VIDEO_FILE_READY,
            message="Video file is ready for download and streaming",
            percentage=100,
            metadata=video_metadata
        )

    def publish_media_asset_created(
        self,
        session_id: str,
        job_id: str,
        asset_type: str,
        asset_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish media asset created event."""
        asset_metadata = {
            "job_id": job_id,
            "asset_type": asset_type,
            "asset_id": asset_id,
            **(metadata or {})
        }

        return self.publish_progress(
            session_id=session_id,
            event_type=ProgressEventType.MEDIA_ASSET_CREATED,
            message=f"Created {asset_type.lower()} asset",
            task_id=job_id,
            metadata=asset_metadata
        )

# Global service instance
_progress_service: Optional[ProgressService] = None

def get_progress_service() -> ProgressService:
    """Get global progress service instance"""
    global _progress_service

    if _progress_service is None:
        _progress_service = ProgressService()

    return _progress_service