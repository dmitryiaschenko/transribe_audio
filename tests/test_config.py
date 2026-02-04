"""Tests for the configuration module."""

import pytest
from src.config import (
    LANGUAGES,
    CONVERSATION_TYPES,
    SUPPORTED_EXTENSIONS,
    ConversationType,
    GUIConfig,
    Pricing,
    get_prompt,
    calculate_cost,
)


class TestLanguages:
    """Tests for language configuration."""

    def test_languages_not_empty(self):
        """Languages dict should not be empty."""
        assert len(LANGUAGES) > 0

    def test_english_available(self):
        """English should be available."""
        assert "English" in LANGUAGES

    def test_russian_available(self):
        """Russian should be available."""
        assert "Russian" in LANGUAGES

    def test_polish_available(self):
        """Polish should be available."""
        assert "Polish" in LANGUAGES


class TestConversationTypes:
    """Tests for conversation type configuration."""

    def test_types_not_empty(self):
        """Conversation types list should not be empty."""
        assert len(CONVERSATION_TYPES) > 0

    def test_interview_type_exists(self):
        """Interview type should be available."""
        assert ConversationType.INTERVIEW in CONVERSATION_TYPES

    def test_business_meeting_type_exists(self):
        """Business meeting type should be available."""
        assert ConversationType.BUSINESS_MEETING in CONVERSATION_TYPES


class TestSupportedExtensions:
    """Tests for supported file extensions."""

    def test_extensions_not_empty(self):
        """Supported extensions should not be empty."""
        assert len(SUPPORTED_EXTENSIONS) > 0

    def test_m4a_supported(self):
        """M4A format should be supported."""
        assert ".m4a" in SUPPORTED_EXTENSIONS

    def test_mp3_supported(self):
        """MP3 format should be supported."""
        assert ".mp3" in SUPPORTED_EXTENSIONS

    def test_wav_supported(self):
        """WAV format should be supported."""
        assert ".wav" in SUPPORTED_EXTENSIONS

    def test_aac_supported(self):
        """AAC format should be supported."""
        assert ".aac" in SUPPORTED_EXTENSIONS

    def test_all_extensions_start_with_dot(self):
        """All extensions should start with a dot."""
        for ext in SUPPORTED_EXTENSIONS:
            assert ext.startswith(".")


class TestGUIConfig:
    """Tests for GUI configuration."""

    def test_default_values(self):
        """GUIConfig should have sensible default values."""
        config = GUIConfig()

        assert config.window_width > 0
        assert config.window_height > 0
        assert config.min_width > 0
        assert config.min_height > 0
        assert config.min_width <= config.window_width
        assert config.min_height <= config.window_height
        assert config.window_title != ""
        assert config.appearance_mode in ("dark", "light", "system")

    def test_immutable(self):
        """GUIConfig should be immutable (frozen dataclass)."""
        config = GUIConfig()
        with pytest.raises(AttributeError):
            config.window_width = 1000


class TestPricing:
    """Tests for pricing configuration."""

    def test_pricing_values_positive(self):
        """Pricing values should be positive."""
        pricing = Pricing()
        assert pricing.input_cost_per_1m > 0
        assert pricing.output_cost_per_1m > 0

    def test_immutable(self):
        """Pricing should be immutable (frozen dataclass)."""
        pricing = Pricing()
        with pytest.raises(AttributeError):
            pricing.input_cost_per_1m = 100.0


class TestGetPrompt:
    """Tests for the get_prompt function."""

    def test_interview_prompt(self):
        """Should generate interview prompt with language."""
        prompt = get_prompt(ConversationType.INTERVIEW, "English")

        assert "English" in prompt
        assert "TRANSCRIPTION" in prompt
        assert "ASSESSMENT" in prompt
        assert "STRENGTHS" in prompt
        assert "WEAKNESSES" in prompt
        assert "RECOMMENDATIONS" in prompt

    def test_business_meeting_prompt(self):
        """Should generate business meeting prompt with language."""
        prompt = get_prompt(ConversationType.BUSINESS_MEETING, "Russian")

        assert "Russian" in prompt
        assert "TRANSCRIPTION" in prompt
        assert "SUMMARY" in prompt
        assert "ACTION ITEMS" in prompt
        assert "NEXT STEPS" in prompt

    def test_invalid_conversation_type(self):
        """Should raise error for invalid conversation type."""
        with pytest.raises(ValueError, match="Unknown conversation type"):
            get_prompt("InvalidType", "English")


class TestCalculateCost:
    """Tests for the calculate_cost function."""

    def test_zero_tokens(self):
        """Should handle zero tokens."""
        result = calculate_cost(0, 0)

        assert result["input_cost"] == 0.0
        assert result["output_cost"] == 0.0
        assert result["total_cost"] == 0.0

    def test_positive_tokens(self):
        """Should calculate cost for positive token counts."""
        result = calculate_cost(1_000_000, 1_000_000)

        assert result["input_cost"] > 0
        assert result["output_cost"] > 0
        assert result["total_cost"] == result["input_cost"] + result["output_cost"]

    def test_cost_increases_with_tokens(self):
        """Cost should increase with more tokens."""
        result_small = calculate_cost(100, 100)
        result_large = calculate_cost(10000, 10000)

        assert result_large["total_cost"] > result_small["total_cost"]

    def test_returns_all_keys(self):
        """Should return dict with all expected keys."""
        result = calculate_cost(1000, 500)

        assert "input_cost" in result
        assert "output_cost" in result
        assert "total_cost" in result
