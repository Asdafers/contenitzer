from typing import Dict, Any, List, Optional
import logging
import asyncio
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini APIs for content generation"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

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
                self.model.generate_content,
                full_prompt
            )

            script_content = response.text
            word_count = len(script_content.split())
            estimated_duration = (word_count / 150) * 60  # seconds

            return {
                "content": script_content,
                "word_count": word_count,
                "estimated_duration": int(estimated_duration),
                "model_used": "gemini-pro"
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

    async def generate_images_for_script(
        self,
        script_content: str,
        num_images: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate background images based on script content

        Args:
            script_content: The script to generate images for
            num_images: Number of images to generate

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
                images.append({
                    "prompt": f"Professional background image related to {topic}, suitable for video content",
                    "image_id": f"img_{i+1}",
                    "estimated_generation_time": 30,  # seconds
                    "dimensions": "1920x1080",
                    "style": "photorealistic"
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
                    "estimated_generation_time": 120  # seconds
                })

            return clips

        except Exception as e:
            logger.error(f"Failed to generate video clips: {e}")
            raise Exception(f"Video clip generation failed: {e}")