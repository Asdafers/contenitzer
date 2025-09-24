"""
TestExecution model for recording test results and validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class TestExecution(BaseModel):
    """Records results of validation tests and setup verification"""

    test_type: Literal["contract", "integration", "smoke", "e2e"] = Field(..., description="Test category")
    test_name: str = Field(..., description="Specific test identifier")
    execution_time: datetime = Field(..., description="When test was run")
    duration_ms: float = Field(..., ge=0, description="Test execution time")
    status: Literal["passed", "failed", "skipped", "error"] = Field(..., description="Test result")
    error_details: Optional[str] = Field(None, description="Failure information")
    test_data: Optional[Dict[str, Any]] = Field(None, description="Input parameters used")
    environment_snapshot: Optional[Dict[str, Any]] = Field(None, description="Configuration at test time")

    class Config:
        schema_extra = {
            "example": {
                "test_type": "contract",
                "test_name": "test_setup_health_endpoint",
                "execution_time": "2025-09-23T16:30:00Z",
                "duration_ms": 150.5,
                "status": "passed",
                "error_details": None,
                "test_data": {"endpoint": "/setup/health"},
                "environment_snapshot": {"redis_available": True}
            }
        }