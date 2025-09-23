from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for interacting with YouTube Data API v3"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    async def get_trending_videos_by_categories(
        self,
        timeframe: str = "weekly",
        max_results_per_category: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trending videos organized by categories

        Args:
            timeframe: 'weekly' or 'monthly' (used for caching strategy)
            max_results_per_category: Maximum videos to fetch per category

        Returns:
            Dictionary with category names as keys and video lists as values
        """
        try:
            # Get video categories
            categories_response = self.youtube.videoCategories().list(
                part='snippet',
                regionCode='US'
            ).execute()

            categories_by_name = {}
            for category in categories_response['items']:
                if category['snippet']['assignable']:  # Only assignable categories
                    categories_by_name[category['snippet']['title']] = category['id']

            # Get trending videos for each category
            trending_by_category = {}

            for category_name, category_id in list(categories_by_name.items())[:5]:  # Top 5 categories
                try:
                    # Get most popular videos in this category
                    videos_response = self.youtube.videos().list(
                        part='snippet,statistics',
                        chart='mostPopular',
                        videoCategoryId=category_id,
                        regionCode='US',
                        maxResults=max_results_per_category
                    ).execute()

                    videos = []
                    for video in videos_response['items']:
                        videos.append({
                            'id': video['id'],
                            'title': video['snippet']['title'],
                            'channel_name': video['snippet']['channelTitle'],
                            'view_count': int(video['statistics'].get('viewCount', 0)),
                            'published_at': video['snippet']['publishedAt'],
                            'description': video['snippet']['description'][:500],  # Truncate
                            'tags': video['snippet'].get('tags', [])
                        })

                    # Sort by view count and take top results
                    videos.sort(key=lambda x: x['view_count'], reverse=True)
                    trending_by_category[category_name] = videos[:max_results_per_category]

                except HttpError as e:
                    logger.warning(f"Failed to fetch videos for category {category_name}: {e}")
                    continue

            return trending_by_category

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise Exception(f"Failed to fetch trending videos: {e}")

    async def extract_themes_from_videos(
        self,
        videos_by_category: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract top 3 themes from each category's trending videos

        Args:
            videos_by_category: Videos organized by category

        Returns:
            Dictionary with category names and their top 3 themes
        """
        themes_by_category = {}

        for category_name, videos in videos_by_category.items():
            if not videos:
                continue

            # Simple theme extraction based on common keywords in titles and tags
            theme_keywords = {}

            for video in videos[:20]:  # Analyze top 20 videos per category
                # Extract keywords from title
                title_words = video['title'].lower().split()
                tags = [tag.lower() for tag in video.get('tags', [])]

                all_keywords = title_words + tags

                for keyword in all_keywords:
                    if len(keyword) > 3:  # Skip short words
                        theme_keywords[keyword] = theme_keywords.get(keyword, 0) + 1

            # Get top 3 most common themes
            sorted_themes = sorted(theme_keywords.items(), key=lambda x: x[1], reverse=True)[:3]

            themes = []
            for i, (theme_name, count) in enumerate(sorted_themes):
                themes.append({
                    'id': f"{category_name.lower().replace(' ', '_')}_{theme_name}_{i+1}",
                    'name': theme_name.title(),
                    'relevance_score': min(1.0, count / 10.0),  # Normalize to 0-1
                    'mention_count': count
                })

            themes_by_category[category_name] = themes

        return themes_by_category

    async def validate_api_key(self) -> bool:
        """Validate if the API key is working"""
        try:
            # Simple test call
            self.youtube.videos().list(
                part='id',
                chart='mostPopular',
                maxResults=1
            ).execute()
            return True
        except HttpError:
            return False