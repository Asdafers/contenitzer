# Import all models to ensure they are registered with SQLAlchemy
from .base import Base
from .user_config import UserConfig
from .content_category import ContentCategory
from .trending_content import TrendingContent
from .generated_theme import GeneratedTheme
from .video_script import VideoScript
from .video_project import VideoProject
from .media_asset import MediaAsset
from .composed_video import ComposedVideo
from .uploaded_script import UploadedScript
from .workflow import Workflow
from .generated_video import GeneratedVideo
from .video_generation_job import VideoGenerationJob
from .media_storage import MediaStorage
from .gemini_model_config import GeminiModelConfig
from .generation_plan import GenerationPlan

# Export all models
__all__ = [
    "Base",
    "UserConfig",
    "ContentCategory",
    "TrendingContent",
    "GeneratedTheme",
    "VideoScript",
    "VideoProject",
    "MediaAsset",
    "ComposedVideo",
    "UploadedScript",
    "Workflow",
    "GeneratedVideo",
    "VideoGenerationJob",
    "MediaStorage",
    "GeminiModelConfig",
    "GenerationPlan"
]