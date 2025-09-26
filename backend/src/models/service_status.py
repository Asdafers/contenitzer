"""
ServiceStatus model for tracking health and connectivity of services
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class ModelHealthStatus(BaseModel):
    """Health status for individual AI models"""

    available: bool = Field(..., description="Model availability status")
    last_success: Optional[datetime] = Field(None, description="Last successful model interaction")
    error_count: int = Field(0, ge=0, description="Number of consecutive errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    response_time_ms: Optional[float] = Field(None, ge=0, description="Average response time")
    requests_count: int = Field(0, ge=0, description="Total requests to this model")


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


class ServiceHealth(BaseModel):
    """Enhanced service health model with AI model tracking capabilities"""

    # Basic service information
    service_name: str = Field(..., description="Service identifier")
    status: Literal["healthy", "unhealthy", "starting", "stopped"] = Field(..., description="Service health state")
    last_check: datetime = Field(..., description="Timestamp of last health check")
    response_time_ms: Optional[float] = Field(None, ge=0, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error description if unhealthy")
    connection_details: Optional[Dict[str, Any]] = Field(None, description="Service-specific metadata")
    dependencies: Optional[list[str]] = Field(default_factory=list, description="Required services")

    # Model tracking fields
    gemini_model_status: Dict[str, ModelHealthStatus] = Field(
        default_factory=dict,
        description="Status tracking for each Gemini model"
    )
    last_model_check: Optional[datetime] = Field(None, description="Timestamp of last model availability check")
    model_performance_metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Performance metrics per model (response times, success rates, etc.)"
    )

    def update_model_status(self, model_name: str, available: bool, response_time_ms: Optional[float] = None, error_message: Optional[str] = None) -> None:
        """Update the status of a specific model"""
        now = datetime.utcnow()

        if model_name not in self.gemini_model_status:
            self.gemini_model_status[model_name] = ModelHealthStatus(
                available=available,
                last_success=now if available else None,
                error_count=0 if available else 1,
                last_error=error_message,
                response_time_ms=response_time_ms,
                requests_count=1
            )
        else:
            model_status = self.gemini_model_status[model_name]
            model_status.available = available
            model_status.requests_count += 1

            if available:
                model_status.last_success = now
                model_status.error_count = 0
                model_status.last_error = None
                if response_time_ms is not None:
                    # Calculate rolling average for response time
                    if model_status.response_time_ms is None:
                        model_status.response_time_ms = response_time_ms
                    else:
                        model_status.response_time_ms = (model_status.response_time_ms * 0.8) + (response_time_ms * 0.2)
            else:
                model_status.error_count += 1
                model_status.last_error = error_message

        self.last_model_check = now

    def update_model_performance_metrics(self, model_name: str, metrics: Dict[str, float]) -> None:
        """Update performance metrics for a specific model"""
        if model_name not in self.model_performance_metrics:
            self.model_performance_metrics[model_name] = {}

        self.model_performance_metrics[model_name].update(metrics)

    def get_overall_model_health(self) -> Literal["healthy", "degraded", "unhealthy"]:
        """Get overall health status of all models"""
        if not self.gemini_model_status:
            return "unhealthy"

        available_models = sum(1 for status in self.gemini_model_status.values() if status.available)
        total_models = len(self.gemini_model_status)

        if available_models == total_models:
            return "healthy"
        elif available_models > 0:
            return "degraded"
        else:
            return "unhealthy"

    def get_model_summary(self) -> Dict[str, Any]:
        """Get a summary of all model statuses for API responses"""
        return {
            "overall_status": self.get_overall_model_health(),
            "total_models": len(self.gemini_model_status),
            "available_models": sum(1 for status in self.gemini_model_status.values() if status.available),
            "last_check": self.last_model_check,
            "models": {
                name: {
                    "available": status.available,
                    "last_success": status.last_success,
                    "error_count": status.error_count,
                    "response_time_ms": status.response_time_ms,
                    "requests_count": status.requests_count
                }
                for name, status in self.gemini_model_status.items()
            },
            "performance_metrics": self.model_performance_metrics
        }

    class Config:
        schema_extra = {
            "example": {
                "service_name": "gemini-ai",
                "status": "healthy",
                "last_check": "2025-09-26T10:30:00Z",
                "response_time_ms": 150.5,
                "error_message": None,
                "connection_details": {
                    "api_version": "v1",
                    "region": "us-central1"
                },
                "dependencies": ["internet", "google-auth"],
                "gemini_model_status": {
                    "gemini-1.5-pro": {
                        "available": True,
                        "last_success": "2025-09-26T10:29:45Z",
                        "error_count": 0,
                        "last_error": None,
                        "response_time_ms": 145.2,
                        "requests_count": 25
                    },
                    "gemini-1.5-flash": {
                        "available": True,
                        "last_success": "2025-09-26T10:29:50Z",
                        "error_count": 0,
                        "last_error": None,
                        "response_time_ms": 89.3,
                        "requests_count": 42
                    }
                },
                "last_model_check": "2025-09-26T10:30:00Z",
                "model_performance_metrics": {
                    "gemini-1.5-pro": {
                        "avg_tokens_per_second": 12.5,
                        "success_rate": 0.98,
                        "p95_response_time_ms": 250.0
                    },
                    "gemini-1.5-flash": {
                        "avg_tokens_per_second": 18.2,
                        "success_rate": 0.99,
                        "p95_response_time_ms": 150.0
                    }
                }
            }
        }