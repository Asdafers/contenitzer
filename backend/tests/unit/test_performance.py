import pytest
import time
import asyncio
from unittest.mock import Mock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.youtube_service import YouTubeService
from src.services.gemini_service import GeminiService
from src.lib.storage import StorageManager
from src.lib.tasks import AsyncTaskManager


class TestPerformance:
    """Performance tests for core services"""

    @pytest.fixture
    def youtube_service(self):
        return YouTubeService(api_key="test-key")

    @pytest.fixture
    def gemini_service(self):
        return GeminiService(api_key="test-key")

    def test_storage_manager_initialization(self):
        """Test storage manager initialization time"""
        start_time = time.time()

        storage_manager = StorageManager(base_path="/tmp/test_storage")

        initialization_time = time.time() - start_time

        # Should initialize quickly (under 100ms)
        assert initialization_time < 0.1

        # Verify directories are created
        assert storage_manager.base_path.exists()
        assert storage_manager.audio_path.exists()
        assert storage_manager.images_path.exists()

    async def test_theme_extraction_performance(self, youtube_service):
        """Test theme extraction performance with large dataset"""
        # Create mock data with many videos
        large_video_dataset = {}
        for category in ['Music', 'Gaming', 'Education', 'Entertainment', 'Technology']:
            videos = []
            for i in range(100):  # 100 videos per category
                videos.append({
                    'id': f'video_{category}_{i}',
                    'title': f'Test Video {i} about {category.lower()} content',
                    'channel_name': f'Channel {i}',
                    'view_count': 1000000 - (i * 1000),
                    'tags': [category.lower(), 'test', f'topic{i % 10}']
                })
            large_video_dataset[category] = videos

        start_time = time.time()

        result = await youtube_service.extract_themes_from_videos(large_video_dataset)

        processing_time = time.time() - start_time

        # Should process 500 videos in under 2 seconds
        assert processing_time < 2.0

        # Verify results structure
        assert len(result) == 5
        for category, themes in result.items():
            assert len(themes) <= 3  # Top 3 themes per category

    async def test_script_generation_mock_performance(self, gemini_service):
        """Test script generation performance (mocked)"""
        # Mock the actual API call to test our processing logic
        with pytest.mock.patch.object(gemini_service.client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Speaker 1: Test content\nSpeaker 2: Response" * 50
            mock_create.return_value = mock_response

            start_time = time.time()

            result = await gemini_service.generate_script_from_theme(
                theme_name="Performance Test Theme",
                min_duration_seconds=180
            )

            processing_time = time.time() - start_time

            # Should process quickly (under 100ms for our logic)
            assert processing_time < 0.1

            # Verify result structure
            assert 'content' in result
            assert 'estimated_duration' in result
            assert result['estimated_duration'] >= 180

    def test_task_manager_performance(self):
        """Test async task manager performance"""
        task_manager = AsyncTaskManager()

        # Test adding many tasks quickly
        start_time = time.time()

        async def dummy_task():
            await asyncio.sleep(0.001)  # Minimal async work
            return "completed"

        # Submit 100 tasks
        task_ids = []
        for i in range(100):
            task_id = asyncio.run(task_manager.submit_task(
                dummy_task,
                task_name=f"perf_test_{i}"
            ))
            task_ids.append(task_id)

        submission_time = time.time() - start_time

        # Should submit 100 tasks quickly (under 500ms)
        assert submission_time < 0.5

        # Verify all tasks were submitted
        assert len(task_ids) == 100

        # Check task manager state
        all_tasks = task_manager.get_all_tasks()
        assert len(all_tasks) == 100

    def test_storage_stats_performance(self):
        """Test storage statistics calculation performance"""
        storage_manager = StorageManager(base_path="/tmp/perf_test_storage")

        # Create some test files
        test_files = []
        for i in range(50):
            file_path = storage_manager.get_temp_path(f"test_file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}" * 100)  # Some content
            test_files.append(file_path)

        start_time = time.time()

        stats = storage_manager.get_storage_stats()

        stats_time = time.time() - start_time

        # Should calculate stats quickly (under 200ms)
        assert stats_time < 0.2

        # Verify stats structure
        assert 'temp' in stats
        assert 'total' in stats
        assert stats['temp']['file_count'] >= 50

        # Cleanup
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def test_concurrent_task_performance(self):
        """Test performance with concurrent tasks"""
        task_manager = AsyncTaskManager()

        async def io_intensive_task(task_id: int):
            # Simulate I/O intensive work
            await asyncio.sleep(0.01)
            return f"Task {task_id} completed"

        start_time = time.time()

        # Submit 20 concurrent tasks
        task_ids = []
        for i in range(20):
            task_id = await task_manager.submit_task(
                io_intensive_task,
                i,
                task_name=f"concurrent_task_{i}"
            )
            task_ids.append(task_id)

        # Wait a bit for tasks to complete
        await asyncio.sleep(0.5)

        total_time = time.time() - start_time

        # Concurrent execution should be faster than sequential (under 300ms)
        assert total_time < 0.3

        # Check that most tasks completed
        completed_count = 0
        for task_id in task_ids:
            task_result = task_manager.get_task_status(task_id)
            if task_result and task_result.status.value == 'completed':
                completed_count += 1

        # At least 80% should have completed
        assert completed_count >= 16

    def test_memory_usage_reasonable(self):
        """Test that services don't use excessive memory"""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create multiple service instances
        services = []
        for i in range(10):
            youtube_service = YouTubeService(api_key=f"test-key-{i}")
            gemini_service = GeminiService(api_key=f"test-key-{i}")
            storage_manager = StorageManager(base_path=f"/tmp/test_storage_{i}")
            services.append((youtube_service, gemini_service, storage_manager))

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (under 50MB for 10 service instances)
        assert memory_increase < 50

        # Cleanup
        del services
        gc.collect()