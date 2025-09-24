"""
SetupProgress model for tracking completion state of setup steps
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class SetupProgress(BaseModel):
    """Tracks completion state of setup steps"""

    step_id: str = Field(..., description="Unique identifier for setup step")
    step_name: str = Field(..., description="Human-readable description")
    category: Literal["prerequisites", "installation", "configuration", "validation"] = Field(..., description="Setup phase")
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"] = Field(..., description="Completion state")
    started_at: Optional[datetime] = Field(None, description="When step execution began")
    completed_at: Optional[datetime] = Field(None, description="When step finished")
    error_details: Optional[str] = Field(None, description="Failure information")
    prerequisites: List[str] = Field(default_factory=list, description="Required previous steps")
    artifacts: Optional[Dict[str, Any]] = Field(None, description="Files or outputs created")

    @validator("completed_at")
    def validate_completion_time(cls, v, values):
        """Ensure completed timestamp is after started timestamp"""
        if v and values.get("started_at") and v < values["started_at"]:
            raise ValueError("Completion time cannot be before start time")
        return v

    @validator("status")
    def validate_status_consistency(cls, v, values):
        """Validate status transitions make sense"""
        completed_at = values.get("completed_at")
        started_at = values.get("started_at")

        if v == "completed" and not completed_at:
            raise ValueError("Completed status requires completion timestamp")
        if v in ["pending", "skipped"] and started_at:
            raise ValueError("Pending/skipped steps should not have start time")

        return v

    class Config:
        schema_extra = {
            "example": {
                "step_id": "redis_installation",
                "step_name": "Install Redis server",
                "category": "installation",
                "status": "completed",
                "started_at": "2025-09-23T16:25:00Z",
                "completed_at": "2025-09-23T16:27:30Z",
                "error_details": None,
                "prerequisites": ["check_system_requirements"],
                "artifacts": {"redis_version": "7.0.0", "config_file": "/etc/redis/redis.conf"}
            }
        }