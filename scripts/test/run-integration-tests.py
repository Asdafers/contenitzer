#!/usr/bin/env python3
"""
Integration test runner for complete workflow validation
"""

import subprocess
import sys
import time
from pathlib import Path


class IntegrationTestRunner:
    """Runs integration tests with environment validation"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.backend_dir = self.project_root / "backend"
        self.test_dir = self.backend_dir / "tests" / "integration"

    def check_environment(self) -> bool:
        """Check if integration test environment is ready"""
        print("🔍 Checking integration test environment...")

        # Check Redis connectivity
        try:
            import redis
            client = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=2)
            client.ping()
            print("✅ Redis connection verified")
        except Exception as e:
            print(f"❌ Redis not available: {e}")
            print("💡 Start Redis with: redis-server or docker run -p 6379:6379 redis")
            return False

        return True

    def run_tests(self) -> bool:
        """Run integration tests"""
        if not self.check_environment():
            return False

        print("\n🧪 Running integration tests...")

        cmd = [
            "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "--durations=10"
        ]

        try:
            result = subprocess.run(cmd, cwd=self.backend_dir)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False


def main():
    runner = IntegrationTestRunner()
    success = runner.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()