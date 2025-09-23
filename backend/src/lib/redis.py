"""
Redis connection and management utilities for session storage and task queue.
"""
import json
import os
import logging
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager, contextmanager
import redis
import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))

# Global Redis instances
_redis_client: Optional[redis.Redis] = None
_async_redis_client: Optional[aioredis.Redis] = None

class RedisConfig:
    """Redis configuration constants"""

    # TTL settings (in seconds)
    SESSION_TTL = 86400  # 24 hours
    TASK_TTL = 604800    # 7 days
    PROGRESS_TTL = 3600  # 1 hour
    UI_STATE_TTL = 86400 # 24 hours (tied to session)

    # Key prefixes
    SESSION_PREFIX = "sessions:"
    TASK_PREFIX = "tasks:"
    PROGRESS_PREFIX = "events:"
    UI_STATE_PREFIX = "ui_state:"
    TASK_PROGRESS_PREFIX = "task_progress:"

    # Pub/Sub channels
    PROGRESS_CHANNEL = "progress_updates"
    SESSION_CHANNEL = "session_updates"

def get_redis_client() -> redis.Redis:
    """Get synchronous Redis client"""
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                max_connections=REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis synchronous client connected successfully")
        except RedisConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return _redis_client

def get_async_redis_client() -> aioredis.Redis:
    """Get asynchronous Redis client"""
    global _async_redis_client

    if _async_redis_client is None:
        try:
            _async_redis_client = aioredis.from_url(
                REDIS_URL,
                max_connections=REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            logger.info("Redis asynchronous client configured")
        except Exception as e:
            logger.error(f"Failed to configure async Redis client: {e}")
            raise

    return _async_redis_client

@contextmanager
def redis_connection():
    """Context manager for Redis connections with error handling"""
    client = None
    try:
        client = get_redis_client()
        yield client
    except RedisConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected Redis error: {e}")
        raise
    finally:
        # Connection is managed by the pool
        pass

@asynccontextmanager
async def async_redis_connection():
    """Async context manager for Redis connections"""
    client = None
    try:
        client = get_async_redis_client()
        await client.ping()  # Test connection
        yield client
    except RedisConnectionError as e:
        logger.error(f"Async Redis connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected async Redis error: {e}")
        raise
    finally:
        # Connection is managed by the pool
        pass

class RedisService:
    """Base Redis service with common operations"""

    def __init__(self, key_prefix: str):
        self.key_prefix = key_prefix
        self.client = get_redis_client()

    def _make_key(self, identifier: str) -> str:
        """Create Redis key with prefix"""
        return f"{self.key_prefix}{identifier}"

    def set_json(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store JSON data with optional TTL"""
        try:
            redis_key = self._make_key(key)
            json_data = json.dumps(data, default=str)

            if ttl:
                return self.client.setex(redis_key, ttl, json_data)
            else:
                return self.client.set(redis_key, json_data)
        except Exception as e:
            logger.error(f"Failed to set JSON data for key {key}: {e}")
            return False

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
        try:
            redis_key = self._make_key(key)
            data = self.client.get(redis_key)

            if data is None:
                return None

            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get JSON data for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            redis_key = self._make_key(key)
            return bool(self.client.delete(redis_key))
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            redis_key = self._make_key(key)
            return bool(self.client.exists(redis_key))
        except Exception as e:
            logger.error(f"Failed to check existence of key {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            redis_key = self._make_key(key)
            return bool(self.client.expire(redis_key, ttl))
        except Exception as e:
            logger.error(f"Failed to set TTL for key {key}: {e}")
            return False

    def get_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get keys matching pattern"""
        try:
            redis_pattern = self._make_key(pattern)
            keys = self.client.keys(redis_pattern)
            # Remove prefix from returned keys
            return [key.replace(self.key_prefix, "") for key in keys]
        except Exception as e:
            logger.error(f"Failed to get keys by pattern {pattern}: {e}")
            return []

class RedisHealthCheck:
    """Redis health check utilities"""

    @staticmethod
    def check_connection() -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            client = get_redis_client()

            # Basic connectivity
            client.ping()

            # Get Redis info
            info = client.info()

            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }
        except RedisConnectionError:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to Redis server"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Redis health check failed: {str(e)}"
            }

    @staticmethod
    async def async_check_connection() -> Dict[str, Any]:
        """Async Redis connection health check"""
        try:
            async with async_redis_connection() as client:
                # Basic connectivity
                await client.ping()

                # Get Redis info
                info = await client.info()

                return {
                    "status": "healthy",
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime_in_seconds": info.get("uptime_in_seconds"),
                }
        except RedisConnectionError:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to Redis server"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Async Redis health check failed: {str(e)}"
            }

# Graceful degradation helper
def with_redis_fallback(fallback_value=None):
    """Decorator for graceful Redis degradation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RedisConnectionError:
                logger.warning(f"Redis unavailable, using fallback for {func.__name__}")
                return fallback_value
            except Exception as e:
                logger.error(f"Redis operation failed in {func.__name__}: {e}")
                return fallback_value
        return wrapper
    return decorator

# Initialize clients on module import
try:
    get_redis_client()
    logger.info("Redis module initialized successfully")
except Exception as e:
    logger.warning(f"Redis initialization failed: {e}. Running in degraded mode.")