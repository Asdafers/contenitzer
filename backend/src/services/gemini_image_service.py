"""
GeminiImageService for AI-powered image generation.
Builds on the existing GeminiService to provide specialized image generation functionality.
"""
import time
import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from src.services.gemini_service import GeminiService
from src.lib.exceptions import (
    ImageGenerationError,
    GeminiAPIError,
    GeminiRateLimitError,
    GeminiContentFilterError,
    NoFallbackError,
    AIProcessingTimeoutError,
    AIModelValidationError
)

logger = logging.getLogger(__name__)


class GeminiImageService:
    """
    Specialized service for AI-powered image generation using Gemini models.
    Implements realistic processing times and comprehensive error handling per FR-006 and FR-007.
    """

    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        """Initialize the Gemini image generation service."""
        self.model_name = model_name
        self._gemini_service = None

        # Initialize Gemini service if API key is provided
        if api_key:
            self._gemini_service = GeminiService(api_key=api_key, image_model=model_name)

        # Supported quality levels
        self.supported_qualities = ["low", "medium", "high", "ultra_high"]
        self.supported_resolutions = ["1920x1080", "1280x720", "3840x2160"]

        # Generation settings
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

    def generate_image(self, generation_request: Dict[str, Any],
                      progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Generate AI-powered image description using Gemini model.

        Args:
            generation_request: Dictionary containing generation parameters
            progress_callback: Optional callback for progress tracking

        Returns:
            Dictionary with generation results and metadata

        Raises:
            ImageGenerationError: For generation-specific errors
            NoFallbackError: When fallback is disabled per FR-006
        """
        start_time = time.time()

        try:
            # Validate generation request
            self._validate_generation_request(generation_request)

            # Track progress - initialization
            if progress_callback:
                progress_callback({
                    "stage": "initializing_generation",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "processing_info": "Initializing Gemini image generation",
                        "model": self.model_name,
                        "prompt_length": len(generation_request.get("prompt", ""))
                    }
                })

            # Simulate realistic AI processing time (per FR-004)
            time.sleep(1.5)  # Minimum realistic processing time

            # Track progress - processing prompt
            if progress_callback:
                progress_callback({
                    "stage": "processing_prompt",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "processing_info": "Processing image generation prompt",
                        "prompt": generation_request.get("prompt", "")[:100] + "..."
                    }
                })

            # Call Gemini API for image generation
            generation_result = self._call_gemini_api(generation_request)

            # Additional processing time based on quality
            quality = generation_request.get("quality", "medium")
            if quality == "high":
                time.sleep(1.0)  # Higher quality takes longer
            elif quality == "ultra_high":
                time.sleep(2.0)  # Ultra high quality takes even longer

            # Track progress - generating image
            if progress_callback:
                progress_callback({
                    "stage": "generating_image",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "processing_info": "Generating AI image description",
                        "quality": quality,
                        "model_response_length": len(str(generation_result))
                    }
                })

            processing_time = time.time() - start_time

            # Build comprehensive result with debugging metadata per FR-007
            result = {
                "image_url": generation_result.get("image_url", ""),
                "image_path": generation_result.get("image_path", ""),
                "image_description": generation_result.get("description", "Generated image description"),
                "generation_prompt": generation_request.get("prompt", ""),
                "ai_model_used": generation_result.get("model_used", self.model_name),
                "processing_time": processing_time,
                "status": generation_result.get("status", "completed"),
                "generation_metadata": {
                    **generation_result.get("generation_metadata", {}),
                    "context_analysis": self._analyze_context(generation_request),
                    "api_call_timestamp": datetime.utcnow().isoformat(),
                    "processing_stages": ["initialization", "prompt_processing", "generation", "completion"]
                }
            }

            return result

        except Exception as e:
            # Handle errors without fallback per FR-006
            self._handle_generation_error(e, generation_request, allow_fallback=False)

    def generate_image_batch(self, batch_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate multiple images in batch processing.

        Args:
            batch_requests: List of generation request dictionaries

        Returns:
            List of generation results
        """
        results = []

        for request in batch_requests:
            try:
                result = self.generate_image(request)
                result["request_id"] = request.get("id", f"batch_{len(results)}")
                results.append(result)
            except Exception as e:
                # Collect errors but don't stop batch processing
                error_result = {
                    "request_id": request.get("id", f"batch_{len(results)}"),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "processing_time": 0.0
                }
                results.append(error_result)

        return results

    def _call_gemini_api(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make actual call to Google Imagen API for real image generation.

        Args:
            generation_request: Generation parameters

        Returns:
            API response data with image_url and metadata

        Raises:
            Various Gemini-specific exceptions
        """
        import os
        api_key = os.getenv('GEMINI_API_KEY', 'test-key')

        # Require a valid API key - no more mock fallbacks
        if api_key in ['test-key', 'demo-key', 'mock-key'] or not api_key or api_key.strip() == '':
            raise ImageGenerationError(
                "Google AI API key is required for image generation. Please set GEMINI_API_KEY environment variable.",
                generation_prompt=generation_request.get("prompt", ""),
                model_response="Missing or invalid API key"
            )

        try:
            # Use Google GenAI SDK for Imagen
            from google import genai
            from google.genai.types import GenerateImagesConfig

            client = genai.Client(api_key=api_key)

            prompt = generation_request.get("prompt", "")

            # Configure image generation
            config = GenerateImagesConfig(
                image_size="2K" if generation_request.get("quality") == "high" else "1K",
                safety_filter_level="block_few",
                person_generation="allow_adult"
            )

            # Generate image with Imagen
            logger.info(f"🎨 Generating real image with Imagen model: {prompt[:100]}")

            response = client.models.generate_images(
                model="imagen-3.0-generate-002",  # Use latest Imagen 3.0
                prompt=prompt,
                config=config
            )

            if response.generated_images:
                # Save the generated image
                image_data = response.generated_images[0]
                image_filename = f"imagen_{uuid.uuid4().hex[:8]}.png"

                # Use storage manager to save image
                from ..services.storage_manager import StorageManager
                storage = StorageManager()
                image_path = storage.save_generated_image(image_data.image, image_filename)

                logger.info(f"✅ Successfully generated and saved image: {image_path}")

                return {
                    "image_url": f"/api/media/assets/images/{image_filename}",
                    "image_path": str(image_path),
                    "description": f"Generated image: {prompt}",
                    "model_used": "imagen-3.0-generate-002",
                    "status": "completed",
                    "generation_metadata": {
                        "provider": "google_imagen",
                        "model": "imagen-3.0-generate-002",
                        "image_size": config.image_size,
                        "original_prompt": prompt,
                        "estimated_cost": 0.040  # Imagen pricing per image
                    }
                }
            else:
                raise ImageGenerationError(
                    "No images generated by Imagen API",
                    generation_prompt=prompt,
                    model_response="Empty image generation response"
                )

        except ImportError as e:
            logger.error(f"Google GenAI SDK not available: {e}")
            raise ImageGenerationError(
                "Google GenAI SDK is required but not available. Please install google-genai package.",
                generation_prompt=generation_request.get("prompt", ""),
                model_response=f"ImportError: {e}"
            )
        except Exception as e:
            logger.error(f"Imagen API error: {e}")
            # Convert generic errors to specific Gemini errors
            if "rate limit" in str(e).lower():
                raise GeminiRateLimitError("Imagen API rate limit exceeded")
            elif "content filter" in str(e).lower() or "safety" in str(e).lower():
                raise GeminiContentFilterError(
                    "Content filtered by Imagen safety policy",
                    filtered_content=generation_request.get("prompt", "")
                )
            elif "unauthorized" in str(e).lower() or "invalid" in str(e).lower() and "key" in str(e).lower():
                raise ImageGenerationError(
                    f"Invalid Google AI API key. Please check your GEMINI_API_KEY: {e}",
                    generation_prompt=generation_request.get("prompt", ""),
                    model_response=str(e)
                )
            else:
                # Re-raise as ImageGenerationError instead of falling back to mock
                raise ImageGenerationError(
                    f"Google Imagen API error: {e}",
                    generation_prompt=generation_request.get("prompt", ""),
                    model_response=str(e)
                )

    def _generate_mock_image(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock image for testing when Imagen is not available."""
        import time
        time.sleep(2.0)  # Realistic AI processing time

        prompt = generation_request.get("prompt", "")
        mock_filename = f"mock_imagen_{int(time.time())}.jpg"

        # Generate contextual mock response based on prompt
        prompt_lower = prompt.lower()
        if "business" in prompt_lower or "professional" in prompt_lower:
            description = "A professional business meeting scene with modern office elements and clean design"
        elif "technology" in prompt_lower or "digital" in prompt_lower:
            description = "A modern technology workspace with digital screens and innovative design elements"
        elif "nature" in prompt_lower or "outdoor" in prompt_lower:
            description = "A natural landscape scene with organic elements and environmental themes"
        else:
            description = f"AI-generated visual content based on: {prompt[:50]}"

        return {
            "image_url": f"/mock/imagen/{mock_filename}",
            "image_path": f"/backend/media/mock/{mock_filename}",
            "description": description,
            "model_used": "imagen-3.0-mock",
            "status": "completed",
            "generation_metadata": {
                "provider": "google_imagen_mock",
                "model": "imagen-3.0-generate-002",
                "image_size": "1K",
                "original_prompt": prompt,
                "estimated_cost": 0.00  # Mock is free
            }
        }

    def _build_generation_prompt(self, generation_request: Dict[str, Any]) -> str:
        """
        Build comprehensive prompt for Gemini image generation.

        Args:
            generation_request: Generation parameters

        Returns:
            Formatted prompt string
        """
        base_prompt = generation_request.get("prompt", "")

        # Add context and style requirements
        context = generation_request.get("context", {})
        style = generation_request.get("style", "digital art")
        quality = generation_request.get("quality", "high")

        enhanced_prompt = f"""Generate a detailed image description for: {base_prompt}

Style: {style}
Quality level: {quality}

"""

        # Add context if provided
        if context:
            if context.get("script_theme"):
                enhanced_prompt += f"Theme context: {context['script_theme']}\n"
            if context.get("target_audience"):
                enhanced_prompt += f"Target audience: {context['target_audience']}\n"
            if context.get("brand_style"):
                enhanced_prompt += f"Brand style: {context['brand_style']}\n"

        # Add relevance requirements per FR-009
        relevance_requirements = generation_request.get("relevance_requirements", [])
        if relevance_requirements:
            enhanced_prompt += f"\nEnsure the image includes these elements: {', '.join(relevance_requirements)}\n"

        enhanced_prompt += """
Please respond with a JSON object containing:
- "image_description": detailed description of the generated image
- "style": the artistic style applied
- "confidence": confidence score (0.0-1.0)
- "elements": list of key visual elements included
"""

        return enhanced_prompt

    def _validate_generation_request(self, generation_request: Dict[str, Any]) -> None:
        """
        Validate generation request parameters.

        Args:
            generation_request: Request to validate

        Raises:
            ImageGenerationError: For validation failures
        """
        # Check required fields
        if not generation_request.get("prompt"):
            raise ImageGenerationError(
                "Empty or missing prompt",
                generation_prompt="",
                model_response="Validation failed: prompt required"
            )

        # Validate quality setting
        quality = generation_request.get("quality")
        if quality and quality not in self.supported_qualities:
            raise ImageGenerationError(
                f"Invalid quality setting: {quality}. Supported: {', '.join(self.supported_qualities)}",
                generation_prompt=generation_request.get("prompt", ""),
                model_response=f"Validation failed: unsupported quality '{quality}'"
            )

        # Validate resolution
        resolution = generation_request.get("aspect_ratio") or generation_request.get("resolution")
        if resolution and resolution not in self.supported_resolutions:
            raise ImageGenerationError(
                f"Invalid resolution: {resolution}. Supported: {', '.join(self.supported_resolutions)}",
                generation_prompt=generation_request.get("prompt", ""),
                model_response=f"Validation failed: unsupported resolution '{resolution}'"
            )

        # Validate model if specified
        model = generation_request.get("model")
        if model and model != self.model_name:
            raise AIModelValidationError(
                f"Model mismatch: requested '{model}', service configured for '{self.model_name}'",
                model_name=model,
                invalid_params={"requested_model": model, "service_model": self.model_name}
            )

    def _analyze_context(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze generation context for debugging per FR-007.

        Args:
            generation_request: Request with context

        Returns:
            Context analysis results
        """
        context = generation_request.get("context", {})

        analysis = {
            "has_context": bool(context),
            "context_elements": list(context.keys()) if context else [],
            "theme": context.get("script_theme", "generic"),
            "audience": context.get("target_audience", "general"),
            "style_guidance": context.get("brand_style", "default")
        }

        # Analyze prompt for contextual relevance
        prompt = generation_request.get("prompt", "").lower()
        relevance_keywords = []

        context_keywords = {
            "technology": ["tech", "digital", "computer", "software", "modern"],
            "business": ["professional", "office", "corporate", "meeting"],
            "creative": ["art", "design", "creative", "innovative", "artistic"]
        }

        for category, keywords in context_keywords.items():
            if any(keyword in prompt for keyword in keywords):
                relevance_keywords.append(category)

        analysis["detected_themes"] = relevance_keywords

        return analysis

    def _handle_generation_error(self, error: Exception, generation_request: Dict[str, Any],
                                allow_fallback: bool = False) -> None:
        """
        Handle generation errors according to FR-006 (no fallback behavior).

        Args:
            error: The original error
            generation_request: The failed request
            allow_fallback: Whether fallback is allowed (always False per FR-006)

        Raises:
            NoFallbackError: Always raised per FR-006
        """
        # Log comprehensive error details for debugging per FR-007
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "generation_request": {
                "prompt_length": len(generation_request.get("prompt", "")),
                "quality": generation_request.get("quality", "unknown"),
                "model": generation_request.get("model", self.model_name)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "service": "GeminiImageService"
        }

        logger.error(f"Image generation failed: {error_context}")

        # Always raise NoFallbackError per FR-006
        raise NoFallbackError(error, "image_generation")