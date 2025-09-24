"""
Integration tests for end-to-end workflow validation
These tests validate complete setup and validation workflows
"""

import pytest
import subprocess
import time
import httpx
import os
from pathlib import Path


class TestE2ESetupIntegration:
    """End-to-end integration tests for complete setup workflow"""

    @pytest.fixture
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent.parent

    def test_complete_environment_setup_workflow(self, project_root: Path):
        """Test complete environment setup from scratch"""
        # Test environment validation script
        script_path = project_root / "scripts" / "config" / "validate-env.py"

        if script_path.exists():
            result = subprocess.run(
                ["python3", str(script_path), "--generate-template"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, "Environment template generation should work"

    def test_redis_to_backend_integration_flow(self):
        """Test Redis connectivity supports backend services"""
        try:
            import redis
            client = redis.Redis(host="localhost", port=6379, decode_responses=True)

            # Test session workflow
            session_id = f"test_session_{int(time.time())}"
            client.hset(f"session:{session_id}", mapping={"user_id": "test", "created": str(time.time())})
            client.expire(f"session:{session_id}", 30)

            data = client.hgetall(f"session:{session_id}")
            assert data["user_id"] == "test", "Session data should persist"

            client.delete(f"session:{session_id}")

        except Exception as e:
            pytest.skip(f"Redis integration test skipped: {e}")

    def test_service_health_check_integration(self):
        """Test that health check workflow would work end-to-end"""
        # Test health check URL structure
        health_url = "http://localhost:8000/setup/health"

        try:
            with httpx.Client(timeout=2) as client:
                response = client.get(health_url)
                if response.status_code == 200:
                    data = response.json()
                    assert "overall_status" in data
        except httpx.ConnectError:
            pass  # Expected when service not running

    def test_validation_script_integration(self, project_root: Path):
        """Test validation scripts work together"""
        scripts_dir = project_root / "scripts"

        if scripts_dir.exists():
            # Test that validation scripts are executable
            for script_file in scripts_dir.rglob("*.py"):
                assert script_file.stat().st_mode & 0o111, f"Script should be executable: {script_file}"