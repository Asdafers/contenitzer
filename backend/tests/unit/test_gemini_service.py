import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.services.gemini_service import GeminiService


class TestGeminiService:
    """Unit tests for Gemini service"""

    @pytest.fixture
    def gemini_service(self):
        return GeminiService(api_key="test-api-key")

    @pytest.fixture
    def mock_openai_response(self):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
Speaker 1: Welcome to our discussion about artificial intelligence and its impact on society.
Speaker 2: Thank you for having me. AI is indeed transforming how we work and live.
Speaker 1: Let's explore the benefits first. What are some positive impacts you've observed?
Speaker 2: AI has revolutionized healthcare with faster diagnosis and personalized treatments.
Speaker 1: That's fascinating. What about challenges we need to address?
Speaker 2: Privacy concerns and job displacement are significant issues we must tackle thoughtfully.
Speaker 1: How can we ensure AI development remains ethical and beneficial for everyone?
Speaker 2: Through collaboration between technologists, policymakers, and civil society.
Speaker 1: Excellent points. Thank you for this insightful conversation about AI's future.
Speaker 2: My pleasure. It's crucial we continue these important discussions.
        """.strip()
        return mock_response

    @patch('asyncio.to_thread')
    async def test_generate_script_from_theme(self, mock_to_thread, gemini_service, mock_openai_response):
        """Test script generation from theme"""
        mock_to_thread.return_value = mock_openai_response

        result = await gemini_service.generate_script_from_theme(
            theme_name="Artificial Intelligence",
            theme_description="Impact on society",
            min_duration_seconds=180
        )

        assert isinstance(result, dict)
        assert 'content' in result
        assert 'word_count' in result
        assert 'estimated_duration' in result
        assert 'model_used' in result

        assert result['estimated_duration'] >= 180
        assert result['word_count'] > 0
        assert result['model_used'] == 'gpt-3.5-turbo'
        assert 'Speaker 1:' in result['content']
        assert 'Speaker 2:' in result['content']

    @patch('asyncio.to_thread')
    async def test_generate_script_from_subject(self, mock_to_thread, gemini_service, mock_openai_response):
        """Test script generation from manual subject"""
        mock_to_thread.return_value = mock_openai_response

        result = await gemini_service.generate_script_from_subject(
            subject="Climate Change Solutions",
            min_duration_seconds=200
        )

        assert isinstance(result, dict)
        assert result['estimated_duration'] >= 200
        assert 'content' in result

    async def test_process_manual_script(self, gemini_service):
        """Test processing of manual script"""
        manual_script = """
Speaker 1: Hello and welcome to our show today.
Speaker 2: Thank you for having me on the program.
Speaker 1: Let's discuss renewable energy and its future prospects.
Speaker 2: Renewable energy is crucial for sustainable development and climate goals.
Speaker 1: What are the main challenges in renewable energy adoption?
Speaker 2: Cost, infrastructure, and energy storage remain significant hurdles.
Speaker 1: How can governments support this transition effectively?
Speaker 2: Through policy incentives, research funding, and infrastructure investment.
Speaker 1: Thank you for sharing these valuable insights with our audience.
Speaker 2: It was my pleasure to discuss this important topic.
        """.strip()

        result = await gemini_service.process_manual_script(manual_script)

        assert isinstance(result, dict)
        assert result['content'] == manual_script
        assert result['word_count'] > 0
        assert result['estimated_duration'] > 0
        assert result['model_used'] == 'manual_input'

        # Check duration calculation
        expected_duration = (result['word_count'] / 150) * 60
        assert abs(result['estimated_duration'] - expected_duration) < 1

    async def test_generate_audio_from_script(self, gemini_service):
        """Test audio generation metadata"""
        script_content = """
Speaker 1: This is a test script.
Speaker 2: Yes, it contains dialogue between two speakers.
Speaker 1: We can analyze the structure.
Speaker 2: And estimate audio generation parameters.
        """.strip()

        result = await gemini_service.generate_audio_from_script(script_content)

        assert isinstance(result, dict)
        assert 'audio_segments' in result
        assert 'speaker1_lines' in result
        assert 'speaker2_lines' in result
        assert 'estimated_audio_duration' in result
        assert 'voice_model' in result
        assert 'status' in result

        assert result['speaker1_lines'] == 2
        assert result['speaker2_lines'] == 2
        assert result['status'] == 'ready_for_generation'

    async def test_generate_images_for_script(self, gemini_service):
        """Test image generation prompts"""
        script_content = """
Speaker 1: Today we discuss technology and innovation in the digital world.
Speaker 2: Artificial intelligence and machine learning are transforming industries.
Speaker 1: Cloud computing enables global collaboration and data processing.
Speaker 2: Cybersecurity remains critical for protecting digital infrastructure.
        """

        result = await gemini_service.generate_images_for_script(
            script_content=script_content,
            num_images=3
        )

        assert isinstance(result, list)
        assert len(result) == 3

        for image_data in result:
            assert 'prompt' in image_data
            assert 'image_id' in image_data
            assert 'estimated_generation_time' in image_data
            assert 'dimensions' in image_data
            assert 'style' in image_data

    async def test_generate_video_clips(self, gemini_service):
        """Test video clip generation metadata"""
        script_content = "Test script for video generation"

        result = await gemini_service.generate_video_clips(
            script_content=script_content,
            num_clips=2
        )

        assert isinstance(result, list)
        assert len(result) == 2

        for clip_data in result:
            assert 'clip_id' in clip_data
            assert 'duration' in clip_data
            assert 'prompt' in clip_data
            assert 'resolution' in clip_data
            assert 'format' in clip_data
            assert 'estimated_generation_time' in clip_data

    @patch('asyncio.to_thread')
    async def test_script_generation_error_handling(self, mock_to_thread, gemini_service):
        """Test error handling in script generation"""
        mock_to_thread.side_effect = Exception("API Error")

        with pytest.raises(Exception) as exc_info:
            await gemini_service.generate_script_from_theme(
                theme_name="Test Theme",
                min_duration_seconds=180
            )

        assert "Script generation failed" in str(exc_info.value)