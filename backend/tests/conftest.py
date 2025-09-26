"""
Test configuration for AI-powered media generation.
Provides fixtures for Gemini API mocking and test setup.
"""
import pytest
from unittest.mock import Mock, patch
import google.generativeai as genai
from typing import Dict, Any, List


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client for testing without API calls."""
    with patch('google.generativeai.configure') as mock_configure:
        # Mock the model generation
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated test content"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content.parts = [Mock()]
        mock_response.candidates[0].content.parts[0].text = "Generated test content"

        mock_model.generate_content.return_value = mock_response

        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model_class.return_value = mock_model
            yield {
                'configure': mock_configure,
                'model': mock_model,
                'response': mock_response
            }


@pytest.fixture
def mock_gemini_image_generation():
    """Mock Gemini image generation responses."""
    mock_response = Mock()
    mock_response.text = '{"image_description": "A vibrant cityscape with neon lights", "style": "digital art", "confidence": 0.95}'
    return mock_response


@pytest.fixture
def mock_gemini_script_analysis():
    """Mock Gemini script analysis responses."""
    mock_response = Mock()
    mock_response.text = '''
    {
        "scenes": [
            {
                "index": 0,
                "text": "Welcome to the future of content creation",
                "visual_themes": ["technology", "futuristic"],
                "image_prompt": "Futuristic digital workspace with holographic displays"
            },
            {
                "index": 1,
                "text": "vibrant cityscapes with glowing neon lights",
                "visual_themes": ["urban", "cyberpunk"],
                "image_prompt": "Cyberpunk cityscape with neon lights reflecting off glass towers"
            }
        ],
        "overall_theme": "technological future",
        "estimated_scenes": 2
    }
    '''
    return mock_response


@pytest.fixture
def mock_gemini_error_response():
    """Mock Gemini API error responses for testing error handling."""
    def create_error(error_type: str, message: str = "Test error"):
        error = Exception(message)
        error.error_type = error_type
        return error

    return {
        'rate_limit': create_error('RATE_LIMIT_EXCEEDED', 'Rate limit exceeded'),
        'content_filter': create_error('CONTENT_FILTER', 'Content filtered by safety policy'),
        'api_error': create_error('API_ERROR', 'API temporarily unavailable'),
        'invalid_request': create_error('INVALID_REQUEST', 'Invalid request parameters')
    }


@pytest.fixture
def gemini_test_config():
    """Test configuration for Gemini API integration."""
    return {
        'model_name': 'gemini-2.5-flash',
        'generation_config': {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 1024,
        },
        'safety_settings': [
            {
                'category': 'HARM_CATEGORY_HATE_SPEECH',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
            },
            {
                'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                'threshold': 'BLOCK_MEDIUM_AND_ABOVE'
            }
        ]
    }


@pytest.fixture
def sample_script_content():
    """Sample script content for testing AI processing."""
    return """
    Welcome to the future of content creation. In this digital age, technology transforms
    how we tell stories. Imagine vibrant cityscapes with glowing neon lights reflecting
    off glass towers. Picture innovative workspace environments where creativity flows
    freely, with modern design elements and collaborative spaces.

    The journey continues through serene natural landscapes - mountain vistas at sunrise,
    peaceful forest paths, and crystal-clear lakes reflecting the sky. These environments
    inspire the next generation of digital storytellers.
    """


@pytest.fixture
def ai_processing_stages():
    """Expected AI processing stages for progress tracking tests."""
    return [
        'analyzing_script',
        'generating_prompts',
        'creating_images',
        'processing_audio',
        'completed'
    ]


@pytest.fixture
def expected_media_assets():
    """Expected structure for AI-generated media assets."""
    return {
        'background_images': [
            {
                'id': 'test-image-1',
                'asset_type': 'IMAGE',
                'generation_method': 'GEMINI_AI',
                'ai_model_used': 'gemini-2.5-flash',
                'generation_prompt': 'Cyberpunk cityscape with neon lights'
            }
        ],
        'audio_tracks': [
            {
                'id': 'test-audio-1',
                'asset_type': 'AUDIO',
                'generation_method': 'GEMINI_AI',
                'ai_model_used': 'gemini-2.5-flash'
            }
        ]
    }