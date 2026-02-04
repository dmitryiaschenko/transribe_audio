"""Tests for the transcription service module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.api.transcription_service import (
    TranscriptionService,
    TranscriptionResult,
    TranscriptionError,
)
from google.genai.errors import ServerError

from src.config import ConversationType, GEMINI_FALLBACK_MODEL


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_creation(self):
        """Should create result with all fields."""
        result = TranscriptionResult(
            text="Test transcription",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            input_cost=0.0001,
            output_cost=0.0002,
            total_cost=0.0003,
        )

        assert result.text == "Test transcription"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
        assert result.total_cost == 0.0003

    def test_formatted_stats(self):
        """Should format stats string correctly."""
        result = TranscriptionResult(
            text="Test",
            input_tokens=12345,
            output_tokens=2456,
            total_tokens=14801,
            input_cost=0.006,
            output_cost=0.007,
            total_cost=0.013,
        )

        stats = result.formatted_stats
        assert "12,345" in stats
        assert "2,456" in stats
        assert "$0.0130" in stats


class TestTranscriptionService:
    """Tests for TranscriptionService class."""

    def test_init_without_api_key(self, monkeypatch):
        """Should create service without immediate error when no API key."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        # Service can be created, but initialization will fail
        service = TranscriptionService(api_key=None)
        assert not service.is_initialized

    def test_init_with_api_key(self):
        """Should create service with provided API key."""
        service = TranscriptionService(api_key="test-key")
        assert not service.is_initialized  # Not initialized until initialize() called

    def test_initialize_without_api_key_raises(self, monkeypatch):
        """Should raise error when initializing without API key."""
        # Must patch both the env var and the already-loaded config constant
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setattr("src.api.transcription_service.GEMINI_API_KEY", None)

        service = TranscriptionService(api_key=None)

        with pytest.raises(TranscriptionError, match="API key not found"):
            service.initialize()

    @patch("src.api.transcription_service.genai")
    def test_initialize_success(self, mock_genai):
        """Should initialize successfully with valid API key."""
        service = TranscriptionService(api_key="test-key")
        service.initialize()

        assert service.is_initialized
        mock_genai.Client.assert_called_once_with(api_key="test-key")

    @patch("src.api.transcription_service.genai")
    def test_initialize_idempotent(self, mock_genai):
        """Should not reinitialize if already initialized."""
        service = TranscriptionService(api_key="test-key")

        service.initialize()
        service.initialize()  # Second call

        # Should only configure once
        assert mock_genai.Client.call_count == 1

    def test_validate_file_not_found(self):
        """Should raise error for non-existent file."""
        service = TranscriptionService(api_key="test-key")

        with pytest.raises(TranscriptionError, match="File not found"):
            service.validate_file("/non/existent/file.mp3")

    def test_validate_file_invalid_extension(self, temp_invalid_file):
        """Should raise error for unsupported file extension."""
        service = TranscriptionService(api_key="test-key")

        with pytest.raises(TranscriptionError, match="Unsupported file format"):
            service.validate_file(temp_invalid_file)

    def test_validate_file_success(self, temp_audio_file):
        """Should return Path for valid audio file."""
        service = TranscriptionService(api_key="test-key")

        result = service.validate_file(temp_audio_file)

        assert isinstance(result, Path)
        assert result.exists()

    @patch("src.api.transcription_service.genai")
    def test_transcribe_initializes_if_needed(self, mock_genai, temp_audio_file):
        """Should auto-initialize when transcribe is called."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Transcribed text"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        service = TranscriptionService(api_key="test-key")
        assert not service.is_initialized

        result = service.transcribe(
            file_path=temp_audio_file,
            language="English",
            conversation_type=ConversationType.INTERVIEW,
        )

        assert service.is_initialized
        assert result.text == "Transcribed text"

    @patch("src.api.transcription_service.genai")
    def test_transcribe_returns_result(self, mock_genai, temp_audio_file):
        """Should return TranscriptionResult with correct data."""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Meeting notes here"
        mock_response.usage_metadata.prompt_token_count = 500
        mock_response.usage_metadata.candidates_token_count = 200
        mock_response.usage_metadata.total_token_count = 700
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        service = TranscriptionService(api_key="test-key")
        result = service.transcribe(
            file_path=temp_audio_file,
            language="Russian",
            conversation_type=ConversationType.BUSINESS_MEETING,
        )

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Meeting notes here"
        assert result.input_tokens == 500
        assert result.output_tokens == 200
        assert result.total_tokens == 700
        assert result.total_cost > 0

    @patch("src.api.transcription_service.genai")
    def test_transcribe_handles_api_error(self, mock_genai, temp_audio_file):
        """Should wrap API errors in TranscriptionError."""
        mock_client = MagicMock()
        mock_client.files.upload.side_effect = Exception("API connection failed")
        mock_genai.Client.return_value = mock_client

        service = TranscriptionService(api_key="test-key")
        service.initialize()

        with pytest.raises(TranscriptionError, match="Transcription failed"):
            service.transcribe(
                file_path=temp_audio_file,
                language="English",
                conversation_type=ConversationType.INTERVIEW,
            )

    @patch("src.api.transcription_service.genai")
    def test_transcribe_with_missing_usage_metadata(self, mock_genai, temp_audio_file):
        """Should handle response without usage_metadata."""
        mock_model = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"
        mock_candidate.content.parts = [MagicMock()]
        mock_response = MagicMock(spec=["text", "candidates"])
        mock_response.text = "Transcription"
        mock_response.candidates = [mock_candidate]
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        service = TranscriptionService(api_key="test-key")
        result = service.transcribe(
            file_path=temp_audio_file,
            language="Polish",
            conversation_type=ConversationType.INTERVIEW,
        )

        # Should default to 0 tokens
        assert result.input_tokens == 0
        assert result.output_tokens == 0
        assert result.total_cost == 0.0

    @patch("src.api.transcription_service.genai")
    def test_transcribe_fallback_on_503(self, mock_genai, temp_audio_file):
        """Should fall back to GEMINI_FALLBACK_MODEL when primary model returns 503."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # First call raises 503, second call succeeds
        mock_response = MagicMock()
        mock_response.text = "Fallback transcription"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150

        mock_client.models.generate_content.side_effect = [
            ServerError(503, {"error": {"message": "model overloaded"}}),
            mock_response,
        ]

        service = TranscriptionService(api_key="test-key")
        result = service.transcribe(
            file_path=temp_audio_file,
            language="English",
            conversation_type=ConversationType.INTERVIEW,
        )

        assert result.text == "Fallback transcription"

        # Verify the second call used the fallback model
        calls = mock_client.models.generate_content.call_args_list
        assert len(calls) == 2
        assert calls[1].kwargs["model"] == GEMINI_FALLBACK_MODEL

    @patch("src.api.transcription_service.genai")
    def test_transcribe_reraises_non_503_server_error(self, mock_genai, temp_audio_file):
        """Should re-raise ServerError for non-503 status codes."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        mock_client.models.generate_content.side_effect = ServerError(500, {"error": {"message": "internal error"}})

        service = TranscriptionService(api_key="test-key")

        with pytest.raises(TranscriptionError, match="Transcription failed"):
            service.transcribe(
                file_path=temp_audio_file,
                language="English",
                conversation_type=ConversationType.INTERVIEW,
            )
