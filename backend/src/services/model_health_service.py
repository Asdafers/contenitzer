from typing import Dict, Any, List, Optional
import logging
import asyncio
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from .gemini_service import GeminiService

logger = logging.getLogger(__name__)


@dataclass
class ModelHealthMetrics:
    """Model health metrics data structure"""
    model_name: str
    available: bool
    last_success: Optional[datetime]
    error_count: int
    avg_response_time_ms: int
    rate_limit_remaining: Optional[int]
    last_checked: datetime


class ModelHealthService:
    """
    Service for monitoring and tracking Gemini model health and availability

    Provides periodic health checks, metrics aggregation, and health status reporting
    for all configured Gemini models.
    """

    def __init__(self, gemini_service: GeminiService, check_interval_seconds: int = 60):
        self.gemini_service = gemini_service
        self.check_interval = check_interval_seconds
        self.metrics_history: Dict[str, List[ModelHealthMetrics]] = {}
        self.current_metrics: Dict[str, ModelHealthMetrics] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False

    async def get_model_health(self, model_name: str) -> Dict[str, Any]:
        """Get current health status for a specific model"""
        try:
            status = await self.gemini_service.check_model_availability(model_name)

            return {
                "available": status.get('available', False),
                "last_success": status.get('last_checked') if status.get('available') else None,
                "error_count": 1 if not status.get('available') else 0,
                "avg_response_time_ms": status.get('response_time_ms', 0),
                "rate_limit_remaining": None,  # Would need API quota info
                "last_checked": status.get('last_checked', datetime.now())
            }
        except Exception as e:
            logger.error(f"Failed to get health for model {model_name}: {e}")
            return {
                "available": False,
                "error_count": 1,
                "avg_response_time_ms": 0,
                "last_checked": datetime.now()
            }

    async def get_all_models_health(self) -> Dict[str, Any]:
        """Get comprehensive health status for all configured models"""
        try:
            # Get health for both text and image models
            text_model_name = self.gemini_service.get_text_model()
            image_model_name = self.gemini_service.get_image_model()

            text_health = await self.get_model_health(text_model_name)
            image_health = await self.get_model_health(image_model_name)

            # Calculate overall status
            text_available = text_health.get('available', False)
            image_available = image_health.get('available', False)

            if text_available and image_available:
                overall_status = 'healthy'
                primary_model_available = True
            elif text_available or image_available:
                overall_status = 'degraded'
                primary_model_available = image_available  # Image model is primary for generation
            else:
                overall_status = 'unhealthy'
                primary_model_available = False

            return {
                "timestamp": datetime.now(),
                "models": {
                    text_model_name: text_health,
                    image_model_name: image_health
                },
                "overall_status": overall_status,
                "primary_model_available": primary_model_available
            }

        except Exception as e:
            logger.error(f"Failed to get all models health: {e}")
            return {
                "timestamp": datetime.now(),
                "models": {},
                "overall_status": "unhealthy",
                "primary_model_available": False,
                "error": str(e)
            }

    async def start_monitoring(self) -> None:
        """Start periodic health monitoring"""
        if self._is_monitoring:
            logger.warning("Health monitoring already running")
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started health monitoring with {self.check_interval}s interval")

    async def stop_monitoring(self) -> None:
        """Stop periodic health monitoring"""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped health monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._is_monitoring:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def _perform_health_check(self) -> None:
        """Perform a single health check cycle"""
        try:
            health_data = await self.get_all_models_health()

            # Update current metrics
            for model_name, health in health_data.get('models', {}).items():
                metrics = ModelHealthMetrics(
                    model_name=model_name,
                    available=health.get('available', False),
                    last_success=health.get('last_success'),
                    error_count=health.get('error_count', 0),
                    avg_response_time_ms=health.get('avg_response_time_ms', 0),
                    rate_limit_remaining=health.get('rate_limit_remaining'),
                    last_checked=health.get('last_checked', datetime.now())
                )

                self.current_metrics[model_name] = metrics

                # Store in history (keep last 100 entries per model)
                if model_name not in self.metrics_history:
                    self.metrics_history[model_name] = []

                self.metrics_history[model_name].append(metrics)
                if len(self.metrics_history[model_name]) > 100:
                    self.metrics_history[model_name] = self.metrics_history[model_name][-100:]

            logger.debug(f"Health check completed. Overall status: {health_data.get('overall_status')}")

        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")