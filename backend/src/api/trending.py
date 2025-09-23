from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import logging

from ..services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)

router = APIRouter()


class TrendingAnalyzeRequest(BaseModel):
    timeframe: str  # 'weekly' or 'monthly'
    api_key: str


class ThemeResponse(BaseModel):
    id: str
    name: str
    relevance_score: float


class CategoryResponse(BaseModel):
    id: str
    name: str
    themes: List[ThemeResponse]


class TrendingAnalyzeResponse(BaseModel):
    categories: List[CategoryResponse]


@router.post("/api/trending/analyze", response_model=TrendingAnalyzeResponse)
async def analyze_trending(request: TrendingAnalyzeRequest):
    """
    Analyze YouTube trending content by categories
    Returns top 3 themes across top 5 categories
    """
    try:
        # Validate timeframe
        if request.timeframe not in ['weekly', 'monthly']:
            raise HTTPException(status_code=422, detail="Timeframe must be 'weekly' or 'monthly'")

        # Initialize YouTube service
        youtube_service = YouTubeService(request.api_key)

        # Validate API key first
        if not await youtube_service.validate_api_key():
            raise HTTPException(status_code=401, detail="Invalid YouTube API key")

        # Get trending videos by categories
        trending_videos = await youtube_service.get_trending_videos_by_categories(
            timeframe=request.timeframe,
            max_results_per_category=50
        )

        # Extract themes from videos
        themes_by_category = await youtube_service.extract_themes_from_videos(trending_videos)

        # Format response
        categories = []
        for category_name, themes in themes_by_category.items():
            category_response = CategoryResponse(
                id=str(uuid.uuid4()),
                name=category_name,
                themes=[
                    ThemeResponse(
                        id=theme["id"],
                        name=theme["name"],
                        relevance_score=theme["relevance_score"]
                    )
                    for theme in themes
                ]
            )
            categories.append(category_response)

        # Limit to top 5 categories
        categories = categories[:5]

        logger.info(f"Analyzed trending content for {request.timeframe} timeframe: {len(categories)} categories")

        return TrendingAnalyzeResponse(categories=categories)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze trending content: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/api/trending/categories")
async def get_categories():
    """Get available YouTube categories"""
    try:
        # This would normally require an API key, but for simplicity
        # return common categories
        categories = [
            {"id": "1", "name": "Film & Animation"},
            {"id": "2", "name": "Autos & Vehicles"},
            {"id": "10", "name": "Music"},
            {"id": "15", "name": "Pets & Animals"},
            {"id": "17", "name": "Sports"},
            {"id": "19", "name": "Travel & Events"},
            {"id": "20", "name": "Gaming"},
            {"id": "22", "name": "People & Blogs"},
            {"id": "23", "name": "Comedy"},
            {"id": "24", "name": "Entertainment"},
            {"id": "25", "name": "News & Politics"},
            {"id": "26", "name": "Howto & Style"},
            {"id": "27", "name": "Education"},
            {"id": "28", "name": "Science & Technology"}
        ]

        return {"categories": categories}

    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")