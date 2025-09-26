"""Health check endpoints with Redis monitoring and Gemini model health"""
from fastapi import APIRouter, HTTPException
from src.lib.database import DatabaseManager
from src.lib.redis import RedisHealthCheck
from ..services.gemini_service import GeminiService
from ..services.model_health_service import ModelHealthService
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check including Redis and Gemini models"""
    db_healthy = DatabaseManager.health_check()
    redis_health = await RedisHealthCheck.async_check_connection()

    return {
        "status": "healthy" if db_healthy and redis_health["status"] == "healthy" else "degraded",
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": redis_health,
        "services": ["database", "redis", "celery", "gemini"]
    }

@router.get("/api/health/models")
async def get_model_health():
    """Get current health status of all Gemini models"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

        gemini_service = GeminiService(api_key=api_key)
        health_service = ModelHealthService(gemini_service)

        health_data = await health_service.get_all_models_health()
        return health_data

    except Exception as e:
        logger.error(f"Failed to get model health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")