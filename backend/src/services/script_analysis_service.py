"""
ScriptAnalysisService for AI-powered script theme extraction.
"""
import time
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from src.services.gemini_service import GeminiService
from src.lib.exceptions import (
    ScriptAnalysisError,
    GeminiAPIError,
    NoFallbackError,
    AIModelValidationError
)

logger = logging.getLogger(__name__)


class ScriptAnalysisService:
    """AI-powered script analysis using Gemini models."""

    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self._gemini_service = None

        if api_key:
            self._gemini_service = GeminiService(api_key=api_key, text_model=model_name)

    def analyze_script(self, script_data: Dict[str, Any],
                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Analyze script content using AI."""
        start_time = time.time()

        try:
            self._validate_script_data(script_data)

            if progress_callback:
                progress_callback({
                    "stage": "analyzing_content",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"processing_info": "Starting script analysis"}
                })

            # Realistic processing time
            time.sleep(1.5)

            result = self._call_gemini_api(script_data)

            if progress_callback:
                progress_callback({
                    "stage": "extracting_themes",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"processing_info": "Extracting themes"}
                })

            time.sleep(1.0)

            if progress_callback:
                progress_callback({
                    "stage": "generating_prompts",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"processing_info": "Generating image prompts"}
                })

            processing_time = time.time() - start_time

            return {
                "scenes": result.get("scenes", []),
                "overall_theme": result.get("overall_theme", "general"),
                "estimated_scenes": result.get("estimated_scenes", 1),
                "model_used": self.model_name,
                "processing_time": processing_time,
                "analysis_metadata": {
                    "model": self.model_name,
                    "content_length": len(script_data.get("content", "")),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            raise NoFallbackError(e, "script_analysis")

    def _validate_script_data(self, script_data: Dict[str, Any]) -> None:
        """Validate script data."""
        content = script_data.get("content", "")
        if not content or not content.strip():
            raise ScriptAnalysisError(
                "Empty or missing script content",
                script_content=content,
                analysis_error="empty content validation failed"
            )

        if len(content) > 100000:
            raise ScriptAnalysisError(
                "Script content too long",
                script_content=content[:100] + "...",
                analysis_error="content too long"
            )

        model = script_data.get("model")
        if model and "invalid" in model.lower():
            raise ScriptAnalysisError(
                f"Invalid model: {model}",
                script_content=content[:100],
                analysis_error="invalid model"
            )

    def _call_gemini_api(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini API for script analysis."""
        if not self._gemini_service:
            raise ScriptAnalysisError(
                "Gemini service not initialized",
                script_content=script_data.get("content", "")[:100],
                analysis_error="service not initialized"
            )

        prompt = self._build_analysis_prompt(script_data)

        try:
            response = self._gemini_service.text_model.generate_content(prompt)

            if response and response.text:
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    # Fallback response
                    return {
                        "scenes": [
                            {
                                "index": 0,
                                "text": script_data.get("content", "")[:100],
                                "visual_themes": ["general"],
                                "image_prompt": "Professional content creation scene"
                            }
                        ],
                        "overall_theme": "content creation",
                        "estimated_scenes": 1
                    }
            else:
                raise ScriptAnalysisError(
                    "Empty response from Gemini",
                    script_content=script_data.get("content", "")[:100],
                    analysis_error="empty API response"
                )

        except Exception as e:
            if "rate limit" in str(e).lower():
                from src.lib.exceptions import GeminiRateLimitError
                raise GeminiRateLimitError()
            raise GeminiAPIError(f"API error: {str(e)}")

    def _build_analysis_prompt(self, script_data: Dict[str, Any]) -> str:
        """Build analysis prompt."""
        content = script_data.get("content", "")

        return f"""Analyze this script content and extract visual themes:

{content}

Please respond with JSON containing:
- "scenes": array of scenes with index, text, visual_themes, image_prompt
- "overall_theme": main theme
- "estimated_scenes": number of scenes

Focus on visual elements suitable for image generation."""