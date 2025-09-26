from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
import os
import time
from datetime import datetime, timedelta
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google Gemini APIs for content generation

    Supports configurable models for different purposes:
    - Text/script generation: uses text_model (default: "gemini-pro")
    - Image generation: uses image_model (default: "gemini-2.5-flash-image" or GEMINI_IMAGE_MODEL env var)

    Model configuration can be set at initialization or changed at runtime using
    set_text_model() and set_image_model() methods.
    """

    def __init__(self, api_key: str, text_model: str = None, image_model: str = None):
        genai.configure(api_key=api_key)

        # Default models
        self.text_model_name = text_model or "gemini-pro"
        self.image_model_name = image_model or os.getenv('GEMINI_IMAGE_MODEL', "gemini-2.5-flash-image")

        # Initialize model instances
        self.text_model = genai.GenerativeModel(self.text_model_name)
        self.image_model = genai.GenerativeModel(self.image_model_name)

        # Availability checking cache
        self._availability_cache = {}
        self._cache_ttl_seconds = 60  # Cache for 60 seconds
        self._last_availability_log = {}  # Track status changes for logging

        # Store API key for availability checks
        self._api_key = api_key

    def get_text_model(self) -> str:
        """Get the current text generation model name"""
        return self.text_model_name

    def get_image_model(self) -> str:
        """Get the current image generation model name"""
        return self.image_model_name

    def set_text_model(self, model_name: str) -> None:
        """Set the text generation model"""
        old_model = self.text_model_name
        self.text_model_name = model_name
        self.text_model = genai.GenerativeModel(model_name)

        # Clear cache for the old model since it's no longer in use
        if old_model in self._availability_cache:
            del self._availability_cache[old_model]

        logger.info(f"Text model changed from {old_model} to {model_name}")

    def set_image_model(self, model_name: str) -> None:
        """Set the image generation model"""
        old_model = self.image_model_name
        self.image_model_name = model_name
        self.image_model = genai.GenerativeModel(model_name)

        # Clear cache for the old model since it's no longer in use
        if old_model in self._availability_cache:
            del self._availability_cache[old_model]

        logger.info(f"Image model changed from {old_model} to {model_name}")

    def get_model_configuration(self) -> Dict[str, str]:
        """Get the current model configuration"""
        return {
            "text_model": self.text_model_name,
            "image_model": self.image_model_name
        }

    def _is_cache_valid(self, model_name: str) -> bool:
        """Check if the cached availability status is still valid"""
        if model_name not in self._availability_cache:
            return False

        cache_entry = self._availability_cache[model_name]
        return time.time() - cache_entry.get('timestamp', 0) < self._cache_ttl_seconds

    def _get_cached_availability(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get cached availability status if valid"""
        if self._is_cache_valid(model_name):
            return self._availability_cache[model_name]['status']
        return None

    def _cache_availability(self, model_name: str, status: Dict[str, Any]) -> None:
        """Cache availability status with timestamp"""
        self._availability_cache[model_name] = {
            'status': status,
            'timestamp': time.time()
        }

        # Log status changes
        previous_status = self._last_availability_log.get(model_name, {}).get('available')
        current_status = status.get('available')

        if previous_status != current_status:
            if current_status:
                logger.info(f"Model {model_name} is now available")
            else:
                logger.warning(f"Model {model_name} is now unavailable: {status.get('error', 'Unknown error')}")

            self._last_availability_log[model_name] = {'available': current_status, 'last_checked': datetime.now()}

    async def check_model_availability(self, model_name: str) -> Dict[str, Any]:
        """
        Check if a specific model is available and accessible

        Args:
            model_name: Name of the model to check

        Returns:
            Dictionary with availability status and details:
            {
                'available': bool,
                'model_name': str,
                'error': str (if not available),
                'error_type': str (if not available),
                'last_checked': datetime,
                'response_time_ms': int,
                'cached': bool
            }
        """
        # Check cache first
        cached_status = self._get_cached_availability(model_name)
        if cached_status is not None:
            cached_status['cached'] = True
            return cached_status

        # Perform actual availability check
        start_time = time.time()
        status = {
            'model_name': model_name,
            'last_checked': datetime.now(),
            'cached': False
        }

        try:
            # Try to instantiate the model
            test_model = genai.GenerativeModel(model_name)

            # Perform a simple test generation
            test_prompt = "Say 'test' if you can respond."

            # Use a timeout for the test call
            response = await asyncio.wait_for(
                asyncio.to_thread(test_model.generate_content, test_prompt),
                timeout=10.0  # 10 second timeout
            )

            # Check if we got a valid response
            if response and response.text:
                status.update({
                    'available': True,
                    'response_time_ms': int((time.time() - start_time) * 1000)
                })
                logger.debug(f"Model {model_name} availability check passed")
            else:
                status.update({
                    'available': False,
                    'error': 'Model returned empty response',
                    'error_type': 'empty_response',
                    'response_time_ms': int((time.time() - start_time) * 1000)
                })

        except asyncio.TimeoutError:
            status.update({
                'available': False,
                'error': 'Model response timeout (10s)',
                'error_type': 'timeout',
                'response_time_ms': int((time.time() - start_time) * 1000)
            })
            logger.warning(f"Model {model_name} availability check timed out")

        except GoogleAPIError as e:
            error_message = str(e)
            error_type = 'api_error'

            # Categorize different types of API errors
            if 'not found' in error_message.lower() or 'does not exist' in error_message.lower():
                error_type = 'model_not_found'
            elif 'quota' in error_message.lower() or 'rate limit' in error_message.lower():
                error_type = 'rate_limit'
            elif 'permission' in error_message.lower() or 'unauthorized' in error_message.lower():
                error_type = 'permission_denied'
            elif 'network' in error_message.lower() or 'connection' in error_message.lower():
                error_type = 'network_error'

            status.update({
                'available': False,
                'error': error_message,
                'error_type': error_type,
                'response_time_ms': int((time.time() - start_time) * 1000)
            })
            logger.error(f"Model {model_name} availability check failed with API error: {error_message}")

        except Exception as e:
            status.update({
                'available': False,
                'error': f"Unexpected error: {str(e)}",
                'error_type': 'unknown_error',
                'response_time_ms': int((time.time() - start_time) * 1000)
            })
            logger.error(f"Model {model_name} availability check failed with unexpected error: {str(e)}")

        # Cache the result
        self._cache_availability(model_name, status)

        return status

    async def check_all_models_availability(self) -> Dict[str, Dict[str, Any]]:
        """
        Check availability of both text and image models

        Returns:
            Dictionary with availability status for all configured models:
            {
                'text_model': {...availability status...},
                'image_model': {...availability status...},
                'overall_status': 'available'|'partial'|'unavailable',
                'summary': str
            }
        """
        logger.info("Checking availability of all configured models")

        # Check both models concurrently
        text_task = self.check_model_availability(self.text_model_name)
        image_task = self.check_model_availability(self.image_model_name)

        text_status, image_status = await asyncio.gather(text_task, image_task, return_exceptions=True)

        # Handle any exceptions from the tasks
        if isinstance(text_status, Exception):
            text_status = {
                'available': False,
                'model_name': self.text_model_name,
                'error': f"Check failed: {str(text_status)}",
                'error_type': 'check_exception',
                'last_checked': datetime.now(),
                'cached': False
            }

        if isinstance(image_status, Exception):
            image_status = {
                'available': False,
                'model_name': self.image_model_name,
                'error': f"Check failed: {str(image_status)}",
                'error_type': 'check_exception',
                'last_checked': datetime.now(),
                'cached': False
            }

        # Determine overall status
        text_available = text_status.get('available', False)
        image_available = image_status.get('available', False)

        if text_available and image_available:
            overall_status = 'available'
            summary = 'All models are available'
        elif text_available or image_available:
            overall_status = 'partial'
            available_models = []
            if text_available:
                available_models.append('text')
            if image_available:
                available_models.append('image')
            summary = f"Partially available: {', '.join(available_models)} model(s) working"
        else:
            overall_status = 'unavailable'
            summary = 'No models are available'

        result = {
            'text_model': text_status,
            'image_model': image_status,
            'overall_status': overall_status,
            'summary': summary
        }

        logger.info(f"Model availability check complete: {summary}")
        return result

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check including API connectivity, model access, and rate limits

        Returns:
            Dictionary with comprehensive health status:
            {
                'healthy': bool,
                'api_connectivity': bool,
                'models': {...model availability...},
                'rate_limit_status': dict,
                'last_check': datetime,
                'issues': List[str]
            }
        """
        logger.info("Performing comprehensive Gemini service health check")

        health_status = {
            'last_check': datetime.now(),
            'issues': []
        }

        try:
            # Check API connectivity with a simple call
            start_time = time.time()
            try:
                # Try to list available models to test API connectivity
                models = await asyncio.to_thread(genai.list_models)
                api_connectivity = True
                api_response_time = int((time.time() - start_time) * 1000)
                logger.debug(f"API connectivity check passed ({api_response_time}ms)")
            except Exception as e:
                api_connectivity = False
                api_response_time = int((time.time() - start_time) * 1000)
                health_status['issues'].append(f"API connectivity failed: {str(e)}")
                logger.error(f"API connectivity check failed: {str(e)}")

            health_status.update({
                'api_connectivity': api_connectivity,
                'api_response_time_ms': api_response_time
            })

            # Check model availability
            models_status = await self.check_all_models_availability()
            health_status['models'] = models_status

            # Add issues for unavailable models
            if models_status['text_model'].get('available') is False:
                health_status['issues'].append(f"Text model unavailable: {models_status['text_model'].get('error', 'Unknown error')}")

            if models_status['image_model'].get('available') is False:
                health_status['issues'].append(f"Image model unavailable: {models_status['image_model'].get('error', 'Unknown error')}")

            # Simple rate limit check (detect rate limit errors from model checks)
            rate_limit_issues = []
            for model_type in ['text_model', 'image_model']:
                model_status = models_status[model_type]
                if model_status.get('error_type') == 'rate_limit':
                    rate_limit_issues.append(f"{model_type}: {model_status.get('error', 'Rate limited')}")

            health_status['rate_limit_status'] = {
                'limited': len(rate_limit_issues) > 0,
                'issues': rate_limit_issues
            }

            if rate_limit_issues:
                health_status['issues'].extend(rate_limit_issues)

            # Determine overall health
            health_status['healthy'] = (
                api_connectivity and
                models_status['overall_status'] != 'unavailable' and
                not health_status['rate_limit_status']['limited']
            )

            if health_status['healthy']:
                logger.info("Gemini service health check: HEALTHY")
            else:
                logger.warning(f"Gemini service health check: UNHEALTHY - Issues: {'; '.join(health_status['issues'])}")

        except Exception as e:
            health_status.update({
                'healthy': False,
                'api_connectivity': False,
                'error': f"Health check failed: {str(e)}"
            })
            health_status['issues'].append(f"Health check exception: {str(e)}")
            logger.error(f"Health check failed with exception: {str(e)}")

        return health_status

    def clear_availability_cache(self) -> None:
        """Clear the availability status cache to force fresh checks"""
        self._availability_cache.clear()
        logger.info("Availability cache cleared")

    async def generate_script_from_theme(
        self,
        theme_name: str,
        theme_description: str = "",
        min_duration_seconds: int = 180
    ) -> Dict[str, Any]:
        """
        Generate a conversational script from a theme

        Args:
            theme_name: The main theme/topic
            theme_description: Additional context about the theme
            min_duration_seconds: Minimum script duration in seconds

        Returns:
            Dictionary with script content and metadata
        """
        # Estimate words needed (approximately 150 words per minute for conversation)
        min_words = (min_duration_seconds / 60) * 150

        prompt = f"""
Create a conversational script between two speakers about the topic: "{theme_name}"

{f"Additional context: {theme_description}" if theme_description else ""}

Requirements:
- Format as a dialogue between Speaker 1 and Speaker 2
- Make it engaging and informative
- Minimum {min_words} words to ensure at least {min_duration_seconds // 60} minutes of content
- Use natural conversation flow with questions, responses, and insights
- Include interesting facts, examples, or perspectives
- End with a satisfying conclusion

Format each line as:
Speaker 1: [dialogue]
Speaker 2: [dialogue]
"""

        try:
            system_prompt = "You are an expert content creator who writes engaging conversational scripts for video content."
            full_prompt = f"{system_prompt}\n\n{prompt}"

            response = await asyncio.to_thread(
                self.text_model.generate_content,
                full_prompt
            )

            script_content = response.text
            word_count = len(script_content.split())
            estimated_duration = (word_count / 150) * 60  # seconds

            return {
                "content": script_content,
                "word_count": word_count,
                "estimated_duration": int(estimated_duration),
                "model_used": self.text_model_name
            }

        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            raise Exception(f"Script generation failed: {e}")

    async def generate_script_from_subject(
        self,
        subject: str,
        min_duration_seconds: int = 180
    ) -> Dict[str, Any]:
        """Generate script from a manual subject input"""
        return await self.generate_script_from_theme(
            theme_name=subject,
            min_duration_seconds=min_duration_seconds
        )

    async def process_manual_script(
        self,
        script_content: str
    ) -> Dict[str, Any]:
        """
        Process a manually provided script and calculate metadata

        Args:
            script_content: The complete script content

        Returns:
            Dictionary with processed script and metadata
        """
        word_count = len(script_content.split())
        estimated_duration = (word_count / 150) * 60  # seconds

        return {
            "content": script_content,
            "word_count": word_count,
            "estimated_duration": int(estimated_duration),
            "model_used": "manual_input"
        }

    async def generate_audio_from_script(
        self,
        script_content: str,
        voice_model: str = "tts-1"
    ) -> Dict[str, Any]:
        """
        Generate conversational audio from script

        Args:
            script_content: The script to convert to audio
            voice_model: The TTS model to use

        Returns:
            Dictionary with audio generation metadata
        """
        try:
            # For now, return metadata about what would be generated
            # In a real implementation, this would call text-to-speech APIs

            lines = [line.strip() for line in script_content.split('\n') if line.strip()]
            speaker_lines = {}

            for line in lines:
                if line.startswith('Speaker 1:'):
                    speaker_lines.setdefault('speaker1', []).append(line[10:].strip())
                elif line.startswith('Speaker 2:'):
                    speaker_lines.setdefault('speaker2', []).append(line[10:].strip())

            return {
                "audio_segments": len(lines),
                "speaker1_lines": len(speaker_lines.get('speaker1', [])),
                "speaker2_lines": len(speaker_lines.get('speaker2', [])),
                "estimated_audio_duration": len(script_content.split()) / 150 * 60,
                "voice_model": voice_model,
                "status": "ready_for_generation"
            }

        except Exception as e:
            logger.error(f"Failed to process audio generation: {e}")
            raise Exception(f"Audio generation failed: {e}")

    async def generate_with_fallback(
        self,
        prompt: str,
        preferred_model: str = None,
        fallback_model: str = None,
        max_retries: int = 3,
        retry_delay_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate content with automatic fallback to secondary model if primary fails

        Args:
            prompt: The generation prompt
            preferred_model: Primary model to try (defaults to image_model)
            fallback_model: Fallback model if primary fails (defaults to "gemini-pro")
            max_retries: Maximum retry attempts per model
            retry_delay_ms: Delay between retries in milliseconds

        Returns:
            Dictionary with generation result and metadata:
            {
                'content': str,
                'model_used': str,
                'fallback_used': bool,
                'generation_time_ms': int,
                'retry_count': int,
                'warnings': List[str]
            }
        """
        # Set defaults
        preferred_model = preferred_model or self.image_model_name
        fallback_model = fallback_model or "gemini-pro"

        start_time = time.time()
        warnings = []

        # First try with preferred model
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempting generation with {preferred_model} (attempt {attempt + 1})")

                model = genai.GenerativeModel(preferred_model)
                response = await asyncio.to_thread(model.generate_content, prompt)

                if response and response.text:
                    generation_time = int((time.time() - start_time) * 1000)
                    logger.info(f"Generation successful with {preferred_model} on attempt {attempt + 1}")

                    return {
                        'content': response.text,
                        'model_used': preferred_model,
                        'fallback_used': False,
                        'generation_time_ms': generation_time,
                        'retry_count': attempt,
                        'warnings': warnings
                    }
                else:
                    warnings.append(f"Empty response from {preferred_model} on attempt {attempt + 1}")

            except GoogleAPIError as e:
                error_msg = str(e)
                warnings.append(f"{preferred_model} attempt {attempt + 1} failed: {error_msg}")
                logger.warning(f"Generation attempt {attempt + 1} with {preferred_model} failed: {error_msg}")

                # Check if we should stop retrying (e.g., model not found)
                if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                    logger.error(f"Model {preferred_model} not found, skipping remaining retries")
                    break

            except Exception as e:
                warnings.append(f"{preferred_model} attempt {attempt + 1} failed: {str(e)}")
                logger.warning(f"Generation attempt {attempt + 1} with {preferred_model} failed: {str(e)}")

            # Wait before retry (except on last attempt)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay_ms / 1000.0)

        # If preferred model failed, try fallback model
        if fallback_model and fallback_model != preferred_model:
            logger.info(f"Primary model {preferred_model} failed, attempting fallback to {fallback_model}")

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempting generation with {fallback_model} (fallback attempt {attempt + 1})")

                    model = genai.GenerativeModel(fallback_model)
                    response = await asyncio.to_thread(model.generate_content, prompt)

                    if response and response.text:
                        generation_time = int((time.time() - start_time) * 1000)
                        logger.info(f"Fallback generation successful with {fallback_model} on attempt {attempt + 1}")

                        warnings.append(f"Used fallback model {fallback_model} after {preferred_model} failed")

                        return {
                            'content': response.text,
                            'model_used': fallback_model,
                            'fallback_used': True,
                            'generation_time_ms': generation_time,
                            'retry_count': max_retries + attempt,  # Total retries across both models
                            'warnings': warnings
                        }
                    else:
                        warnings.append(f"Empty response from {fallback_model} on fallback attempt {attempt + 1}")

                except GoogleAPIError as e:
                    error_msg = str(e)
                    warnings.append(f"{fallback_model} fallback attempt {attempt + 1} failed: {error_msg}")
                    logger.warning(f"Fallback attempt {attempt + 1} with {fallback_model} failed: {error_msg}")

                except Exception as e:
                    warnings.append(f"{fallback_model} fallback attempt {attempt + 1} failed: {str(e)}")
                    logger.warning(f"Fallback attempt {attempt + 1} with {fallback_model} failed: {str(e)}")

                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay_ms / 1000.0)

        # All attempts failed
        generation_time = int((time.time() - start_time) * 1000)
        error_summary = f"All generation attempts failed after {max_retries * (2 if fallback_model else 1)} total attempts"
        logger.error(error_summary)

        raise Exception(f"Generation failed: {error_summary}. Warnings: {'; '.join(warnings)}")

    async def generate_image_with_fallback(
        self,
        prompt: str,
        preferred_model: str = None,
        allow_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a single image with fallback support

        Args:
            prompt: Image generation prompt
            preferred_model: Preferred model (defaults to configured image model)
            allow_fallback: Whether to allow fallback to secondary model

        Returns:
            Dictionary with image generation result and metadata
        """
        preferred_model = preferred_model or self.image_model_name
        fallback_model = "gemini-pro" if allow_fallback else None

        # Enhance prompt for image generation
        enhanced_prompt = f"Generate a high-quality, professional image: {prompt}"

        return await self.generate_with_fallback(
            prompt=enhanced_prompt,
            preferred_model=preferred_model,
            fallback_model=fallback_model
        )

    async def generate_images_for_script(
        self,
        script_content: str,
        num_images: int = 5,
        preferred_model: str = None,
        allow_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate background images based on script content using the configured image model with fallback

        Args:
            script_content: The script to generate images for
            num_images: Number of images to generate
            preferred_model: Preferred model for generation
            allow_fallback: Whether to allow fallback to secondary model

        Returns:
            List of image generation metadata
        """
        try:
            # Extract key topics from script for image prompts
            # This is a simplified version - real implementation would use more sophisticated NLP

            words = script_content.lower().split()
            common_nouns = [word for word in words if len(word) > 4][:num_images]

            images = []
            for i, topic in enumerate(common_nouns):
                prompt = f"Professional background image related to {topic}, suitable for video content"

                # For now, just return metadata - actual generation would use generate_image_with_fallback
                images.append({
                    "prompt": prompt,
                    "image_id": f"img_{i+1}",
                    "estimated_generation_time": 30,  # seconds
                    "dimensions": "1920x1080",
                    "style": "photorealistic",
                    "model_used": preferred_model or self.image_model_name,
                    "fallback_enabled": allow_fallback
                })

            return images

        except Exception as e:
            logger.error(f"Failed to generate image prompts: {e}")
            raise Exception(f"Image generation failed: {e}")

    async def generate_video_clips(
        self,
        script_content: str,
        num_clips: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate short video clips for background

        Args:
            script_content: The script to generate clips for
            num_clips: Number of video clips to generate

        Returns:
            List of video generation metadata
        """
        try:
            # For now, return metadata about what clips would be generated
            clips = []
            for i in range(num_clips):
                clips.append({
                    "clip_id": f"clip_{i+1}",
                    "duration": 10,  # seconds
                    "prompt": f"Background video clip {i+1} for script content",
                    "resolution": "1920x1080",
                    "format": "mp4",
                    "estimated_generation_time": 120,  # seconds
                    "model_used": self.text_model_name  # Using text model for video prompt generation
                })

            return clips

        except Exception as e:
            logger.error(f"Failed to generate video clips: {e}")
            raise Exception(f"Video clip generation failed: {e}")