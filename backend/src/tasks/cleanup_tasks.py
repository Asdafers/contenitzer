"""
Celery tasks for file cleanup and storage management.
"""
import logging
from typing import Dict, Any, Optional
from celery import current_task
from datetime import datetime, timedelta
import uuid

from celery_worker import celery_app
from ..services.storage_manager import StorageManager, StorageManagerError
from ..services.video_generation_service import VideoGenerationService
from ..lib.database import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="cleanup_tasks.cleanup_expired_files")
def cleanup_expired_files(
    self,
    storage_type: Optional[str] = None,
    max_age_days: int = 7
) -> Dict[str, Any]:
    """
    Clean up expired files based on storage policies.

    Args:
        storage_type: Specific storage type to clean (optional)
        max_age_days: Maximum age for files before cleanup

    Returns:
        Dictionary with cleanup results
    """
    task_id = self.request.id
    storage_manager = StorageManager()

    try:
        logger.info(f"Starting file cleanup task {task_id}")

        # Convert storage_type string to enum if provided
        target_storage_type = None
        if storage_type:
            from ..models.media_storage import StorageType
            target_storage_type = StorageType(storage_type.upper())

        # Run cleanup
        cleanup_results = storage_manager.cleanup_expired_files(target_storage_type)

        # Update storage records
        usage_stats = storage_manager.scan_storage_usage()

        result = {
            "status": "success",
            "cleanup_results": cleanup_results,
            "storage_usage_after": usage_stats,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"File cleanup task {task_id} completed: "
                   f"{cleanup_results['files_removed']} files, "
                   f"{cleanup_results['bytes_freed']} bytes freed")

        return result

    except StorageManagerError as e:
        error_msg = f"Storage cleanup failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise
    except Exception as e:
        error_msg = f"Cleanup task failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise


@celery_app.task(bind=True, name="cleanup_tasks.cleanup_failed_job")
def cleanup_failed_job(
    self,
    job_id: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Clean up files and database records for a failed video generation job.

    Args:
        job_id: UUID of the failed job
        session_id: Optional session ID for context

    Returns:
        Dictionary with cleanup results
    """
    task_id = self.request.id
    video_service = VideoGenerationService()

    try:
        logger.info(f"Starting failed job cleanup for job {job_id}")

        # Cancel the job if still active
        job_cancelled = video_service.cancel_job(uuid.UUID(job_id))

        # Clean up temporary files
        video_service.video_composer.cleanup_temp_files(uuid.UUID(job_id))

        # Clean up media assets
        files_cleaned = 0
        bytes_freed = 0

        with get_db_session() as db:
            from ..models.media_asset import MediaAsset
            from pathlib import Path

            # Get all assets for this job
            assets = db.query(MediaAsset).filter(
                MediaAsset.generation_job_id == uuid.UUID(job_id)
            ).all()

            for asset in assets:
                try:
                    asset_path = Path(asset.file_path)
                    if asset_path.exists():
                        file_size = asset_path.stat().st_size
                        asset_path.unlink()
                        files_cleaned += 1
                        bytes_freed += file_size
                        logger.debug(f"Removed asset file: {asset_path}")
                except Exception as file_error:
                    logger.warning(f"Failed to remove asset file {asset.file_path}: {file_error}")

            # Remove asset database records
            for asset in assets:
                db.delete(asset)

            db.commit()

        result = {
            "status": "success",
            "job_id": job_id,
            "job_cancelled": job_cancelled,
            "files_cleaned": files_cleaned,
            "bytes_freed": bytes_freed,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"Failed job cleanup completed for {job_id}: "
                   f"{files_cleaned} files removed, {bytes_freed} bytes freed")

        return result

    except Exception as e:
        error_msg = f"Failed job cleanup failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise


@celery_app.task(bind=True, name="cleanup_tasks.enforce_storage_quotas")
def enforce_storage_quotas(self) -> Dict[str, Any]:
    """
    Enforce storage quotas by cleaning up excess files.

    Returns:
        Dictionary with quota enforcement results
    """
    task_id = self.request.id
    storage_manager = StorageManager()

    try:
        logger.info(f"Starting storage quota enforcement task {task_id}")

        # Check current storage usage
        usage_stats = storage_manager.scan_storage_usage()

        # Enforce quotas
        quota_results = storage_manager.enforce_storage_quotas()

        # Check disk space
        disk_space = storage_manager.get_available_space()

        result = {
            "status": "success",
            "quota_results": quota_results,
            "storage_usage": usage_stats,
            "disk_space": disk_space,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"Storage quota enforcement completed: "
                   f"{quota_results['quotas_enforced']} quotas enforced, "
                   f"{quota_results['bytes_freed']} bytes freed")

        return result

    except StorageManagerError as e:
        error_msg = f"Quota enforcement failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise
    except Exception as e:
        error_msg = f"Quota enforcement task failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise


@celery_app.task(bind=True, name="cleanup_tasks.cleanup_old_jobs")
def cleanup_old_jobs(
    self,
    max_age_days: int = 30,
    preserve_completed: bool = True
) -> Dict[str, Any]:
    """
    Clean up old video generation jobs and their associated data.

    Args:
        max_age_days: Maximum age for jobs before cleanup
        preserve_completed: Whether to preserve completed videos

    Returns:
        Dictionary with cleanup results
    """
    task_id = self.request.id
    video_service = VideoGenerationService()

    try:
        logger.info(f"Starting old jobs cleanup task {task_id}")

        # Use the service cleanup method
        jobs_cleaned = video_service.cleanup_expired_jobs(max_age_days)

        # Also run general file cleanup
        storage_manager = StorageManager()
        cleanup_results = storage_manager.cleanup_expired_files()

        result = {
            "status": "success",
            "jobs_cleaned": jobs_cleaned,
            "max_age_days": max_age_days,
            "preserve_completed": preserve_completed,
            "file_cleanup": cleanup_results,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"Old jobs cleanup completed: {jobs_cleaned} jobs cleaned")
        return result

    except Exception as e:
        error_msg = f"Old jobs cleanup failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")
        raise


@celery_app.task(bind=True, name="cleanup_tasks.validate_storage_health")
def validate_storage_health(self) -> Dict[str, Any]:
    """
    Validate storage system health and report issues.

    Returns:
        Dictionary with health validation results
    """
    task_id = self.request.id
    storage_manager = StorageManager()

    try:
        logger.info(f"Starting storage health validation task {task_id}")

        # Run health validation
        health_report = storage_manager.validate_storage_health()

        # Log any critical issues
        if health_report["status"] == "critical":
            logger.error(f"Critical storage issues detected: {health_report['issues']}")
        elif health_report["status"] == "warning":
            logger.warning(f"Storage warnings: {health_report['issues']}")

        result = {
            "status": "success",
            "health_report": health_report,
            "completed_at": datetime.now().isoformat()
        }

        logger.info(f"Storage health validation completed: {health_report['status']}")
        return result

    except Exception as e:
        error_msg = f"Storage health validation failed: {str(e)}"
        logger.error(f"Task {task_id} failed: {error_msg}")

        return {
            "status": "failed",
            "error": error_msg,
            "completed_at": datetime.now().isoformat()
        }