"""
Redis-based task queue service for managing background tasks and job processing.
Handles task queuing, status tracking, and result storage with TTL management.
"""
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Literal
from enum import Enum

from ..lib.redis import RedisService, RedisConfig

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(str, Enum):
    """Task priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TaskType(str, Enum):
    """Task type enumeration"""
    SCRIPT_GENERATION = "script_generation"
    MEDIA_GENERATION = "media_generation"
    VIDEO_COMPOSITION = "video_composition"
    YOUTUBE_UPLOAD = "youtube_upload"
    TRENDING_ANALYSIS = "trending_analysis"
    THEME_EXTRACTION = "theme_extraction"

class TaskQueueServiceError(Exception):
    """Custom exception for task queue service operations"""
    pass

class TaskQueueService(RedisService):
    """Redis service for task queue management"""

    def __init__(self):
        """Initialize task queue service with Redis connection"""
        super().__init__(RedisConfig.TASK_PREFIX)
        logger.info("TaskQueueService initialized")

    def submit_task(
        self,
        task_type: TaskType,
        input_data: Dict[str, Any],
        session_id: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a new task to the queue

        Args:
            task_type: Type of task to execute
            input_data: Task input parameters
            session_id: Associated session ID
            priority: Task priority level
            metadata: Additional task metadata

        Returns:
            task_id: New task UUID

        Raises:
            TaskQueueServiceError: If task submission fails
        """
        try:
            task_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            task_data = {
                "task_id": task_id,
                "task_type": task_type.value,
                "status": TaskStatus.PENDING.value,
                "priority": priority.value,
                "session_id": session_id,
                "input_data": input_data,
                "metadata": metadata or {},
                "created_at": now,
                "updated_at": now,
                "started_at": None,
                "completed_at": None,
                "result": None,
                "error_message": None,
                "retry_count": 0,
                "max_retries": 3,
                "progress": 0,
                "estimated_duration": None,
                "worker_id": None
            }

            success = self.set_json(task_id, task_data, RedisConfig.TASK_TTL)

            if not success:
                raise TaskQueueServiceError(f"Failed to store task data for {task_id}")

            # Add to priority queue
            self._add_to_priority_queue(task_id, priority)

            logger.info(f"Submitted task {task_id} of type {task_type} for session {session_id}")
            return task_id

        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise TaskQueueServiceError(f"Task submission failed: {e}")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve task data by ID

        Args:
            task_id: Task UUID

        Returns:
            Task data dictionary or None if not found
        """
        try:
            task_data = self.get_json(task_id)

            if not task_data:
                logger.debug(f"Task {task_id} not found")
                return None

            logger.debug(f"Retrieved task {task_id}")
            return task_data

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        worker_id: Optional[str] = None
    ) -> bool:
        """
        Update task status and related fields

        Args:
            task_id: Task UUID
            status: New task status
            progress: Task progress percentage (0-100)
            result: Task result data (for completed tasks)
            error_message: Error message (for failed tasks)
            worker_id: Worker processing the task

        Returns:
            True if update successful, False otherwise
        """
        try:
            task_data = self.get_json(task_id)

            if not task_data:
                logger.warning(f"Task {task_id} not found for status update")
                return False

            now = datetime.now(timezone.utc).isoformat()

            # Update status and timestamp
            task_data["status"] = status.value
            task_data["updated_at"] = now

            # Update specific fields based on status
            if status == TaskStatus.RUNNING and not task_data["started_at"]:
                task_data["started_at"] = now
                task_data["worker_id"] = worker_id

            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task_data["completed_at"] = now
                if result:
                    task_data["result"] = result
                if error_message:
                    task_data["error_message"] = error_message

            elif status == TaskStatus.RETRYING:
                task_data["retry_count"] = task_data.get("retry_count", 0) + 1

            # Update progress
            if progress is not None:
                task_data["progress"] = min(100, max(0, progress))

            success = self.set_json(task_id, task_data, RedisConfig.TASK_TTL)

            if success:
                logger.info(f"Updated task {task_id} status to {status}")
                # Remove from priority queue if completed/failed/cancelled
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    self._remove_from_priority_queue(task_id)
            else:
                logger.error(f"Failed to update task {task_id} status")

            return success

        except Exception as e:
            logger.error(f"Failed to update task {task_id} status: {e}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task

        Args:
            task_id: Task UUID

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            task_data = self.get_json(task_id)

            if not task_data:
                logger.warning(f"Task {task_id} not found for cancellation")
                return False

            current_status = TaskStatus(task_data["status"])

            # Only allow cancellation of pending or running tasks
            if current_status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                logger.warning(f"Task {task_id} cannot be cancelled in status {current_status}")
                return False

            success = self.update_task_status(task_id, TaskStatus.CANCELLED)

            if success:
                logger.info(f"Cancelled task {task_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

    def retry_task(self, task_id: str) -> bool:
        """
        Retry a failed task

        Args:
            task_id: Task UUID

        Returns:
            True if retry successful, False otherwise
        """
        try:
            task_data = self.get_json(task_id)

            if not task_data:
                logger.warning(f"Task {task_id} not found for retry")
                return False

            current_status = TaskStatus(task_data["status"])
            retry_count = task_data.get("retry_count", 0)
            max_retries = task_data.get("max_retries", 3)

            # Only allow retry of failed tasks within retry limit
            if current_status != TaskStatus.FAILED:
                logger.warning(f"Task {task_id} cannot be retried in status {current_status}")
                return False

            if retry_count >= max_retries:
                logger.warning(f"Task {task_id} has exceeded max retries ({max_retries})")
                return False

            # Reset task for retry
            success = self.update_task_status(task_id, TaskStatus.PENDING)

            if success:
                # Re-add to priority queue
                priority = TaskPriority(task_data.get("priority", TaskPriority.NORMAL.value))
                self._add_to_priority_queue(task_id, priority)
                logger.info(f"Retrying task {task_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {e}")
            return False

    def list_tasks(
        self,
        session_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional filtering

        Args:
            session_id: Filter by session ID
            status: Filter by task status
            task_type: Filter by task type
            limit: Maximum number of tasks to return

        Returns:
            List of task data dictionaries
        """
        try:
            all_keys = self.get_keys_by_pattern("*")
            tasks = []

            for task_id in all_keys:
                if len(tasks) >= limit:
                    break

                task_data = self.get_json(task_id)
                if not task_data:
                    continue

                # Apply filters
                if session_id and task_data.get("session_id") != session_id:
                    continue

                if status and task_data.get("status") != status.value:
                    continue

                if task_type and task_data.get("task_type") != task_type.value:
                    continue

                tasks.append(task_data)

            # Sort by created_at (newest first)
            tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            logger.debug(f"Listed {len(tasks)} tasks with filters: session_id={session_id}, status={status}, task_type={task_type}")
            return tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

    def get_next_task(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get next pending task for worker to process (priority queue)

        Args:
            worker_id: ID of worker requesting task

        Returns:
            Task data dictionary or None if no tasks available
        """
        try:
            # Check priority queues in order (urgent, high, normal, low)
            for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                queue_key = f"queue:{priority.value}"
                task_id = self.client.lpop(self._make_key(queue_key))

                if task_id:
                    task_data = self.get_json(task_id)
                    if task_data and task_data.get("status") == TaskStatus.PENDING.value:
                        # Mark as running
                        self.update_task_status(task_id, TaskStatus.RUNNING, worker_id=worker_id)
                        logger.info(f"Assigned task {task_id} to worker {worker_id}")
                        return task_data

            logger.debug(f"No tasks available for worker {worker_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to get next task for worker {worker_id}: {e}")
            return None

    def cleanup_expired_tasks(self) -> int:
        """
        Clean up expired tasks and stale queue entries

        Returns:
            Number of tasks cleaned up
        """
        try:
            all_keys = self.get_keys_by_pattern("*")
            cleaned_count = 0

            for task_id in all_keys:
                if not self.exists(task_id):
                    cleaned_count += 1

            # Clean up priority queues
            for priority in TaskPriority:
                queue_key = f"queue:{priority.value}"
                # Remove stale task IDs from queues
                queue_items = self.client.lrange(self._make_key(queue_key), 0, -1)
                for task_id in queue_items:
                    if not self.exists(task_id):
                        self.client.lrem(self._make_key(queue_key), 0, task_id)

            logger.info(f"Cleaned up {cleaned_count} expired tasks")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired tasks: {e}")
            return 0

    def _add_to_priority_queue(self, task_id: str, priority: TaskPriority):
        """Add task to priority queue"""
        try:
            queue_key = f"queue:{priority.value}"
            self.client.rpush(self._make_key(queue_key), task_id)
            logger.debug(f"Added task {task_id} to {priority.value} priority queue")

        except Exception as e:
            logger.error(f"Failed to add task {task_id} to priority queue: {e}")

    def _remove_from_priority_queue(self, task_id: str):
        """Remove task from all priority queues"""
        try:
            for priority in TaskPriority:
                queue_key = f"queue:{priority.value}"
                self.client.lrem(self._make_key(queue_key), 0, task_id)

            logger.debug(f"Removed task {task_id} from priority queues")

        except Exception as e:
            logger.error(f"Failed to remove task {task_id} from priority queues: {e}")

# Global service instance
_task_queue_service: Optional[TaskQueueService] = None

def get_task_queue_service() -> TaskQueueService:
    """Get global task queue service instance"""
    global _task_queue_service

    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()

    return _task_queue_service