import pytest
from unittest.mock import Mock, AsyncMock
import uuid

from src.services.script_service import ScriptService
from src.models.video_script import VideoScript, InputSourceEnum, FormatTypeEnum


class TestScriptService:
    """Unit tests for Script service"""

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        return db

    @pytest.fixture
    def mock_gemini_service(self):
        service = Mock()
        service.generate_script_from_theme = AsyncMock(return_value={
            "content": "Speaker 1: Test content\nSpeaker 2: Response content",
            "estimated_duration": 200,
            "word_count": 50,
            "model_used": "gpt-3.5-turbo"
        })
        service.generate_script_from_subject = AsyncMock(return_value={
            "content": "Speaker 1: Subject content\nSpeaker 2: Subject response",
            "estimated_duration": 220,
            "word_count": 55,
            "model_used": "gpt-3.5-turbo"
        })
        service.process_manual_script = AsyncMock(return_value={
            "content": "Manual script content",
            "estimated_duration": 180,
            "word_count": 45,
            "model_used": "manual_input"
        })
        return service

    @pytest.fixture
    def script_service(self, mock_db, mock_gemini_service):
        return ScriptService(db=mock_db, gemini_service=mock_gemini_service)

    async def test_generate_from_theme(self, script_service, mock_db, mock_gemini_service):
        """Test script generation from theme"""
        theme_id = str(uuid.uuid4())
        theme_name = "Test Theme"
        theme_description = "Test description"

        result = await script_service.generate_from_theme(
            theme_id=theme_id,
            theme_name=theme_name,
            theme_description=theme_description
        )

        # Verify Gemini service was called
        mock_gemini_service.generate_script_from_theme.assert_called_once_with(
            theme_name=theme_name,
            theme_description=theme_description,
            min_duration_seconds=180
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify script properties
        script_call_args = mock_db.add.call_args[0][0]
        assert isinstance(script_call_args, VideoScript)
        assert script_call_args.input_source == InputSourceEnum.generated
        assert script_call_args.format_type == FormatTypeEnum.conversational
        assert script_call_args.speaker_count == 2

    async def test_generate_from_manual_subject(self, script_service, mock_db, mock_gemini_service):
        """Test script generation from manual subject"""
        subject = "Test subject for script generation"

        result = await script_service.generate_from_manual_subject(subject=subject)

        # Verify Gemini service was called
        mock_gemini_service.generate_script_from_subject.assert_called_once_with(
            subject=subject,
            min_duration_seconds=180
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify script properties
        script_call_args = mock_db.add.call_args[0][0]
        assert script_call_args.input_source == InputSourceEnum.manual_subject
        assert script_call_args.manual_input == subject
        assert script_call_args.theme_id is None

    async def test_process_manual_script(self, script_service, mock_db, mock_gemini_service):
        """Test processing of complete manual script"""
        script_content = """
Speaker 1: This is a complete manual script.
Speaker 2: It should be processed without generation.
Speaker 1: The duration should be calculated correctly.
Speaker 2: And it should be stored with the right properties.
        """.strip()

        result = await script_service.process_manual_script(script_content=script_content)

        # Verify Gemini service was called
        mock_gemini_service.process_manual_script.assert_called_once_with(script_content)

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify script properties
        script_call_args = mock_db.add.call_args[0][0]
        assert script_call_args.input_source == InputSourceEnum.manual_script
        assert script_call_args.manual_input == script_content
        assert script_call_args.content == script_content

    async def test_process_manual_script_too_short(self, script_service, mock_gemini_service):
        """Test handling of manual script that's too short"""
        # Mock service to return script that's too short
        mock_gemini_service.process_manual_script.return_value = {
            "content": "Short script",
            "estimated_duration": 120,  # Less than 180 seconds
            "word_count": 20,
            "model_used": "manual_input"
        }

        short_script = "Speaker 1: Too short. Speaker 2: Yes, very short."

        with pytest.raises(ValueError) as exc_info:
            await script_service.process_manual_script(script_content=short_script)

        assert "Script too short" in str(exc_info.value)

    def test_get_script_by_id(self, script_service, mock_db):
        """Test getting script by ID"""
        script_id = str(uuid.uuid4())
        mock_script = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_script

        result = script_service.get_script_by_id(script_id)

        assert result == mock_script
        mock_db.query.assert_called_once()

    def test_get_script_by_id_not_found(self, script_service, mock_db):
        """Test getting script by ID when not found"""
        script_id = str(uuid.uuid4())
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = script_service.get_script_by_id(script_id)

        assert result is None

    def test_validate_script_duration(self, script_service):
        """Test script duration validation"""
        # Create mock scripts with different durations
        valid_script = Mock()
        valid_script.estimated_duration = 200

        invalid_script = Mock()
        invalid_script.estimated_duration = 120

        assert script_service.validate_script_duration(valid_script) is True
        assert script_service.validate_script_duration(invalid_script) is False

    async def test_error_handling_with_rollback(self, script_service, mock_db, mock_gemini_service):
        """Test error handling with database rollback"""
        # Mock Gemini service to raise an exception
        mock_gemini_service.generate_script_from_theme.side_effect = Exception("Generation failed")

        theme_id = str(uuid.uuid4())

        with pytest.raises(Exception):
            await script_service.generate_from_theme(
                theme_id=theme_id,
                theme_name="Test Theme",
                theme_description="Test description"
            )

        # Verify rollback was called
        mock_db.rollback.assert_called_once()