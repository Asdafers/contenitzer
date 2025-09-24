#!/usr/bin/env python3
"""
End-to-end workflow validation script
Tests complete setup and validation workflows
"""

import asyncio
import httpx
import redis
import json
from typing import Dict, Any


class E2EWorkflowValidator:
    """End-to-end workflow validation"""

    def __init__(self):
        self.base_url = "http://localhost:8000"

    async def run_complete_workflow(self) -> bool:
        """Run complete end-to-end workflow validation"""
        print("🚀 Starting end-to-end workflow validation...")

        try:
            # Step 1: Health check
            if not await self._test_health_endpoint():
                return False

            # Step 2: Configuration validation
            if not await self._test_config_validation():
                return False

            # Step 3: Connectivity testing
            if not await self._test_connectivity():
                return False

            print("✅ End-to-end workflow completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            return False

    async def _test_health_endpoint(self) -> bool:
        """Test health endpoint"""
        print("📊 Testing health endpoint...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/setup/health")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Health check passed - Status: {data.get('overall_status')}")
                    return True
                else:
                    print(f"❌ Health check failed - Status: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            return False

    async def _test_config_validation(self) -> bool:
        """Test configuration validation"""
        print("🔧 Testing configuration validation...")

        config = {
            "redis_url": "redis://localhost:6379/0",
            "redis_session_db": 1,
            "redis_task_db": 2,
            "youtube_api_key": "test_youtube_key_12345",
            "openai_api_key": "test_openai_key_12345",
            "environment": "local"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/setup/validate-config",
                    json=config
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Config validation passed - Valid: {data.get('valid')}")
                    return True
                else:
                    print(f"❌ Config validation failed - Status: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Config validation error: {e}")
            return False

    async def _test_connectivity(self) -> bool:
        """Test service connectivity"""
        print("🌐 Testing service connectivity...")

        request_data = {
            "services": ["redis"],
            "timeout_seconds": 5
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/setup/test-connectivity",
                    json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Connectivity test passed - Success: {data.get('overall_success')}")
                    return True
                else:
                    print(f"❌ Connectivity test failed - Status: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Connectivity test error: {e}")
            return False


async def main():
    validator = E2EWorkflowValidator()
    success = await validator.run_complete_workflow()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)