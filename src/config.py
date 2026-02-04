"""Configuration settings and constants for the transcription app."""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"

# Web server configuration
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

CORS_ORIGINS: List[str] = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]


@dataclass(frozen=True)
class Pricing:
    input_cost_per_1m: float = 0.50
    output_cost_per_1m: float = 3.00


LANGUAGES: Dict[str, str] = {
    "English": "English",
    "Russian": "Russian",
    "Polish": "Polish",
}


@dataclass(frozen=True)
class ConversationType:
    INTERVIEW: str = "Interview"
    BUSINESS_MEETING: str = "Business Meeting"


CONVERSATION_TYPES: List[str] = [
    ConversationType.INTERVIEW,
    ConversationType.BUSINESS_MEETING,
]

SUPPORTED_EXTENSIONS: Tuple[str, ...] = (".m4a", ".mp3", ".wav", ".aac")


@dataclass(frozen=True)
class GUIConfig:
    window_title: str = "Audio Transcription App"
    window_width: int = 700
    window_height: int = 750
    min_width: int = 600
    min_height: int = 650
    appearance_mode: str = "dark"
    color_theme: str = "blue"


PROMPT_TEMPLATES: Dict[str, str] = {
    ConversationType.INTERVIEW: """Transcribe this audio in {language} and provide interview analysis.

Format:
1. TRANSCRIPTION: [full transcription]
2. OVERALL ASSESSMENT: [rating and summary]
3. STRENGTHS: [bullet points]
4. WEAKNESSES: [bullet points]
5. RECOMMENDATIONS: [specific advice]""",

    ConversationType.BUSINESS_MEETING: """Transcribe this audio in {language} and provide business meeting summary.

Format:
1. TRANSCRIPTION: [full transcription]
2. SUMMARY: [key points discussed]
3. ACTION ITEMS: [list of tasks/decisions with responsible parties if mentioned]
4. NEXT STEPS: [follow-up actions]""",
}


def get_prompt(conversation_type: str, language: str) -> str:
    """Get the prompt template for the given conversation type and language."""
    template = PROMPT_TEMPLATES.get(conversation_type)
    if not template:
        raise ValueError(f"Unknown conversation type: {conversation_type}")
    return template.format(language=language)


def calculate_cost(input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """Calculate the cost based on token usage."""
    pricing = Pricing()
    input_cost = (input_tokens / 1_000_000) * pricing.input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * pricing.output_cost_per_1m
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }
