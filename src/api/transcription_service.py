"""Transcription service using Google's Gemini AI."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from google import genai
from google.genai.errors import ServerError

from src.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
    SUPPORTED_EXTENSIONS,
    get_prompt,
    calculate_cost,
)
from src.logger import logger


class TranscriptionError(Exception):
    """Custom exception for transcription-related errors."""
    pass


@dataclass
class TranscriptionResult:
    """Container for transcription results."""
    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float

    @property
    def formatted_stats(self) -> str:
        """Return formatted token and cost statistics."""
        return (
            f"Tokens: {self.input_tokens:,} input / {self.output_tokens:,} output | "
            f"Cost: ${self.total_cost:.4f}"
        )


class TranscriptionService:
    """Service for handling audio transcription via Gemini AI."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or GEMINI_API_KEY
        self._client = None
        self._initialized = False
        logger.debug("TranscriptionService created")

    def initialize(self) -> None:
        """Initialize the Gemini API client."""
        if self._initialized:
            logger.debug("Service already initialized")
            return

        if not self._api_key:
            logger.error("No API key provided")
            raise TranscriptionError(
                "API key not found. Please set GEMINI_API_KEY in .env file."
            )

        try:
            logger.info("Initializing Gemini API client")
            self._client = genai.Client(api_key=self._api_key)
            self._initialized = True
            logger.info(f"Gemini model '{GEMINI_MODEL}' initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize Gemini API")
            raise TranscriptionError(f"Failed to initialize Gemini API: {e}")

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    def validate_file(self, file_path: str) -> Path:
        """Validate the audio file and return Path if valid."""
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise TranscriptionError(f"File not found: {file_path}")

        if not path.is_file():
            logger.error(f"Not a file: {file_path}")
            raise TranscriptionError(f"Not a file: {file_path}")

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file format: {path.suffix}")
            raise TranscriptionError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        logger.debug(f"File validated: {file_path}")
        return path

    def _extract_response_text(self, response) -> str:
        """Extract text from response with proper error handling."""
        if not response.candidates:
            logger.error("No candidates in response")
            raise TranscriptionError(
                "The API returned no response. The audio file may be too short, "
                "corrupted, or contain no recognizable speech."
            )

        candidate = response.candidates[0]

        if hasattr(candidate, "finish_reason"):
            finish_reason = candidate.finish_reason
            logger.debug(f"Response finish_reason: {finish_reason}")

            if finish_reason == "SAFETY":
                safety_ratings = getattr(candidate, "safety_ratings", [])
                logger.warning(f"Content blocked by safety filters: {safety_ratings}")
                raise TranscriptionError(
                    "The content was blocked by safety filters. "
                    "The audio may contain sensitive content."
                )
            elif finish_reason == "MAX_TOKENS":
                logger.warning("Response truncated due to max tokens")
            elif finish_reason == "RECITATION":
                logger.warning("Response blocked due to recitation")
                raise TranscriptionError(
                    "The response was blocked due to potential copyright issues."
                )

        if not hasattr(candidate, "content") or not candidate.content.parts:
            logger.error("Response has no content parts")
            raise TranscriptionError(
                "The API returned an empty response. Please try again or use a different audio file."
            )

        try:
            return response.text
        except ValueError as e:
            logger.error(f"Failed to extract text: {e}")
            raise TranscriptionError(
                "Failed to extract transcription from response. "
                "The audio file may not contain recognizable speech."
            )

    def transcribe(
        self,
        file_path: str,
        language: str,
        conversation_type: str,
    ) -> TranscriptionResult:
        """Transcribe an audio file and return results with usage statistics."""
        if not self._initialized:
            self.initialize()

        path = self.validate_file(file_path)
        logger.info(f"Starting transcription: {path.name}")
        logger.debug(f"Language: {language}, Type: {conversation_type}")

        try:
            logger.debug("Uploading file to Gemini")
            audio_file = self._client.files.upload(file=str(path))
            logger.debug("File uploaded successfully")

            while audio_file.state == "PROCESSING":
                logger.debug("File still processing, waiting...")
                time.sleep(2)
                audio_file = self._client.files.get(name=audio_file.name)

            if audio_file.state == "FAILED":
                raise TranscriptionError("File processing failed on Google's servers.")

            logger.debug(f"File ready, state: {audio_file.state}")

            prompt = get_prompt(conversation_type, language)
            logger.debug(f"Generated prompt for {conversation_type}")

            logger.info("Generating transcription...")
            contents = [prompt, audio_file]
            try:
                response = self._client.models.generate_content(model=GEMINI_MODEL, contents=contents)
            except ServerError as e:
                if e.code != 503:
                    raise
                logger.warning(
                    f"Primary model {GEMINI_MODEL} overloaded (503), falling back to {GEMINI_FALLBACK_MODEL}"
                )
                response = self._client.models.generate_content(model=GEMINI_FALLBACK_MODEL, contents=contents)
            logger.info("Transcription completed")

            response_text = self._extract_response_text(response)

            input_tokens = 0
            output_tokens = 0
            total_tokens = 0

            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                total_tokens = usage.total_token_count
                logger.debug(
                    f"Token usage - Input: {input_tokens}, "
                    f"Output: {output_tokens}, Total: {total_tokens}"
                )

            costs = calculate_cost(input_tokens, output_tokens)
            logger.debug(f"Cost calculated: ${costs['total_cost']:.4f}")

            result = TranscriptionResult(
                text=response_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=costs["input_cost"],
                output_cost=costs["output_cost"],
                total_cost=costs["total_cost"],
            )

            logger.info(f"Transcription successful: {result.formatted_stats}")
            return result

        except TranscriptionError:
            raise
        except Exception as e:
            logger.exception("Transcription failed")
            raise TranscriptionError(f"Transcription failed: {e}")
