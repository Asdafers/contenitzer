import asyncio
import logging
import os
from typing import Dict, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import traceback

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of an async task execution"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: int = 0  # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "progress": self.progress,
            "metadata": self.metadata
        }


class AsyncTaskManager:
    """Manages async task execution and tracking"""

    def __init__(self):
        self.tasks: Dict[str, TaskResult] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def submit_task(
        self,
        func: Callable,
        *args,
        task_name: str = None,
        **kwargs
    ) -> str:
        """
        Submit an async task for execution

        Args:
            func: Async function to execute
            *args: Function arguments
            task_name: Optional task name for identification
            **kwargs: Function keyword arguments

        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())

        # Create task result
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING,
            metadata={"name": task_name or func.__name__}
        )
        self.tasks[task_id] = task_result

        # Create and start asyncio task
        async_task = asyncio.create_task(
            self._execute_task(task_id, func, *args, **kwargs)
        )
        self.running_tasks[task_id] = async_task

        logger.info(f"Submitted task {task_id}: {task_name or func.__name__}")
        return task_id

    async def _execute_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """Execute a task with error handling and tracking"""
        task_result = self.tasks[task_id]

        try:
            task_result.status = TaskStatus.RUNNING
            task_result.start_time = datetime.now()

            logger.info(f"Starting task {task_id}: {task_result.metadata.get('name')}")

            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Task completed successfully
            task_result.status = TaskStatus.COMPLETED
            task_result.result = result
            task_result.progress = 100
            task_result.end_time = datetime.now()

            logger.info(f"Completed task {task_id} in {task_result.duration:.2f}s")

        except asyncio.CancelledError:
            task_result.status = TaskStatus.CANCELLED
            task_result.end_time = datetime.now()
            logger.warning(f"Task {task_id} was cancelled")
            raise

        except Exception as e:
            task_result.status = TaskStatus.FAILED
            task_result.error = str(e)
            task_result.end_time = datetime.now()

            error_trace = traceback.format_exc()
            logger.error(f"Task {task_id} failed: {e}\n{error_trace}")

        finally:
            # Clean up running task reference
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """Get task status and result"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, TaskResult]:
        """Get all tasks"""
        return self.tasks.copy()

    def get_running_tasks(self) -> Dict[str, TaskResult]:
        """Get currently running tasks"""
        running = {}
        for task_id, task_result in self.tasks.items():
            if task_result.status == TaskStatus.RUNNING:
                running[task_id] = task_result
        return running

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.running_tasks:
            async_task = self.running_tasks[task_id]
            async_task.cancel()

            try:
                await async_task
            except asyncio.CancelledError:
                pass

            logger.info(f"Cancelled task {task_id}")
            return True

        return False

    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Remove old completed tasks"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []

        for task_id, task_result in self.tasks.items():
            if (task_result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task_result.end_time and task_result.end_time < cutoff_time):
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old tasks")

        return len(to_remove)

    def update_task_progress(self, task_id: str, progress: int, metadata: Dict[str, Any] = None):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = max(0, min(100, progress))
            if metadata:
                self.tasks[task_id].metadata.update(metadata)


class TaskProgressTracker:
    """Helper for tracking task progress within long-running operations"""

    def __init__(self, task_manager: AsyncTaskManager, task_id: str):
        self.task_manager = task_manager
        self.task_id = task_id
        self.total_steps = 0
        self.current_step = 0

    def set_total_steps(self, total: int):
        """Set total number of steps for progress calculation"""
        self.total_steps = total
        self.current_step = 0

    def update_progress(self, step_name: str = None, metadata: Dict[str, Any] = None):
        """Update progress by one step"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100) if self.total_steps > 0 else 0

        update_metadata = {"current_step": step_name or f"Step {self.current_step}"}
        if metadata:
            update_metadata.update(metadata)

        self.task_manager.update_task_progress(
            self.task_id,
            progress,
            update_metadata
        )

        logger.debug(f"Task {self.task_id} progress: {progress}% - {step_name}")

    def set_progress(self, progress: int, step_name: str = None, metadata: Dict[str, Any] = None):
        """Set progress directly"""
        update_metadata = {"current_step": step_name or f"Progress: {progress}%"}
        if metadata:
            update_metadata.update(metadata)

        self.task_manager.update_task_progress(
            self.task_id,
            progress,
            update_metadata
        )


# Global task manager instance
task_manager = AsyncTaskManager()


# Convenience functions for common task patterns
async def run_media_generation_task(script_id: str) -> str:
    """Submit media generation as async task"""
    from ..services.media_service import MediaService
    from ..services.gemini_service import GeminiService
    from .database import get_db_session

    async def media_generation_wrapper():
        with get_db_session() as db:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            gemini_service = GeminiService(api_key=api_key)
            media_service = MediaService(db=db, gemini_service=gemini_service)
            return await media_service.generate_media_assets(script_id)

    return await task_manager.submit_task(
        media_generation_wrapper,
        task_name=f"media_generation_{script_id}"
    )


async def run_video_composition_task(project_id: str) -> str:
    """Submit video composition as async task"""
    from ..services.video_service import VideoService
    from .database import get_db_session

    async def video_composition_wrapper():
        with get_db_session() as db:
            video_service = VideoService(db=db)
            return await video_service.compose_video(project_id)

    return await task_manager.submit_task(
        video_composition_wrapper,
        task_name=f"video_composition_{project_id}"
    )


async def run_youtube_upload_task(project_id: str, youtube_api_key: str, **upload_params) -> str:
    """Submit YouTube upload as async task"""
    from ..services.upload_service import UploadService
    from .database import get_db_session

    async def youtube_upload_wrapper():
        with get_db_session() as db:
            upload_service = UploadService(db=db)
            return await upload_service.upload_to_youtube(
                project_id=project_id,
                youtube_api_key=youtube_api_key,
                **upload_params
            )

    return await task_manager.submit_task(
        youtube_upload_wrapper,
        task_name=f"youtube_upload_{project_id}"
    )