"""
System dependency validation and health checks.
Validates required system components for video generation.
"""
import logging
import sys
import shutil
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

logger = logging.getLogger(__name__)


class SystemCheckError(Exception):
    """Exception raised when system checks fail."""
    pass


class DependencyCheck:
    """Individual dependency check result."""

    def __init__(self, name: str, required: bool = True):
        self.name = name
        self.required = required
        self.available = False
        self.version = None
        self.path = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert check result to dictionary."""
        return {
            "name": self.name,
            "required": self.required,
            "available": self.available,
            "version": self.version,
            "path": self.path,
            "error": self.error,
            "status": "PASS" if self.available or not self.required else "FAIL"
        }


class SystemValidator:
    """System dependency validator for video generation."""

    def __init__(self):
        self.checks: List[DependencyCheck] = []
        self.media_dir = Path("media")

    def check_python_version(self) -> DependencyCheck:
        """Check Python version compatibility."""
        check = DependencyCheck("Python 3.11+", required=True)

        try:
            version_info = sys.version_info
            check.version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
            check.available = version_info >= (3, 11)

            if not check.available:
                check.error = f"Python 3.11+ required, found {check.version}"

        except Exception as e:
            check.error = f"Failed to check Python version: {e}"

        return check

    def check_ffmpeg_python(self) -> DependencyCheck:
        """Check ffmpeg-python package availability."""
        check = DependencyCheck("ffmpeg-python", required=True)

        try:
            import ffmpeg
            check.available = True
            check.version = getattr(ffmpeg, '__version__', 'unknown')
            check.path = ffmpeg.__file__

        except ImportError as e:
            check.error = f"ffmpeg-python package not installed: {e}"
        except Exception as e:
            check.error = f"Error checking ffmpeg-python: {e}"

        return check

    def check_ffmpeg_binary(self) -> DependencyCheck:
        """Check FFmpeg binary availability."""
        check = DependencyCheck("FFmpeg binary", required=False)

        try:
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                check.available = True
                check.path = ffmpeg_path

                # Get version
                result = subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    check.version = version_line.split()[2] if len(version_line.split()) > 2 else "unknown"
                else:
                    check.error = "FFmpeg found but version check failed"
            else:
                check.error = "FFmpeg binary not found in PATH"

        except Exception as e:
            check.error = f"Error checking FFmpeg binary: {e}"

        return check

    def check_redis_connectivity(self) -> DependencyCheck:
        """Check Redis connectivity for task queue."""
        check = DependencyCheck("Redis connectivity", required=True)

        try:
            import redis
            client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            response = client.ping()
            check.available = response is True
            check.version = client.info().get('redis_version', 'unknown')

            if not check.available:
                check.error = "Redis ping failed"

        except ImportError:
            check.error = "Redis package not installed"
        except Exception as e:
            check.error = f"Redis connection failed: {e}"

        return check

    def check_media_directories(self) -> DependencyCheck:
        """Check media directory structure."""
        check = DependencyCheck("Media directories", required=True)

        required_dirs = [
            "media/videos",
            "media/assets/images",
            "media/assets/audio",
            "media/assets/temp",
            "media/stock"
        ]

        try:
            missing_dirs = []
            for dir_path in required_dirs:
                full_path = Path(dir_path)
                if not full_path.exists():
                    missing_dirs.append(dir_path)

            check.available = len(missing_dirs) == 0

            if missing_dirs:
                check.error = f"Missing directories: {', '.join(missing_dirs)}"
            else:
                check.path = str(self.media_dir.absolute())

        except Exception as e:
            check.error = f"Error checking media directories: {e}"

        return check

    def check_disk_space(self, min_gb: float = 1.0) -> DependencyCheck:
        """Check available disk space for video generation."""
        check = DependencyCheck(f"Disk space ({min_gb}GB free)", required=True)

        try:
            stat = shutil.disk_usage(Path.cwd())
            free_gb = stat.free / (1024 ** 3)
            check.available = free_gb >= min_gb
            check.version = f"{free_gb:.2f}GB free"

            if not check.available:
                check.error = f"Insufficient disk space: {free_gb:.2f}GB free, {min_gb}GB required"

        except Exception as e:
            check.error = f"Error checking disk space: {e}"

        return check

    def check_celery_worker(self) -> DependencyCheck:
        """Check if Celery worker is running."""
        check = DependencyCheck("Celery worker", required=False)

        try:
            from celery import Celery
            from backend.src.lib.database import get_redis_url

            # Create Celery app instance
            app = Celery('test')
            app.config_from_object('backend.celery_config')

            # Try to get worker stats
            inspect = app.control.inspect()
            stats = inspect.stats()

            if stats:
                check.available = True
                check.version = f"{len(stats)} worker(s) active"
            else:
                check.error = "No active Celery workers found"

        except ImportError as e:
            check.error = f"Celery not available: {e}"
        except Exception as e:
            check.error = f"Error checking Celery worker: {e}"

        return check

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all system checks and return results."""
        self.checks = [
            self.check_python_version(),
            self.check_ffmpeg_python(),
            self.check_ffmpeg_binary(),
            self.check_redis_connectivity(),
            self.check_media_directories(),
            self.check_disk_space(),
            self.check_celery_worker()
        ]

        # Calculate overall status
        required_checks = [c for c in self.checks if c.required]
        required_passed = [c for c in required_checks if c.available]
        optional_checks = [c for c in self.checks if not c.required]
        optional_passed = [c for c in optional_checks if c.available]

        overall_status = "PASS" if len(required_passed) == len(required_checks) else "FAIL"

        return {
            "overall_status": overall_status,
            "summary": {
                "required_checks": len(required_checks),
                "required_passed": len(required_passed),
                "optional_checks": len(optional_checks),
                "optional_passed": len(optional_passed)
            },
            "checks": [check.to_dict() for check in self.checks],
            "ready_for_video_generation": overall_status == "PASS"
        }

    def get_failed_checks(self) -> List[DependencyCheck]:
        """Get list of failed checks."""
        return [check for check in self.checks if check.required and not check.available]

    def get_recommendations(self) -> List[str]:
        """Get recommendations for fixing failed checks."""
        recommendations = []
        failed_checks = self.get_failed_checks()

        for check in failed_checks:
            if check.name == "Python 3.11+":
                recommendations.append("Upgrade Python to version 3.11 or higher")
            elif check.name == "ffmpeg-python":
                recommendations.append("Install ffmpeg-python: uv add ffmpeg-python")
            elif check.name == "Redis connectivity":
                recommendations.append("Start Redis server: sudo systemctl start redis-server")
            elif check.name == "Media directories":
                recommendations.append("Create media directories or run setup task T001")
            elif check.name.startswith("Disk space"):
                recommendations.append("Free up disk space or mount additional storage")

        return recommendations


def validate_system() -> Dict[str, Any]:
    """
    Run complete system validation check.

    Returns:
        Dictionary with validation results and recommendations
    """
    validator = SystemValidator()
    results = validator.run_all_checks()

    # Add recommendations if there are failures
    if results["overall_status"] == "FAIL":
        results["recommendations"] = validator.get_recommendations()

    return results


def check_video_generation_readiness() -> bool:
    """
    Quick check if system is ready for video generation.

    Returns:
        True if all required dependencies are available
    """
    try:
        results = validate_system()
        return results["ready_for_video_generation"]
    except Exception as e:
        logger.error(f"Error checking video generation readiness: {e}")
        return False


if __name__ == "__main__":
    # CLI interface for system checks
    import json

    results = validate_system()
    print(json.dumps(results, indent=2))

    if results["overall_status"] == "FAIL":
        print("\nRecommendations:")
        for rec in results.get("recommendations", []):
            print(f"  - {rec}")
        sys.exit(1)
    else:
        print("\n✅ System ready for video generation!")
        sys.exit(0)