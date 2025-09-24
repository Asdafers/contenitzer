"""
ServiceStatus model for tracking health and connectivity of services
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class ServiceStatus(BaseModel):
    """Health and connectivity status of individual services"""

    service_name: str = Field(..., description="Service identifier")
    status: Literal["healthy", "unhealthy", "starting", "stopped"] = Field(..., description="Service health state")
    last_check: datetime = Field(..., description="Timestamp of last health check")
    response_time_ms: Optional[float] = Field(None, ge=0, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error description if unhealthy")
    connection_details: Optional[Dict[str, Any]] = Field(None, description="Service-specific metadata")
    dependencies: Optional[list[str]] = Field(default_factory=list, description="Required services")

    class Config:
        schema_extra = {
            "example": {
                "service_name": "redis",
                "status": "healthy",
                "last_check": "2025-09-23T16:30:00Z",
                "response_time_ms": 2.5,
                "error_message": None,
                "connection_details": {
                    "version": "7.0.0",
                    "memory_usage_mb": 45.2
                },
                "dependencies": []
            }
        }