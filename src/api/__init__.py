"""API module for external service integrations."""

from src.api.transcription_service import TranscriptionService, TranscriptionResult

__all__ = ["TranscriptionService", "TranscriptionResult"]
