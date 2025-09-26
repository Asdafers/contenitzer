"""
AI Processing Exception Types
Defines specific exceptions for AI-powered media generation errors.
"""


class AIProcessingError(Exception):
    """Base exception for AI processing errors."""
    def __init__(self, message: str, error_context: dict = None):
        super().__init__(message)
        self.error_context = error_context or {}


class GeminiAPIError(AIProcessingError):
    """Exception for Gemini API-related errors."""
    def __init__(self, message: str, api_error_code: str = None, error_context: dict = None):
        super().__init__(message, error_context)
        self.api_error_code = api_error_code


class GeminiRateLimitError(GeminiAPIError):
    """Exception for Gemini API rate limit exceeded."""
    def __init__(self, message: str = "Gemini API rate limit exceeded", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class GeminiContentFilterError(GeminiAPIError):
    """Exception for content filtered by Gemini safety policies."""
    def __init__(self, message: str = "Content filtered by safety policy", filtered_content: str = None):
        super().__init__(message, "CONTENT_FILTER")
        self.filtered_content = filtered_content


class GeminiModelUnavailableError(GeminiAPIError):
    """Exception for Gemini model unavailable."""
    def __init__(self, model_name: str, message: str = None):
        message = message or f"Gemini model '{model_name}' is unavailable"
        super().__init__(message, "MODEL_UNAVAILABLE")
        self.model_name = model_name


class ScriptAnalysisError(AIProcessingError):
    """Exception for script analysis failures."""
    def __init__(self, message: str, script_content: str = None, analysis_error: str = None):
        super().__init__(message)
        self.script_content = script_content
        self.analysis_error = analysis_error


class ImageGenerationError(AIProcessingError):
    """Exception for AI image generation failures."""
    def __init__(self, message: str, generation_prompt: str = None, model_response: str = None):
        super().__init__(message)
        self.generation_prompt = generation_prompt
        self.model_response = model_response


class AudioGenerationError(AIProcessingError):
    """Exception for AI audio generation failures."""
    def __init__(self, message: str, audio_requirements: dict = None):
        super().__init__(message)
        self.audio_requirements = audio_requirements or {}


class VideoGenerationError(AIProcessingError):
    """Exception for AI video generation failures."""
    def __init__(self, message: str, generation_prompt: str = None, model_response: str = None):
        super().__init__(message)
        self.generation_prompt = generation_prompt or ""
        self.model_response = model_response or ""


class AIProcessingTimeoutError(AIProcessingError):
    """Exception for AI processing timeout."""
    def __init__(self, message: str, processing_stage: str = None, timeout_seconds: int = None):
        super().__init__(message)
        self.processing_stage = processing_stage
        self.timeout_seconds = timeout_seconds


class NoFallbackError(AIProcessingError):
    """Exception indicating fallback behavior is disabled per requirements FR-006."""
    def __init__(self, original_error: Exception, processing_stage: str):
        message = f"AI processing failed at stage '{processing_stage}' - no fallback behavior allowed"
        super().__init__(message)
        self.original_error = original_error
        self.processing_stage = processing_stage


class AIModelValidationError(AIProcessingError):
    """Exception for invalid AI model parameters."""
    def __init__(self, message: str, model_name: str = None, invalid_params: dict = None):
        super().__init__(message)
        self.model_name = model_name
        self.invalid_params = invalid_params or {}


class ProgressTrackingError(AIProcessingError):
    """Exception for progress tracking failures during AI processing."""
    def __init__(self, message: str, session_id: str = None, processing_stage: str = None):
        super().__init__(message)
        self.session_id = session_id
        self.processing_stage = processing_stage


class ContentPlanningError(AIProcessingError):
    """Exception for content planning failures."""
    def __init__(self, message: str, script_content: str = None, planning_stage: str = None):
        super().__init__(message)
        self.script_content = script_content
        self.planning_stage = planning_stage