"""
ConfigurationProfile model for development environment configuration
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from urllib.parse import urlparse
import re


class ConfigurationProfile(BaseModel):
    """Complete development environment configuration profile"""

    # Redis Configuration
    redis_url: str = Field(..., description="Redis connection URL")
    redis_session_db: Optional[int] = Field(1, ge=0, le=15, description="Redis database for sessions")
    redis_task_db: Optional[int] = Field(2, ge=0, le=15, description="Redis database for tasks")

    # API Keys
    youtube_api_key: str = Field(..., min_length=1, description="YouTube Data API v3 key")
    gemini_api_key: str = Field(..., min_length=1, description="Google Gemini API key")

    # Service URLs
    backend_url: Optional[str] = Field("http://localhost:8000", description="Backend API URL")
    frontend_url: Optional[str] = Field("http://localhost:3000", description="Frontend URL")
    websocket_url: Optional[str] = Field(None, description="WebSocket connection URL")

    # Environment Settings
    environment: Literal["local", "docker", "cloud"] = Field("local", description="Environment type")

    @validator("redis_url")
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        parsed = urlparse(v)
        if parsed.scheme not in ["redis", "rediss"]:
            raise ValueError("Redis URL must use redis:// or rediss:// scheme")
        if not parsed.hostname:
            raise ValueError("Redis URL must include hostname")
        return v

    @validator("youtube_api_key", "gemini_api_key")
    def validate_api_keys(cls, v):
        """Validate API keys are not placeholder values"""
        placeholders = ["your_key_here", "YOUR_API_KEY", "placeholder", ""]
        if v in placeholders:
            raise ValueError("API key cannot be a placeholder value")
        if len(v) < 10:
            raise ValueError("API key seems too short (minimum 10 characters)")
        return v

    @validator("backend_url", "frontend_url")
    def validate_service_urls(cls, v):
        """Validate service URLs"""
        if v:
            parsed = urlparse(v)
            if parsed.scheme not in ["http", "https"]:
                raise ValueError("Service URLs must use http:// or https://")
            if not parsed.hostname:
                raise ValueError("Service URLs must include hostname")
        return v

    @validator("websocket_url")
    def validate_websocket_url(cls, v):
        """Validate WebSocket URL"""
        if v:
            parsed = urlparse(v)
            if parsed.scheme not in ["ws", "wss"]:
                raise ValueError("WebSocket URL must use ws:// or wss://")
            if not parsed.hostname:
                raise ValueError("WebSocket URL must include hostname")
        return v

    class Config:
        schema_extra = {
            "example": {
                "redis_url": "redis://localhost:6379/0",
                "redis_session_db": 1,
                "redis_task_db": 2,
                "youtube_api_key": "AIzaSyExample123456789",
                "gemini_api_key": "AIzaSyGeminiExample123456789",
                "backend_url": "http://localhost:8000",
                "frontend_url": "http://localhost:3000",
                "websocket_url": "ws://localhost:8000/ws",
                "environment": "local"
            }
        }