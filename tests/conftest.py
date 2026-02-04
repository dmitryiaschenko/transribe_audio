"""Pytest fixtures and configuration."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_audio_file():
    """Create a temporary file with an audio extension for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio content")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_invalid_file():
    """Create a temporary file with an invalid extension."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not an audio file")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_api_key(monkeypatch):
    """Set a mock API key for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-12345")
    return "test-api-key-12345"
