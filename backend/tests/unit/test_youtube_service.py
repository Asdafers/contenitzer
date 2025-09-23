import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.youtube_service import YouTubeService


class TestYouTubeService:
    """Unit tests for YouTube service"""

    @pytest.fixture
    def youtube_service(self):
        return YouTubeService(api_key="test-api-key")

    @pytest.fixture
    def mock_youtube_client(self):
        mock_client = Mock()
        mock_client.videoCategories.return_value.list.return_value.execute.return_value = {
            'items': [
                {'id': '1', 'snippet': {'title': 'Film & Animation', 'assignable': True}},
                {'id': '10', 'snippet': {'title': 'Music', 'assignable': True}},
                {'id': '22', 'snippet': {'title': 'People & Blogs', 'assignable': True}},
                {'id': '24', 'snippet': {'title': 'Entertainment', 'assignable': True}},
                {'id': '25', 'snippet': {'title': 'News & Politics', 'assignable': True}},
            ]
        }

        mock_client.videos.return_value.list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'video1',
                    'snippet': {
                        'title': 'Test Video 1',
                        'channelTitle': 'Test Channel',
                        'publishedAt': '2024-01-01T00:00:00Z',
                        'description': 'Test description',
                        'tags': ['test', 'video']
                    },
                    'statistics': {'viewCount': '1000000'}
                },
                {
                    'id': 'video2',
                    'snippet': {
                        'title': 'Another Test Video',
                        'channelTitle': 'Another Channel',
                        'publishedAt': '2024-01-02T00:00:00Z',
                        'description': 'Another description',
                        'tags': ['another', 'test']
                    },
                    'statistics': {'viewCount': '500000'}
                }
            ]
        }
        return mock_client

    @patch('src.services.youtube_service.build')
    async def test_get_trending_videos_by_categories(self, mock_build, youtube_service, mock_youtube_client):
        """Test getting trending videos by categories"""
        mock_build.return_value = mock_youtube_client

        result = await youtube_service.get_trending_videos_by_categories(
            timeframe="weekly",
            max_results_per_category=2
        )

        assert isinstance(result, dict)
        assert len(result) <= 5  # Top 5 categories

        # Check structure of results
        for category_name, videos in result.items():
            assert isinstance(category_name, str)
            assert isinstance(videos, list)

            for video in videos:
                assert 'id' in video
                assert 'title' in video
                assert 'channel_name' in video
                assert 'view_count' in video
                assert isinstance(video['view_count'], int)

    async def test_extract_themes_from_videos(self, youtube_service):
        """Test theme extraction from videos"""
        videos_by_category = {
            'Music': [
                {
                    'id': 'video1',
                    'title': 'Amazing Music Video Performance',
                    'channel_name': 'Music Channel',
                    'view_count': 1000000,
                    'tags': ['music', 'performance', 'amazing']
                },
                {
                    'id': 'video2',
                    'title': 'Best Music Compilation',
                    'channel_name': 'Compilation Channel',
                    'view_count': 800000,
                    'tags': ['music', 'compilation', 'best']
                }
            ]
        }

        result = await youtube_service.extract_themes_from_videos(videos_by_category)

        assert isinstance(result, dict)
        assert 'Music' in result

        themes = result['Music']
        assert isinstance(themes, list)
        assert len(themes) <= 3  # Top 3 themes

        for theme in themes:
            assert 'id' in theme
            assert 'name' in theme
            assert 'relevance_score' in theme
            assert isinstance(theme['relevance_score'], float)
            assert 0.0 <= theme['relevance_score'] <= 1.0

    @patch('src.services.youtube_service.build')
    async def test_validate_api_key_success(self, mock_build, youtube_service, mock_youtube_client):
        """Test successful API key validation"""
        mock_build.return_value = mock_youtube_client

        result = await youtube_service.validate_api_key()

        assert result is True
        mock_youtube_client.videos.return_value.list.assert_called_once()

    @patch('src.services.youtube_service.build')
    async def test_validate_api_key_failure(self, mock_build, youtube_service):
        """Test failed API key validation"""
        mock_client = Mock()
        mock_client.videos.return_value.list.return_value.execute.side_effect = Exception("Invalid API key")
        mock_build.return_value = mock_client

        result = await youtube_service.validate_api_key()

        assert result is False

    async def test_empty_videos_handling(self, youtube_service):
        """Test handling of empty video lists"""
        empty_videos = {}

        result = await youtube_service.extract_themes_from_videos(empty_videos)

        assert isinstance(result, dict)
        assert len(result) == 0

    async def test_theme_extraction_with_no_tags(self, youtube_service):
        """Test theme extraction when videos have no tags"""
        videos_by_category = {
            'Test Category': [
                {
                    'id': 'video1',
                    'title': 'Video Without Tags',
                    'channel_name': 'Test Channel',
                    'view_count': 100000,
                    'tags': []  # No tags
                }
            ]
        }

        result = await youtube_service.extract_themes_from_videos(videos_by_category)

        assert 'Test Category' in result
        themes = result['Test Category']

        # Should still extract themes from title words
        assert len(themes) > 0