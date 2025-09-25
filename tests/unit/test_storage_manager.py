"""Unit tests for storage manager service."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from datetime import datetime, timedelta

from backend.src.services.storage_manager import (
    StorageManager,
    StorageManagerError,
    StorageRecord
)


class TestStorageManager:
    """Test StorageManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage_manager = StorageManager(base_path=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test StorageManager initialization."""
        assert self.storage_manager.base_path == self.temp_dir
        assert self.storage_manager.base_path.exists()

    def test_create_directory_structure(self):
        """Test directory structure creation."""
        records = self.storage_manager.initialize_storage_records()

        # Check that directories were created
        expected_dirs = ['videos', 'assets/images', 'assets/audio', 'assets/temp', 'stock']

        for dir_path in expected_dirs:
            full_path = self.temp_dir / dir_path
            assert full_path.exists()
            assert full_path.is_dir()

        # Check that records were created
        assert len(records) == len(expected_dirs)

    def test_get_storage_path(self):
        """Test storage path generation."""
        video_path = self.storage_manager.get_storage_path('videos', 'test.mp4')
        image_path = self.storage_manager.get_storage_path('assets/images', 'test.jpg')

        assert video_path == self.temp_dir / 'videos' / 'test.mp4'
        assert image_path == self.temp_dir / 'assets' / 'images' / 'test.jpg'

    def test_store_file(self):
        """Test file storage."""
        # Create source file
        source_file = self.temp_dir / 'source.txt'
        source_file.write_text('test content')

        # Store file
        stored_path = self.storage_manager.store_file(
            source_file, 'assets/temp', 'stored.txt'
        )

        assert stored_path.exists()
        assert stored_path.read_text() == 'test content'
        assert stored_path.parent == self.temp_dir / 'assets' / 'temp'

    def test_store_file_with_move(self):
        """Test file storage with move operation."""
        # Create source file
        source_file = self.temp_dir / 'source.txt'
        source_file.write_text('test content')

        # Store file with move
        stored_path = self.storage_manager.store_file(
            source_file, 'videos', 'moved.txt', move=True
        )

        assert stored_path.exists()
        assert not source_file.exists()  # Source should be moved

    def test_store_file_content(self):
        """Test storing file content directly."""
        content = b'binary content'

        stored_path = self.storage_manager.store_file_content(
            content, 'assets/temp', 'binary.bin'
        )

        assert stored_path.exists()
        assert stored_path.read_bytes() == content

    def test_delete_file(self):
        """Test file deletion."""
        # Create and store file
        test_file = self.temp_dir / 'assets' / 'temp' / 'test.txt'
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('test')

        # Delete file
        success = self.storage_manager.delete_file('assets/temp', 'test.txt')

        assert success is True
        assert not test_file.exists()

    def test_delete_nonexistent_file(self):
        """Test deletion of non-existent file."""
        success = self.storage_manager.delete_file('assets/temp', 'nonexistent.txt')
        assert success is False

    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        # Create temp files with different ages
        temp_dir = self.temp_dir / 'assets' / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)

        old_file = temp_dir / 'old.txt'
        new_file = temp_dir / 'new.txt'

        old_file.write_text('old')
        new_file.write_text('new')

        # Make old file appear old
        old_time = datetime.now() - timedelta(hours=25)
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Cleanup files older than 24 hours
        cleaned = self.storage_manager.cleanup_temp_files(max_age_hours=24)

        assert cleaned == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_get_directory_size(self):
        """Test directory size calculation."""
        # Create files in directory
        video_dir = self.temp_dir / 'videos'
        video_dir.mkdir(parents=True, exist_ok=True)

        file1 = video_dir / 'video1.mp4'
        file2 = video_dir / 'video2.mp4'

        file1.write_bytes(b'x' * 1000)  # 1KB
        file2.write_bytes(b'x' * 2000)  # 2KB

        size = self.storage_manager.get_directory_size('videos')

        assert size == 3000  # 3KB total

    def test_get_storage_stats(self):
        """Test storage statistics generation."""
        # Create some files
        self.storage_manager.initialize_storage_records()

        video_dir = self.temp_dir / 'videos'
        video_dir.mkdir(parents=True, exist_ok=True)
        (video_dir / 'test.mp4').write_bytes(b'x' * 1000)

        stats = self.storage_manager.get_storage_stats()

        assert 'total' in stats
        assert 'videos' in stats
        assert stats['total']['file_count'] > 0
        assert stats['total']['total_size'] > 0

    def test_enforce_quota(self):
        """Test storage quota enforcement."""
        # Set small quota
        self.storage_manager.max_storage_mb = 1  # 1MB

        # Try to store large file
        large_content = b'x' * (2 * 1024 * 1024)  # 2MB

        with pytest.raises(StorageManagerError, match="quota"):
            self.storage_manager.store_file_content(
                large_content, 'videos', 'large.mp4'
            )

    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        # Create existing file
        existing = self.temp_dir / 'assets' / 'temp' / 'test.txt'
        existing.parent.mkdir(parents=True, exist_ok=True)
        existing.write_text('existing')

        # Generate unique filename
        unique_path = self.storage_manager.get_storage_path('assets/temp', 'test.txt')
        unique_filename = self.storage_manager._generate_unique_filename(unique_path)

        assert unique_filename != 'test.txt'
        assert 'test' in unique_filename
        assert '.txt' in unique_filename

    def test_validate_storage_type(self):
        """Test storage type validation."""
        # Valid types should work
        valid_path = self.storage_manager.get_storage_path('videos', 'test.mp4')
        assert valid_path is not None

        # Invalid types should raise error
        with pytest.raises(StorageManagerError, match="Invalid storage type"):
            self.storage_manager.get_storage_path('invalid', 'test.mp4')

    @patch('shutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage):
        """Test disk usage calculation."""
        # Mock disk usage return value (total, used, free)
        mock_disk_usage.return_value = (1000000000, 400000000, 600000000)

        usage = self.storage_manager.get_disk_usage()

        assert usage['total_mb'] == pytest.approx(953.67, rel=1e-2)
        assert usage['used_mb'] == pytest.approx(381.47, rel=1e-2)
        assert usage['free_mb'] == pytest.approx(572.20, rel=1e-2)
        assert usage['used_percentage'] == pytest.approx(40.0, rel=1e-2)


class TestStorageRecord:
    """Test StorageRecord dataclass."""

    def test_storage_record_creation(self):
        """Test StorageRecord creation and methods."""
        path = Path('/test/path')
        record = StorageRecord(
            path=path,
            storage_type='videos',
            created_at=datetime.now(),
            file_count=5,
            total_size=1000
        )

        assert record.path == path
        assert record.storage_type == 'videos'
        assert record.file_count == 5
        assert record.total_size == 1000

    def test_storage_record_dict_conversion(self):
        """Test StorageRecord to dict conversion."""
        record = StorageRecord(
            path=Path('/test'),
            storage_type='images',
            created_at=datetime.now(),
            file_count=0,
            total_size=0
        )

        record_dict = record.to_dict()

        assert record_dict['path'] == '/test'
        assert record_dict['storage_type'] == 'images'
        assert 'created_at' in record_dict
        assert record_dict['file_count'] == 0


if __name__ == '__main__':
    pytest.main([__file__])