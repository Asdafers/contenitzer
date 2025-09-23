"""Health check endpoints with Redis monitoring"""
from fastapi import APIRouter
from src.lib.database import DatabaseManager
from src.lib.redis import RedisHealthCheck

router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check including Redis"""
    db_healthy = DatabaseManager.health_check()
    redis_health = await RedisHealthCheck.async_check_connection()

    return {
        "status": "healthy" if db_healthy and redis_health["status"] == "healthy" else "degraded",
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": redis_health,
        "services": ["database", "redis", "celery"]
    }