"""
Setup progress tracking service for monitoring setup steps
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from ..models.setup_progress import SetupProgress


class SetupProgressService:
    """Service for tracking and managing setup progress"""

    def __init__(self):
        self.steps: Dict[str, SetupProgress] = {}

    def start_step(self, step_id: str, step_name: str, category: str, prerequisites: List[str] = None) -> SetupProgress:
        """Start a new setup step"""
        # Check prerequisites
        if prerequisites:
            for prereq_id in prerequisites:
                if prereq_id not in self.steps or self.steps[prereq_id].status != "completed":
                    raise ValueError(f"Prerequisite step '{prereq_id}' not completed")

        step = SetupProgress(
            step_id=step_id,
            step_name=step_name,
            category=category,
            status="in_progress",
            started_at=datetime.utcnow(),
            prerequisites=prerequisites or []
        )

        self.steps[step_id] = step
        return step

    def complete_step(self, step_id: str, artifacts: Optional[Dict[str, Any]] = None) -> SetupProgress:
        """Mark a step as completed"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = "completed"
        step.completed_at = datetime.utcnow()

        if artifacts:
            step.artifacts = artifacts

        return step

    def fail_step(self, step_id: str, error_details: str) -> SetupProgress:
        """Mark a step as failed"""
        if step_id not in self.steps:
            raise ValueError(f"Step '{step_id}' not found")

        step = self.steps[step_id]
        step.status = "failed"
        step.completed_at = datetime.utcnow()
        step.error_details = error_details

        return step

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get overall progress summary"""
        total_steps = len(self.steps)
        if total_steps == 0:
            return {"total": 0, "completed": 0, "failed": 0, "in_progress": 0, "progress_percentage": 0}

        status_counts = {"completed": 0, "failed": 0, "in_progress": 0, "pending": 0, "skipped": 0}

        for step in self.steps.values():
            status_counts[step.status] += 1

        progress_percentage = (status_counts["completed"] / total_steps) * 100

        return {
            "total": total_steps,
            "completed": status_counts["completed"],
            "failed": status_counts["failed"],
            "in_progress": status_counts["in_progress"],
            "pending": status_counts["pending"],
            "skipped": status_counts["skipped"],
            "progress_percentage": round(progress_percentage, 1)
        }