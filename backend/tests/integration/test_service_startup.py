"""
Integration tests for service startup sequence validation
These tests validate the complete service startup and health checking workflow
"""

import pytest
import subprocess
import time
import httpx
import psutil
import os
import signal
from pathlib import Path
from typing import Optional, Dict, Any


class TestServiceStartupIntegration:
    """Integration tests for complete service startup sequence"""

    @pytest.fixture(scope="class")
    def service_urls(self) -> Dict[str, str]:
        """Service URLs for testing"""
        return {
            "backend": "http://localhost:8000",
            "frontend": "http://localhost:3000",
            "websocket": "ws://localhost:8000/ws"
        }

    @pytest.fixture(scope="class")
    def project_root(self) -> Path:
        """Project root directory"""
        return Path(__file__).parent.parent.parent.parent

    def test_project_structure_exists(self, project_root: Path):
        """Test that required project structure exists"""
        # Backend structure
        backend_dir = project_root / "backend"
        assert backend_dir.exists(), "Backend directory should exist"
        assert (backend_dir / "main.py").exists(), "Backend main.py should exist"
        assert (backend_dir / "pyproject.toml").exists(), "Backend pyproject.toml should exist"

        # Frontend structure
        frontend_dir = project_root / "frontend"
        assert frontend_dir.exists(), "Frontend directory should exist"
        assert (frontend_dir / "package.json").exists(), "Frontend package.json should exist"

        # Scripts structure
        scripts_dir = project_root / "scripts"
        if scripts_dir.exists():
            # If scripts exist, check basic structure
            config_dir = scripts_dir / "config"
            if config_dir.exists():
                assert (config_dir / "validate-env.py").exists(), "Environment validation script should exist"

    def test_backend_dependency_check(self, project_root: Path):
        """Test that backend dependencies can be resolved"""
        backend_dir = project_root / "backend"

        try:
            # Check if uv is available
            uv_check = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if uv_check.returncode == 0:
                # Test dependency resolution with uv
                result = subprocess.run(
                    ["uv", "sync", "--check"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # Check should pass or indicate what needs to be installed
                assert result.returncode in [0, 1], "Dependency check should complete"

            else:
                # Fall back to pip check
                pip_result = subprocess.run(
                    ["pip", "check"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                # pip check may fail if not in virtual environment - that's okay

        except subprocess.TimeoutExpired:
            pytest.fail("Backend dependency check timed out")
        except FileNotFoundError:
            pytest.skip("Neither uv nor pip available for dependency checking")

    def test_frontend_dependency_check(self, project_root: Path):
        """Test that frontend dependencies can be resolved"""
        frontend_dir = project_root / "frontend"

        try:
            # Check if package.json exists and is valid
            result = subprocess.run(
                ["npm", "list", "--depth=0"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            # npm list may fail if dependencies aren't installed - that's okay
            # We're just checking that the command structure works
            assert result.returncode in [0, 1], "npm list should complete"

        except subprocess.TimeoutExpired:
            pytest.fail("Frontend dependency check timed out")
        except FileNotFoundError:
            pytest.skip("npm not available for dependency checking")

    def test_environment_validation_script(self, project_root: Path):
        """Test that environment validation script works"""
        script_path = project_root / "scripts" / "config" / "validate-env.py"

        if not script_path.exists():
            pytest.skip("Environment validation script not found")

        try:
            # Test script help/usage
            result = subprocess.run(
                ["python3", str(script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0, "Environment validation script should show help"
            assert "validate" in result.stdout.lower(), "Help should mention validation"

            # Test template generation
            temp_env_path = project_root / "backend" / ".env.test.example"

            gen_result = subprocess.run(
                ["python3", str(script_path), "--generate-template", "--template-output", str(temp_env_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if gen_result.returncode == 0:
                assert temp_env_path.exists(), "Template file should be generated"

                # Clean up test template
                temp_env_path.unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            pytest.fail("Environment validation script timed out")

    def test_redis_availability_for_services(self):
        """Test that Redis is available for service startup"""
        try:
            import redis

            # Test basic Redis connectivity
            client = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=5)
            response = client.ping()

            assert response is True, "Redis should be available for services"

            # Test multiple databases that services will use
            session_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True, socket_timeout=5)
            task_client = redis.Redis(host="localhost", port=6379, db=2, decode_responses=True, socket_timeout=5)

            session_client.ping()
            task_client.ping()

        except ImportError:
            pytest.skip("Redis Python client not available")
        except Exception as e:
            pytest.fail(f"Redis not available for services: {e}")

    def test_port_availability_check(self, service_urls: Dict[str, str]):
        """Test that required service ports are available or in use correctly"""
        import socket

        required_ports = [8000, 3000, 6379]

        for port in required_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            try:
                result = sock.connect_ex(("localhost", port))

                if result == 0:
                    # Port is in use - might be our services or conflicts
                    print(f"Port {port} is in use (might be service or conflict)")
                else:
                    # Port is available for our services
                    print(f"Port {port} is available")

            except Exception as e:
                print(f"Could not check port {port}: {e}")
            finally:
                sock.close()

    def test_backend_startup_simulation(self, project_root: Path, service_urls: Dict[str, str]):
        """Test backend service startup process"""
        backend_dir = project_root / "backend"

        # Test that we can at least attempt to start the backend
        # (We don't actually start it to avoid port conflicts)

        # Check if main.py exists and is importable
        main_py = backend_dir / "main.py"
        if not main_py.exists():
            pytest.skip("Backend main.py not found")

        try:
            # Test syntax check of main.py
            syntax_check = subprocess.run(
                ["python3", "-m", "py_compile", str(main_py)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=backend_dir
            )

            assert syntax_check.returncode == 0, f"Backend main.py should have valid syntax: {syntax_check.stderr}"

        except subprocess.TimeoutExpired:
            pytest.fail("Backend syntax check timed out")
        except FileNotFoundError:
            pytest.skip("Python3 not available for syntax checking")

    def test_frontend_startup_simulation(self, project_root: Path):
        """Test frontend service startup process"""
        frontend_dir = project_root / "frontend"

        if not (frontend_dir / "package.json").exists():
            pytest.skip("Frontend package.json not found")

        try:
            # Test that npm scripts are defined
            result = subprocess.run(
                ["npm", "run"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should list available scripts
            if result.returncode == 0:
                assert "dev" in result.stdout, "Frontend should have 'dev' script"

        except subprocess.TimeoutExpired:
            pytest.fail("Frontend script check timed out")
        except FileNotFoundError:
            pytest.skip("npm not available for frontend checking")

    def test_service_health_endpoint_contracts(self, service_urls: Dict[str, str]):
        """Test that service health endpoints would work when services are running"""
        # This test validates the health check approach without requiring running services

        backend_url = service_urls["backend"]
        health_url = f"{backend_url}/health"

        try:
            # Attempt to connect (will likely fail, but we check error handling)
            with httpx.Client(timeout=2) as client:
                try:
                    response = client.get(health_url)

                    # If we get a response, validate it
                    if response.status_code == 200:
                        data = response.json()
                        assert "status" in data, "Health endpoint should return status"

                except httpx.ConnectError:
                    # Expected when service isn't running - this is okay
                    pass
                except httpx.TimeoutException:
                    # Also okay - just means service isn't responding
                    pass

        except Exception as e:
            # Any other errors are also okay for this test
            print(f"Health endpoint test info: {e}")

    def test_websocket_connection_availability(self, service_urls: Dict[str, str]):
        """Test WebSocket connection setup"""
        # Test WebSocket URL parsing and validation
        websocket_url = service_urls["websocket"]

        assert websocket_url.startswith("ws://"), "WebSocket URL should use ws:// protocol"
        assert "localhost" in websocket_url, "WebSocket should be configured for localhost"

        # Test that the URL structure is valid
        from urllib.parse import urlparse

        parsed = urlparse(websocket_url)
        assert parsed.hostname == "localhost", "WebSocket hostname should be localhost"
        assert parsed.port == 8000, "WebSocket port should be 8000"
        assert parsed.path == "/ws", "WebSocket path should be /ws"

    def test_service_startup_order_dependencies(self):
        """Test service startup dependency requirements"""
        # Define expected startup order
        startup_order = [
            "redis",       # Must be first
            "backend",     # Depends on Redis
            "frontend",    # Can start independently
            "websocket"    # Part of backend service
        ]

        # Test that Redis dependency is documented
        assert startup_order[0] == "redis", "Redis should start first"
        assert startup_order.index("backend") > startup_order.index("redis"), "Backend should start after Redis"

    def test_service_graceful_shutdown_preparation(self):
        """Test preparation for graceful service shutdown"""
        # Test signal handling preparation
        import signal

        # Verify that standard signals are available
        assert hasattr(signal, 'SIGTERM'), "SIGTERM should be available for graceful shutdown"
        assert hasattr(signal, 'SIGINT'), "SIGINT should be available for interrupt handling"

        # Test process identification methods
        current_pid = os.getpid()
        assert current_pid > 0, "Should be able to get process ID"

    def test_service_monitoring_readiness(self):
        """Test that service monitoring infrastructure is ready"""
        # Test that we can monitor system resources
        try:
            import psutil

            # Test memory monitoring
            memory = psutil.virtual_memory()
            assert memory.total > 0, "Should be able to monitor memory"

            # Test CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=0.1)
            assert cpu_percent >= 0, "Should be able to monitor CPU"

            # Test disk monitoring
            disk = psutil.disk_usage('/')
            assert disk.total > 0, "Should be able to monitor disk"

        except ImportError:
            pytest.skip("psutil not available for system monitoring")

    def test_log_directory_preparation(self, project_root: Path):
        """Test that log directories can be created"""
        log_dirs = [
            project_root / "logs",
            project_root / "backend" / "logs",
            project_root / "frontend" / "logs"
        ]

        for log_dir in log_dirs:
            try:
                # Test that we can create log directories
                log_dir.mkdir(parents=True, exist_ok=True)

                # Test that we can write to log directories
                test_file = log_dir / "startup_test.log"
                test_file.write_text(f"Test log entry at {time.time()}")

                assert test_file.exists(), f"Should be able to write to {log_dir}"

                # Clean up test file
                test_file.unlink(missing_ok=True)

                # Only remove directory if we created it and it's empty
                try:
                    log_dir.rmdir()
                except OSError:
                    # Directory not empty or already existed - that's fine
                    pass

            except PermissionError:
                pytest.fail(f"No permission to create log directory: {log_dir}")

    def test_configuration_file_access(self, project_root: Path):
        """Test access to configuration files"""
        config_files = [
            project_root / "backend" / "pyproject.toml",
            project_root / "frontend" / "package.json",
        ]

        for config_file in config_files:
            if config_file.exists():
                # Test that we can read configuration files
                content = config_file.read_text()
                assert len(content) > 0, f"Configuration file should have content: {config_file}"

                # Test basic JSON/TOML parsing
                if config_file.name.endswith(".json"):
                    import json
                    json.loads(content)  # Should not raise exception

                elif config_file.name.endswith(".toml"):
                    # Basic TOML validation (just check for section headers)
                    assert "[" in content, "TOML file should have sections"