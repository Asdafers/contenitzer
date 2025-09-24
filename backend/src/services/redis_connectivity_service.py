"""
Redis connectivity service for testing and monitoring Redis connections
"""

import redis
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class RedisConnectivityService:
    """Service for testing Redis connectivity and operations"""

    def __init__(self):
        self.last_check: Optional[datetime] = None
        self.last_response_time: Optional[float] = None

    def test_connection(self, redis_url: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """
        Test Redis connection and basic operations
        Returns connection test results
        """
        start_time = time.time()

        try:
            # Create Redis client
            client = redis.from_url(redis_url, decode_responses=True, socket_timeout=timeout_seconds)

            # Test basic ping
            ping_response = client.ping()

            if not ping_response:
                raise redis.ConnectionError("Ping failed")

            # Test basic operations
            test_key = f"connectivity_test:{int(time.time())}"
            client.set(test_key, "test_value", ex=10)
            retrieved = client.get(test_key)
            client.delete(test_key)

            if retrieved != "test_value":
                raise Exception("Basic operations failed")

            response_time = (time.time() - start_time) * 1000
            self.last_check = datetime.utcnow()
            self.last_response_time = response_time

            # Get Redis info
            info = client.info()

            return {
                "connected": True,
                "response_time_ms": response_time,
                "error": None,
                "details": {
                    "redis_version": info.get("redis_version"),
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients")
                }
            }

        except redis.ConnectionError as e:
            return {
                "connected": False,
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": f"Connection failed: {str(e)}",
                "details": {"error_type": "ConnectionError"}
            }
        except Exception as e:
            return {
                "connected": False,
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": f"Test failed: {str(e)}",
                "details": {"error_type": type(e).__name__}
            }

    def test_multiple_databases(self, redis_url: str, databases: list[int]) -> Dict[str, Any]:
        """Test connectivity to multiple Redis databases"""
        results = {}

        for db_num in databases:
            try:
                db_url = redis_url.rstrip('/0123456789') + f"/{db_num}"
                result = self.test_connection(db_url)
                results[f"db_{db_num}"] = result
            except Exception as e:
                results[f"db_{db_num}"] = {
                    "connected": False,
                    "error": str(e),
                    "details": {"database": db_num}
                }

        return results