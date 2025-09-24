"""
Integration tests for Redis installation and setup validation
These tests validate complete Redis setup workflows
"""

import pytest
import subprocess
import time
import redis
import os
from pathlib import Path
from typing import Optional


class TestRedisSetupIntegration:
    """Integration tests for Redis installation and configuration"""

    @pytest.fixture(scope="class")
    def redis_connection_params(self) -> dict:
        """Redis connection parameters for testing"""
        return {
            "host": "localhost",
            "port": 6379,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5
        }

    def test_redis_server_installation_detection(self):
        """Test that Redis server is installed and available"""
        try:
            # Check if redis-server command exists
            result = subprocess.run(
                ["which", "redis-server"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Redis is installed via system package
                assert Path(result.stdout.strip()).exists(), "Redis server executable should exist"
            else:
                # Check for Docker redis or other installation methods
                docker_result = subprocess.run(
                    ["docker", "ps", "--filter", "name=redis", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Either system redis or docker redis should be available
                assert (result.returncode == 0) or ("redis" in docker_result.stdout), \
                    "Redis should be installed either via system package or Docker"

        except subprocess.TimeoutExpired:
            pytest.fail("Redis installation check timed out")
        except FileNotFoundError as e:
            pytest.fail(f"Command not found during Redis check: {e}")

    def test_redis_server_connectivity(self, redis_connection_params: dict):
        """Test basic Redis server connectivity"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Test basic ping
            response = client.ping()
            assert response is True, "Redis should respond to ping"

        except redis.ConnectionError:
            pytest.fail("Cannot connect to Redis server - ensure Redis is running on localhost:6379")
        except redis.TimeoutError:
            pytest.fail("Redis connection timed out")

    def test_redis_basic_operations(self, redis_connection_params: dict):
        """Test basic Redis operations work correctly"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Test string operations
            test_key = "test:setup:validation"
            test_value = "redis_setup_test_value"

            client.set(test_key, test_value, ex=30)  # 30 second expiry
            retrieved_value = client.get(test_key)

            assert retrieved_value == test_value, "Redis SET/GET operations should work"

            # Test hash operations
            hash_key = "test:setup:hash"
            hash_data = {
                "field1": "value1",
                "field2": "value2",
                "timestamp": str(int(time.time()))
            }

            client.hset(hash_key, mapping=hash_data)
            client.expire(hash_key, 30)

            retrieved_hash = client.hgetall(hash_key)
            assert retrieved_hash == hash_data, "Redis hash operations should work"

            # Clean up test data
            client.delete(test_key, hash_key)

        except redis.ConnectionError:
            pytest.fail("Redis connection lost during operations")
        except Exception as e:
            pytest.fail(f"Redis operations failed: {e}")

    def test_redis_multiple_databases(self, redis_connection_params: dict):
        """Test Redis multiple database support"""
        try:
            # Test session database (typically db=1)
            session_params = {**redis_connection_params, "db": 1}
            session_client = redis.Redis(**session_params)

            # Test task database (typically db=2)
            task_params = {**redis_connection_params, "db": 2}
            task_client = redis.Redis(**task_params)

            # Test both databases work independently
            session_key = "test:session:key"
            task_key = "test:task:key"

            session_client.set(session_key, "session_data", ex=30)
            task_client.set(task_key, "task_data", ex=30)

            # Verify data isolation
            assert session_client.get(session_key) == "session_data"
            assert task_client.get(task_key) == "task_data"

            # Verify databases are isolated
            assert session_client.get(task_key) is None
            assert task_client.get(session_key) is None

            # Clean up
            session_client.delete(session_key)
            task_client.delete(task_key)

        except redis.ConnectionError:
            pytest.fail("Redis multi-database setup failed")

    def test_redis_memory_info(self, redis_connection_params: dict):
        """Test Redis memory information is accessible"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Get memory info
            memory_info = client.info("memory")

            # Check essential memory metrics are available
            assert "used_memory" in memory_info, "Redis should report used memory"
            assert "used_memory_human" in memory_info, "Redis should report human readable memory"
            assert "maxmemory" in memory_info, "Redis should report max memory setting"

            # Memory usage should be reasonable for development
            used_memory_mb = memory_info["used_memory"] / (1024 * 1024)
            assert used_memory_mb < 500, f"Redis memory usage ({used_memory_mb:.2f}MB) should be reasonable for dev environment"

        except redis.ConnectionError:
            pytest.fail("Cannot get Redis memory information")

    def test_redis_persistence_configuration(self, redis_connection_params: dict):
        """Test Redis persistence settings"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Get server configuration
            config = client.config_get()

            # Check if persistence is configured
            save_config = config.get("save", "")
            appendonly = config.get("appendonly", "no")

            # For development, either RDB or AOF should be configured
            has_rdb = bool(save_config and save_config != "")
            has_aof = appendonly == "yes"

            # At least one persistence method should be enabled for data safety
            assert has_rdb or has_aof, "Redis should have some form of persistence configured"

        except redis.ConnectionError:
            pytest.fail("Cannot check Redis persistence configuration")

    def test_redis_performance_baseline(self, redis_connection_params: dict):
        """Test basic Redis performance meets development requirements"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Test write performance
            start_time = time.time()
            for i in range(100):
                client.set(f"perf:test:{i}", f"value_{i}")
            write_time = time.time() - start_time

            # Test read performance
            start_time = time.time()
            for i in range(100):
                client.get(f"perf:test:{i}")
            read_time = time.time() - start_time

            # Performance should be reasonable for development
            assert write_time < 1.0, f"Redis write performance too slow: {write_time:.3f}s for 100 operations"
            assert read_time < 1.0, f"Redis read performance too slow: {read_time:.3f}s for 100 operations"

            # Clean up performance test data
            keys_to_delete = [f"perf:test:{i}" for i in range(100)]
            client.delete(*keys_to_delete)

        except redis.ConnectionError:
            pytest.fail("Redis performance test connection failed")

    def test_redis_connection_recovery(self, redis_connection_params: dict):
        """Test Redis connection recovery and error handling"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Test normal operation
            client.set("test:recovery", "initial_value", ex=60)
            assert client.get("test:recovery") == "initial_value"

            # Test connection with invalid database number (should fail gracefully)
            invalid_params = {**redis_connection_params, "db": 99}
            invalid_client = redis.Redis(**invalid_params)

            with pytest.raises(redis.ResponseError):
                invalid_client.set("test:invalid", "value")

            # Original connection should still work
            assert client.get("test:recovery") == "initial_value"

            # Clean up
            client.delete("test:recovery")

        except redis.ConnectionError:
            pytest.fail("Redis connection recovery test failed")

    def test_redis_security_basic_checks(self, redis_connection_params: dict):
        """Test basic Redis security configuration"""
        try:
            client = redis.Redis(**redis_connection_params)

            # Get server info
            server_info = client.info("server")

            # Check Redis version (should be reasonably recent)
            redis_version = server_info.get("redis_version", "0.0.0")
            version_parts = redis_version.split(".")

            if len(version_parts) >= 2:
                major_version = int(version_parts[0])
                minor_version = int(version_parts[1])

                # Should be Redis 6.0+ for better security features
                assert major_version >= 6, f"Redis version {redis_version} should be 6.0+ for security"

            # Check if protected mode is reasonable for local development
            config = client.config_get("protected-mode")
            protected_mode = config.get("protected-mode", "yes")

            # For local development, protected mode behavior should be documented
            # (This is informational - actual security depends on network setup)
            assert protected_mode in ["yes", "no"], "Protected mode should have a valid setting"

        except redis.ConnectionError:
            pytest.fail("Cannot check Redis security configuration")
        except ValueError:
            # Version parsing failed - that's okay for this test
            pass

    def test_environment_redis_url_validation(self):
        """Test that Redis URL from environment is valid if set"""
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            # Parse Redis URL if provided in environment
            try:
                client = redis.from_url(redis_url, decode_responses=True, socket_timeout=5)

                # Test connection with environment URL
                response = client.ping()
                assert response is True, "Redis connection via REDIS_URL should work"

            except redis.ConnectionError:
                pytest.fail(f"Cannot connect using REDIS_URL: {redis_url}")
            except Exception as e:
                pytest.fail(f"Invalid REDIS_URL format: {e}")
        else:
            # REDIS_URL not set - this is okay for local development
            pytest.skip("REDIS_URL environment variable not set")

    @pytest.mark.skipif(
        subprocess.run(["which", "redis-cli"], capture_output=True).returncode != 0,
        reason="redis-cli not available"
    )
    def test_redis_cli_availability(self):
        """Test that Redis CLI tools are available"""
        try:
            # Test redis-cli ping
            result = subprocess.run(
                ["redis-cli", "ping"],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0, "redis-cli should be available and working"
            assert "PONG" in result.stdout, "redis-cli ping should return PONG"

        except subprocess.TimeoutExpired:
            pytest.fail("redis-cli command timed out")
        except FileNotFoundError:
            pytest.fail("redis-cli command not found")