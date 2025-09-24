#!/usr/bin/env python3
"""
Service startup validation script
Checks if all required services are running and accessible
"""

import asyncio
import httpx
import redis
import socket
from typing import Dict, Any


class ServiceValidator:
    """Validates all required services are running"""

    async def check_all_services(self) -> Dict[str, Any]:
        """Check all required services"""
        results = {}

        # Check Redis
        results["redis"] = self._check_redis()

        # Check Backend API
        results["backend"] = await self._check_backend()

        # Check Frontend
        results["frontend"] = await self._check_frontend()

        # Overall status
        all_healthy = all(service["status"] == "healthy" for service in results.values())
        overall_status = "healthy" if all_healthy else "unhealthy"

        return {
            "overall_status": overall_status,
            "services": results
        }

    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis service"""
        try:
            client = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=2)
            response = client.ping()

            if response:
                info = client.info()
                return {
                    "status": "healthy",
                    "version": info.get("redis_version"),
                    "memory": info.get("used_memory_human")
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_backend(self) -> Dict[str, Any]:
        """Check Backend API service"""
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    return {"status": "healthy", "response_code": 200}
                else:
                    return {"status": "unhealthy", "response_code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_frontend(self) -> Dict[str, Any]:
        """Check Frontend service"""
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get("http://localhost:3000")
                if response.status_code == 200:
                    return {"status": "healthy", "response_code": 200}
                else:
                    return {"status": "unhealthy", "response_code": response.status_code}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def print_results(self, results: Dict[str, Any]) -> None:
        """Print service check results"""
        print("🔍 Service Health Check Results")
        print("=" * 40)

        overall = results["overall_status"]
        if overall == "healthy":
            print("✅ All services are healthy")
        else:
            print("❌ Some services are unhealthy")

        for service_name, service_data in results["services"].items():
            status = service_data["status"]
            icon = "✅" if status == "healthy" else "❌"

            print(f"{icon} {service_name.title()}: {status}")

            if status == "unhealthy" and "error" in service_data:
                print(f"   Error: {service_data['error']}")


async def main():
    validator = ServiceValidator()
    results = await validator.check_all_services()
    validator.print_results(results)

    # Return appropriate exit code
    exit_code = 0 if results["overall_status"] == "healthy" else 1
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)