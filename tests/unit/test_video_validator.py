"""Unit tests for video validation utilities."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from backend.src.lib.video_validator import (
    VideoValidator,
    ValidationResult,
    ValidationLevel,
    VideoRequirements,
    validate_video_file,
    is_valid_video_file
)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_initialization(self):
        """Test ValidationResult initialization."""
        result = ValidationResult()

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}

    def test_add_error(self):
        """Test adding errors invalidates result."""
        result = ValidationResult()

        result.add_error("Test error")

        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding warnings doesn't invalidate result."""
        result = ValidationResult()

        result.add_warning("Test warning")

        assert result.is_valid is True
        assert "Test warning" in result.warnings


class TestVideoRequirements:
    """Test VideoRequirements dataclass."""

    def test_default_requirements(self):
        """Test default video requirements."""
        requirements = VideoRequirements()

        assert requirements.max_duration_seconds == 300
        assert requirements.min_duration_seconds == 1
        assert 'mp4' in requirements.allowed_formats
        assert 'h264' in requirements.required_codecs


class TestVideoValidator:
    """Test VideoValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = VideoValidator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, filename: str, content: bytes = b'fake video content') -> Path:
        """Helper to create temporary test files."""
        file_path = self.temp_dir / filename
        file_path.write_bytes(content)
        return file_path

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        nonexistent = self.temp_dir / "nonexistent.mp4"

        result = self.validator.validate_video(nonexistent, ValidationLevel.BASIC)

        assert result.is_valid is False
        assert any("does not exist" in error for error in result.errors)

    def test_validate_file_extension(self):
        """Test file extension validation."""
        # Valid extension
        valid_file = self.create_temp_file("test.mp4")
        result = self.validator.validate_video(valid_file, ValidationLevel.BASIC)

        # Should pass basic validation (file exists and has valid extension)
        extension_errors = [e for e in result.errors if "format" in e.lower()]
        assert len(extension_errors) == 0

        # Invalid extension
        invalid_file = self.create_temp_file("test.txt")
        result = self.validator.validate_video(invalid_file, ValidationLevel.BASIC)

        assert result.is_valid is False
        assert any("format" in error.lower() for error in result.errors)

    def test_validate_file_size(self):
        """Test file size validation."""
        # Create file with specific size
        large_content = b'x' * (50 * 1024 * 1024)  # 50MB
        large_file = self.create_temp_file("large.mp4", large_content)

        # Test with small size limit
        small_requirements = VideoRequirements(max_file_size_mb=10)
        validator = VideoValidator(small_requirements)

        result = validator.validate_video(large_file, ValidationLevel.BASIC)

        assert result.is_valid is False
        assert any("size" in error.lower() for error in result.errors)

    @patch('backend.src.lib.video_validator.is_ffmpeg_available')
    def test_validate_without_ffmpeg(self, mock_ffmpeg_available):
        """Test validation when FFmpeg is not available."""
        mock_ffmpeg_available.return_value = False

        validator = VideoValidator()
        video_file = self.create_temp_file("test.mp4")

        result = validator.validate_video(video_file, ValidationLevel.FULL)

        # Should only do basic validation
        assert result.is_valid is True  # Basic validation should pass

    @patch('backend.src.lib.video_validator.probe_video')
    @patch('backend.src.lib.video_validator.is_ffmpeg_available')
    def test_validate_with_ffmpeg_success(self, mock_ffmpeg_available, mock_probe):
        """Test validation with successful FFmpeg probe."""
        mock_ffmpeg_available.return_value = True
        mock_probe.return_value = {
            'duration': 30.0,
            'width': 1280,
            'height': 720,
            'codec_name': 'h264',
            'bit_rate': '1000000',
            'r_frame_rate': '30/1',
            'has_audio': True
        }

        validator = VideoValidator()
        video_file = self.create_temp_file("test.mp4")

        result = validator.validate_video(video_file, ValidationLevel.FULL)

        assert result.is_valid is True
        assert result.metadata['duration'] == 30.0
        assert result.metadata['width'] == 1280
        assert result.metadata['height'] == 720

    @patch('backend.src.lib.video_validator.probe_video')
    @patch('backend.src.lib.video_validator.is_ffmpeg_available')
    def test_validate_duration_limits(self, mock_ffmpeg_available, mock_probe):
        """Test duration validation limits."""
        mock_ffmpeg_available.return_value = True
        mock_probe.return_value = {
            'duration': 600.0,  # 10 minutes
            'width': 1280,
            'height': 720,
            'codec_name': 'h264'
        }

        # Test with 5-minute limit
        requirements = VideoRequirements(max_duration_seconds=300)
        validator = VideoValidator(requirements)
        video_file = self.create_temp_file("test.mp4")

        result = validator.validate_video(video_file, ValidationLevel.FULL)

        assert result.is_valid is False
        assert any("duration" in error.lower() for error in result.errors)

    @patch('backend.src.lib.video_validator.probe_video')
    @patch('backend.src.lib.video_validator.is_ffmpeg_available')
    def test_validate_resolution_limits(self, mock_ffmpeg_available, mock_probe):
        """Test resolution validation limits."""
        mock_ffmpeg_available.return_value = True
        mock_probe.return_value = {
            'duration': 30.0,
            'width': 4000,  # Too wide
            'height': 720,
            'codec_name': 'h264'
        }

        validator = VideoValidator()
        video_file = self.create_temp_file("test.mp4")

        result = validator.validate_video(video_file, ValidationLevel.FULL)

        assert result.is_valid is False
        assert any("width" in error.lower() for error in result.errors)

    def test_validate_batch(self):
        """Test batch validation of multiple files."""
        files = [
            self.create_temp_file("video1.mp4"),
            self.create_temp_file("video2.avi"),
            self.create_temp_file("invalid.txt")
        ]

        results = self.validator.validate_video_batch(files, ValidationLevel.BASIC)

        assert len(results) == 3
        assert results[str(files[0])].is_valid is True
        assert results[str(files[1])].is_valid is True
        assert results[str(files[2])].is_valid is False


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, filename: str) -> Path:
        """Helper to create temporary test files."""
        file_path = self.temp_dir / filename
        file_path.write_bytes(b'fake video content')
        return file_path

    def test_validate_video_file_function(self):
        """Test validate_video_file convenience function."""
        video_file = self.create_temp_file("test.mp4")

        result = validate_video_file(video_file, ValidationLevel.BASIC)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    def test_is_valid_video_file_function(self):
        """Test is_valid_video_file convenience function."""
        valid_file = self.create_temp_file("test.mp4")
        invalid_file = self.create_temp_file("test.txt")

        assert is_valid_video_file(valid_file) is True
        assert is_valid_video_file(invalid_file) is False

    def test_custom_requirements(self):
        """Test validation with custom requirements."""
        video_file = self.create_temp_file("test.mp4")
        custom_requirements = VideoRequirements(
            allowed_formats=['mp4'],
            max_file_size_mb=1
        )

        result = validate_video_file(video_file, requirements=custom_requirements)

        assert isinstance(result, ValidationResult)


if __name__ == '__main__':
    pytest.main([__file__])